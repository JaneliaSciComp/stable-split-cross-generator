from flask import render_template
from app import app
from app.settings import Settings

@app.route('/', methods=['GET','POST'])
def index():
    return render_template('index.html')