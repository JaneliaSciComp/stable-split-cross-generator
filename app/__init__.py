import json
from flask import Flask
from flask_admin import Admin
from flask_login import LoginManager

app = Flask(__name__) #app variable, an object of class FLask
from app import views

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.context_processor
def get_app_version():
  mpath = app.root_path.split('/')
  result = '/'.join(mpath[0:(len(mpath) - 1)]) + '/package.json'
  with open(result) as package_data:
    data = json.load(package_data)
    package_data.close()
    return dict(version=data['version'])