from flask import render_template, Flask, Response, redirect, url_for, request, session, abort
from app import app
from app.settings import Settings
from app.forms import LoginForm, RegisterForm
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route('/', methods=['GET','POST'])
def home():
    # if not session.get('logged_in'):
    #     form = LoginForm()
    #     return render_template('login.html', form=form)
    return render_template('index.html')

@app.route('/result', methods=['GET','POST'])
def result():
    return render_template('result.html')

@app.route('/login', methods=['POST'])
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

@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        form = RegisterForm()
        return render_template('register.html', form=form)
    user = User(request.form['username'] , request.form['password'],request.form['email'])
    db.session.add(user)
    db.session.commit()
    flash('User successfully registered')
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))