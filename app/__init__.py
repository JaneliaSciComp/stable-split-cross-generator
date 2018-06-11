import json
from flask import Flask
from flask_admin import Admin
from celery import Celery

app = Flask(__name__) #app variable, an object of class FLask
app.config.from_pyfile('sscg-config.cfg')
from app import views

@app.context_processor
def get_app_version():
  mpath = app.root_path.split('/')
  result = '/'.join(mpath[0:(len(mpath) - 1)]) + '/package.json'
  with open(result) as package_data:
    data = json.load(package_data)
    package_data.close()
    return dict(version=data['version'])