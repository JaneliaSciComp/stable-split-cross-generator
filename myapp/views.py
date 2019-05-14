import ipdb, sys, os, subprocess, logging,  glob, time, datetime, shutil
from flask import render_template, redirect, url_for, request, abort, send_from_directory, jsonify, send_from_directory
from datetime import datetime
from celery import Celery
from celery.schedules import crontab
from pprint import pprint
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

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Test clean up job, run every 30 seconds
    # sender.add_periodic_task(30.0, cleanup_folders.s('cleanup'), name='cleanup folders')

    # Executes every Monday morning at 6:00 a.m.
    sender.add_periodic_task(
        crontab(hour=6, minute=00, day_of_week='mon-fri'),
        cleanup_folders.s('cleanup'),
    )

@celery.task
def cleanup_folders(arg):
    path = glob.glob(Settings.outputDir + '/*')
    now = time.time()

    # Delete all folders whichs are older than 10 days
    taskClient = MongoClient(mongosettings)
    db = taskClient.stablesplit
    for f in path:
        folder = os.path.basename(os.path.normpath(f))
        msgs = db.messages.find( { 'task_id': { '$eq': folder } } )
        if msgs.count() > 0 and os.stat(f).st_mtime < now - (3 * 86400):
            shutil.rmtree(f)

@celery.task
def compute_splits_task(linenames, aline, task_name, show_all, username):
    gen1_split_generator = os.path.join(Settings.imagingEcoDir, 'gen1_split_generator.py')
    cmd = None

    if aline:
        print('2 -- linenames and aline')
        cmd = "{bin} --aline {aline} --debug --name {username} --task {task}{show-all}".format(**{
            'bin': gen1_split_generator,
            'aline': aline,
            'username': username,
            'task': task_name,
            'show-all': ' --all' if show_all else ''
        })
    else:
        print('3 -- linenames but no aline')
        cmd = "{bin} --debug --name {username} --task {task}{show-all}".format(**{
            'bin': gen1_split_generator,
            'username': username,
            'task': task_name,
            'show-all': ' --all' if show_all else ''
        })

    task_id = compute_splits_task.request.id

    output_dir = os.path.join(Settings.outputDir, task_id)
    logger.info('output dir: ' + output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pipe = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf8', cwd=output_dir)
    stdout, stderr = pipe.communicate(input=linenames)

    client_fork = MongoClient(mongosettings)
    sscg_fork = client_fork.stablesplit

    if pipe.returncode != 0: # TODO check exit code, only raise exception when not 0
        print('An exception ocurred')
        sscg_fork.messages.insert_one({
            'task_id': compute_splits_task.request.id,
            'task_name': task_name,
            'date': datetime.now(),
            'message': stdout,
            'status': 'ERROR',
            'output': stderr
            })
        raise Exception(stderr)
    else:
        print('Success')
        sscg_fork.messages.insert_one({
            'task_id': compute_splits_task.request.id,
            'task_name': task_name,
            'date': datetime.now(),
            'message': 'success',
            'status': 'SUCCESS',
            'output': stdout
            })


@myapp.route('/', methods=['GET','POST'])
@myapp.route('/uname/<username>')
@myapp.route('/uname/<username>/lnames/<linenames>')
@myapp.route('/uname/<username>/lnames/<linenames>/aline/<aline>', methods=['GET','POST'])
def home(username = None, linenames = None, aline = None):
    return render_template('index.html',
            username=username,
            linenames=linenames,
            aline=aline
        )

# this function is called within the POST success as a change of window.locate => no POST request
@myapp.route('/result/output/<task_id>/', methods=['GET'])
@myapp.route('/result', methods=['GET','POST'])
def result(task_id=None):

    # list all tasks
    folders = os.listdir(os.path.join(Settings.outputDir))
    directories = []
    for folder in folders:
        entry = {}
        entry['folder'] = folder
        entry['date'] = datetime.fromtimestamp(os.path.getmtime(os.path.join(Settings.outputDir, folder))).strftime('%m-%d-%Y %H:%M:%S')
        directories.append(entry)
    directories.sort(key=lambda x: x['date'], reverse=True)
    output = None

    if task_id != None:
        try:
            msgs = sscg.messages.find({'task_id': {'$eq': task_id}})
            if msgs.count() == 0:
                return render_template('processing.html')
            else:
                for result_object in msgs[0:1]:
                    pprint(result_object)
                    if 'output' in result_object:
                        output = result_object["output"]

        except Exception as e:
            print(e)
            return render_template('message.html', message="Could not connect to database.")

    return render_template(
        'list_directories.html',
        directories=directories,
        task_id=task_id,
        output=output
    )

@myapp.route('/detail/<task_id>/' , methods=['GET'])
def detail(task_id=None):
    try:
        msgs = sscg.messages.find({'task_id': {'$eq': task_id}})
        if msgs.count() == 0:
            return render_template('processing.html')
        else:
            for result_object in msgs[0:1]:
                if result_object["status"] == "SUCCESS":
                    files = os.listdir(os.path.join(Settings.outputDir, task_id))

                    if len(files) > 0:
                        content = []
                        for file in files:
                            print(file)
                            entry = {}
                            entry['file'] = file
                            data = None
                            if file.endswith('.txt'):
                                with open(os.path.join(Settings.outputDir, task_id, file), "r") as myfile:
                                    data = myfile.readlines()
                            entry['content'] = data
                            content.append(entry)
                        return render_template('result.html', content=content, task_id=task_id)
                    else:
                        return render_template('message.html', message="There are no results available for this task,")
                else:
                    return render_template(
                        'message.html',
                        message="There was an error in the application. No files have been generated."
                    )
    except:
        return render_template('message.html', message="Could not connect to database.")

@myapp.route("/download/<task_id>/<file>")
def download(task_id, file=None):
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
    user = User(request.form['username'], request.form['password'], request.form['email'])
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
            data['show-all'],
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
    try:
        messages = sscg.messages.find({'task_id': {"$eq": task_id}})
        if messages.count() == 1: # task ran successfully
            message = messages.next()
            return jsonify(message['status'])
        else:
            return jsonify('pending')
    except:
        return render_template('message.html', message='Could not connect to database.')

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))