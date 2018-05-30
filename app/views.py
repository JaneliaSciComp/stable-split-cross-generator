from flask import render_template, Flask, Response, redirect, url_for, request, session, abort
from app import app
from app.settings import Settings
from app.forms import LoginForm

@app.route('/', methods=['GET','POST'])
def index():
    return render_template('index.html')

@app.route('/result', methods=['GET','POST'])
def result():
    return render_template('result.html')

@app.route('/login', methods=['GET', 'POST'])
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