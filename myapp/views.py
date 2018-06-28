import ipdb, pika, sys, os, subprocess
from flask import render_template, Flask, Response, redirect, url_for, request, session, abort
from celery import Celery
from myapp import myapp
from myapp.settings import Settings
from myapp.forms import LoginForm, RegisterForm
from flask_login import LoginManager
from flask_pika import Pika as FPika

login_manager = LoginManager()
login_manager.init_app(myapp)
login_manager.login_view = "login"

myapp.config.from_pyfile('sscg-config.cfg')
celery = Celery('task', backend='amqp', broker='amqp://guest:guest@localhost:5672/')
# celery = Celery(app.name, broker=app.config)
# celery.conf.update(app.config)

@celery.task
def compute_splits_task(lines, a_line):
    ecosystem_path = myapp.config['IMAGING_ECOSYSTEM']
    if not ecosystem_path.startswith('/'): # relative
        ecosystem_path = os.path.join(myapp.root_path, ecosystem_path)

    gen1_split_generator = os.path.join(ecosystem_path, 'gen1_split_generator.py')
    # Call R, allow Rprofile.site file
    cmd = "python {bin}".format(**{
        'bin': gen1_split_generator
    })
    pipe = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, encoding='utf8')
    stdout, stderr = pipe.communicate()
    if stderr: # TODO check exit code, only raise exception when not 0
        raise Exception(stderr)

@celery.task
def test(val1, val2):
    print('here the celery task goes in')
    return 'another test'

@myapp.route('/', methods=['GET','POST'])
def home():
    # if not session.get('logged_in'):
    #     form = LoginForm()
    #     return render_template('login.html', form=form)
    return render_template('index.html')


@myapp.route('/result', methods=['GET','POST'])
def result():
    return render_template('result.html')

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

@myapp.route('/compute_splits' , methods=['GET','POST'])
def compute_splits():
    lines = "lines"
    a_line  = 'a_line'
    task = compute_splits_task.delay(lines, a_line)
    print(dir(task))
    return 'task queued'

@myapp.route('/pika' , methods=['GET','POST'])
def pika():
    print('task is set')
    return 'pika task'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))