import json
from flask import Flask
from flask_admin import Admin
from celery import Celery

myapp = Flask(__name__) #app variable, an object of class FLask
myapp.config.from_pyfile('sscg-config.cfg')
from myapp import views

@myapp.context_processor
def get_app_version():
  mpath = myapp.root_path.split('/')
  result = '/'.join(mpath[0:(len(mpath) - 1)]) + '/package.json'
  with open(result) as package_data:
    data = json.load(package_data)
    package_data.close()
    return dict(version=data['version'])