import dateutil, json
import dateutil.parser
from flask import Flask
from flask_admin import Admin
from celery import Celery
from datetime import datetime
from myapp.settings import Settings

myapp = Flask(__name__, static_folder='static') #app variable, an object of class FLask
myapp.config.from_pyfile('sscg-config.cfg')

admin=Admin(myapp)

from myapp import views

@myapp.context_processor
def add_global_variables():
  return dict(date_now=datetime.now())

@myapp.context_processor
def get_app_version():
  mpath = myapp.root_path.split('/')
  result = '/'.join(mpath[0:(len(mpath) - 1)]) + '/package.json'
  with open(result) as package_data:
    data = json.load(package_data)
    package_data.close()
    return dict(version=data['version'])

@myapp.context_processor
def get_app_userUrl():
  return dict(userUrl=Settings.users)

@myapp.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    date = dateutil.parser.parse(date)
    native = date.replace(tzinfo=None)

    format= "%Y-%m-%d at %H:%M:%S"
    return native.strftime(format)

@myapp.template_filter('strftime_short')
def _jinja2_filter_datetime(date, fmt=None):
    date = dateutil.parser.parse(date)
    native = date.replace(tzinfo=None)

    format= "%Y-%m-%d_%H:%M:%S"
    return native.strftime(format)