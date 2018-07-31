import ipdb, sys, os, subprocess, logging
from flask import render_template, redirect, url_for, request, abort, send_from_directory, jsonify, send_from_directory
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

@myapp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(myapp.root_path, 'static'),
                               'favicon.ico')

@celery.task
def compute_splits_task(linenames, aline, task_name, username):
    print(aline)

    gen1_split_generator = os.path.join(Settings.imagingEcoDir, 'gen1_split_generator.py')
    # Call R, allow Rprofile.site file
    # printf "55D12\n60b11\n40c01" | ./gen1_split_generator.py --deb
    # linenames = None
    cmd = None
    vtcache_path =  myapp.config['VTCACHE_PATH'] + username + '_vt.cache'

    if aline:
        print('2 -- linenames and aline')
        cmd = "{bin} --aline {aline} --debug --name {username} --vtcache {vtcache}".format(**{
            'bin': gen1_split_generator,
            'aline': aline,
            'username': username,
            'vtcache': vtcache_path
        })
    else:
        print('3 -- linenames but no aline')
        cmd = "{bin} --debug --name {username} --vtcache {vtcache}".format(**{
            'bin': gen1_split_generator,
            'username': username,
            'vtcache': vtcache_path
        })

    task_id = compute_splits_task.request.id

    output_dir = os.path.join(Settings.outputDir, task_id)
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
            'message': stdout,
            'status': 'ERROR'
            })
        raise Exception(stdout)
    else:
        print('Success')
        sscg_fork.messages.insert_one({
            'task_id': compute_splits_task.request.id,
            'task_name': task_name,
            'date': datetime.now(),
            'message': 'success',
            'status': 'SUCCESS'
            })


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
    msgs = sscg.messages.find( { 'task_id': { '$eq': task_id } } )
    if msgs.count() == 0:
        return render_template('processing.html')
    else:
        for result_object in msgs[0:1]:
            if result_object["status"] == "SUCCESS":
                file1 = None
                file2 = None
                file3 = None
                files = os.listdir(os.path.join(Settings.outputDir, task_id))
                if len(files) > 0:
                    file1 = files[0]
                    if len(files) > 1:
                        file2 = files[1]
                    if len(files) > 2:
                        file3 = files[2]
                    return render_template('result.html', file1=file1, file2=file2, file3=file3, task_id=task_id)
                else:
                    return 'There was an error with the application'
            else:
                return 'There was an error with the application'

@myapp.route("/download/<task_id>/<file>")
def download(task_id, file = None):
    path = os.path.join(Settings.outputDir, task_id)
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
@myapp.route('/compute_splits/<username>' , methods=['GET','POST'])
#@myapp.route('/compute_splits/<linenames>/<aline>/' , methods=['GET','POST'])
def compute_splits(username = None):
    data = request.json
    task = compute_splits_task.delay(
            data['lnames'],
            data['aline'],
            data['task_name'],
            username
        )

    result = {
        'status': 'QUEUED',
        'task_id': task.task_id
    }
    return jsonify(result)

# Route to query the database, if the task ran successfully already
@myapp.route('/polling/<task_id>' , methods=['GET'])
def polling(task_id):
    # count = sscg.messages.find({ "$and": [ { 'task_id': { "$eq": task_id } }, { 'status': { "$eq": 'SUCCESS' } } ] }).count()
    messages = sscg.messages.find({ 'task_id': { "$eq": task_id }})
    if messages.count() == 1: # task ran successfully
        message = messages.next()
        return jsonify(message['status'])
    else:
        return jsonify('pending')

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))