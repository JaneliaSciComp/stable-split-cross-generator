import ipdb, pika, sys, os, subprocess
from flask import render_template, Flask, Response, redirect, url_for, request, session, abort, send_from_directory
from celery import Celery
from myapp import myapp
from myapp.settings import Settings
from myapp.forms import LoginForm, RegisterForm
from flask_login import LoginManager
from flask_pika import Pika as FPika
from pymongo import MongoClient

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
def compute_splits_task(linenames, aline):
    print('in task');
    ecosystem_path = myapp.config['IMAGING_ECOSYSTEM']
    if not ecosystem_path.startswith('/'): # relative
        ecosystem_path = os.path.join(myapp.root_path, ecosystem_path)

    gen1_split_generator = os.path.join(ecosystem_path, 'gen1_split_generator.py')
    # Call R, allow Rprofile.site file
    # printf "55D12\n60b11\n40c01" | ./gen1_split_generator.py --deb
    cmd = None
    if not linenames:
        cmd = "python {bin} --file line-names.txt --debug".format(**{
            'bin': gen1_split_generator
        })
    else:
        if aline:
            cmd = "printf {linenames} | {bin} --aline {aline} --debug".format(**{
                'linenames': linenames,
                'bin': gen1_split_generator,
                'aline': aline
            })
        else:
            cmd = "printf {linenames} | {bin} --debug".format(**{
                'linenames': linenames,
                'bin': gen1_split_generator
            })
    print('command ' + cmd)
    pipe = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, encoding='utf8')
    stdout, stderr = pipe.communicate()
    print('stdout {0}'.format(stdout))
    print('stderr {0}'.format(stderr))
    if stderr: # TODO check exit code, only raise exception when not 0
        print('An exception ocurred')
        raise Exception(stderr)


@myapp.route('/', methods=['GET','POST'])
def home():
    # if not session.get('logged_in'):
    #     form = LoginForm()
    #     return render_template('login.html', form=form)
    return render_template('index.html')


# this function is called within the POST success as a change of window.locate => no POST request
@myapp.route('/result', methods=['GET','POST'])
def result():
    message = sscg.message
    m = message.find_one()
    ipdb.set_trace()

    file1 = '58443-customName.crosses.txt'
    file2 = '58443-customName.flycore.xls'
    file3 = '58443-customName.no_crosses.txt'

    return render_template('result.html', file1=file1, file2=file2, file3=file3)

@myapp.route("/download/<file>")
def download(file):
    myfile = os.path.join(os.path.dirname(myapp.root_path), file)
    print('myfile ' + myfile)
    return send_from_directory(
            os.path.dirname(myapp.root_path),
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

@myapp.route('/compute_splits/' , methods=['GET','POST'])
@myapp.route('/compute_splits/<linenames>/<aline>' , methods=['GET','POST'])
def compute_splits(linenames = None, aline = None):
    if not linenames and not aline:
        data = request.json
        task = compute_splits_task.delay(
                data['lnames'],
                data['aline'])
    if linenames:
        compute_splits_task.delay(linenames, aline)
    # print(dir(task))
    # return redirect(url_for('result'))
    return ''

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))