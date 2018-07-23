import ipdb, sys, os, subprocess, json, logging
from flask import render_template, Flask, Response, redirect, url_for, request, session, abort, send_from_directory, jsonify
from datetime import datetime
from celery import Celery
from myapp import myapp
from myapp.settings import Settings
from myapp.forms import LoginForm, RegisterForm
from flask_login import LoginManager
from pymongo import MongoClient

logger = logging.getLogger(__file__)

login_manager = LoginManager()
login_manager.init_app(myapp)
login_manager.login_view = "login"

myapp.config.from_pyfile('sscg-config.cfg')
myapp.url_map.strict_slashes = False
celery = Celery('task', backend='amqp', broker='amqp://guest:guest@localhost:5672/')

# Mongo client
mongosettings = 'mongodb://' + myapp.config['MONGODB_SETTINGS']['host'] + ':' + str(myapp.config['MONGODB_SETTINGS']['port']) + '/'
client = MongoClient(mongosettings)

sscg = client.stablesplit

@celery.task
def compute_splits_task(linenames, aline, task_name):
    ecosystem_path = myapp.config['IMAGING_ECOSYSTEM']
    if not ecosystem_path.startswith('/'): # relative
        ecosystem_path = os.path.join(myapp.root_path, ecosystem_path)

    gen1_split_generator = os.path.join(ecosystem_path, 'gen1_split_generator.py')
    # Call R, allow Rprofile.site file
    # printf "55D12\n60b11\n40c01" | ./gen1_split_generator.py --deb
    # linenames = None
    cmd = None
    if not linenames:
        print('1 -- no linenames')
        cmd = "python {bin} --file ../line-names.txt --debug".format(**{
            'bin': gen1_split_generator
        })
    else:
        if aline:
            print('2 -- linenames and aline')
            cmd = "{bin} --aline {aline} --debug".format(**{
                'bin': gen1_split_generator,
                'aline': aline
            })
        else:
            print('3 -- linenames but no aline')
            cmd = "{bin} --debug".format(**{
                'bin': gen1_split_generator
            })

    task_id = compute_splits_task.request.id

    output_dir = os.path.join(myapp.root_path, 'static/output', task_id)
    logger.info('output dir: ' + output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pipe = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, encoding='utf8', cwd=output_dir)
    stdout, stderr = pipe.communicate(input=linenames)

    #subprocess.call([cmd_dir])
    client_fork = MongoClient(mongosettings)
    sscg_fork = client_fork.stablesplit

    if pipe.returncode != 0: # TODO check exit code, only raise exception when not 0
        print('An exception ocurred')
        sscg_fork.messages.insert_one({
            'task_id': compute_splits_task.request.id,
            'task_name': task_name,
            'date': datetime.now(),
            'message': stderr,
            'status': 'ERROR'
            })
        raise Exception(stderr)
    else:
        print('Success')
        sscg_fork.messages.insert_one({
            'task_id': compute_splits_task.request.id,
            'task_name': task_name,
            'date': datetime.now(),
            'message': 'success',
            'status': 'SUCCESS'
            })

    os.killpg(os.getpgid(pipe.pid), signal.SIGTERM)


@myapp.route('/', methods=['GET','POST'])
def home():
    # if not session.get('logged_in'):
    #     form = LoginForm()
    #     return render_template('login.html', form=form)
    return render_template('index.html')


# this function is called within the POST success as a change of window.locate => no POST request
@myapp.route('/result/<task_id>/' , methods=['GET'])
@myapp.route('/result', methods=['GET','POST'])
def result(task_id = None):
    files = os.listdir(os.path.join(myapp.root_path, 'static/output' , task_id))
    if len(files) > 0:
        message = sscg.message
        m = message.find_one()
        file1 = files[0]
        file2 = files[1]
        file3 = files[2]
        return render_template('result.html', file1=file1, file2=file2, file3=file3, task_id=task_id)
    else:
        return 'no result yet'

@myapp.route("/download/<task_id>/<file>")
def download(task_id, file):
    path = os.path.join(myapp.static_folder, 'output', task_id)
    return send_from_directory(
            path,
            file,
            as_attachment=True
        )

@myapp.route('/login', methods=['POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate():
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # is_safe_url should check if the url is safe for redirects.
        # See http://flask.pocoo.org/snippets/62/ for an example.
        if not is_safe_url(next):
            return abort(400)

        return redirect(next or flask.url_for('index'))
    return render_template('login.html', form=form)

@myapp.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        form = RegisterForm()
        return render_template('register.html', form=form)
    user = User(request.form['username'] , request.form['password'],request.form['email'])
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered')
    return redirect(url_for('login'))

# Route to call the task to compute stable splits
@myapp.route('/compute_splits' , methods=['GET','POST'])
@myapp.route('/compute_splits/<linenames>/<aline>/' , methods=['GET','POST'])
def compute_splits(linenames=None, aline=None, task_name=None):
    if not linenames and not aline:
        data = request.json
        task = compute_splits_task.delay(
                data['lnames'],
                data['aline'],
                data['task_name']
            )
    if linenames:
        compute_splits_task.delay(linenames, aline, task_name)

    result = {
        'status': 'QUEUED',
        'task_id': task.task_id
    }
    return jsonify(result)

# Route to query the database, if the task ran successfully already
@myapp.route('/polling/<task_id>' , methods=['GET'])
def polling(task_id):
    count = sscg.messages.find({ "$and": [ { 'task_id': { "$eq": task_id } }, { 'status': { "$eq": 'SUCCESS' } } ] }).count()
    if count == 1: # task ran successfully
        return jsonify('success')
    else:
        return jsonify('failure')

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))