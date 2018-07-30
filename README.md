# stable-split-cross-generator

Make sure, your python is version 3.5 or higher and your pip is using this correct python:

```bash
$ python --version
$ pip --version
$ which python
$ which pip
```
Create a virtualenv environment, here the environment is called 'env':

```bash
$ virtualenv env --no-site-packages
```
or better

```bash
$ virtualenv --no-site-packages -p [path to your python] env
```
Activate the environment:

```bash
$ source env/bin/activate
```

Install the requirements:

```bash
$ pip install -r requirements.txt
```

With

```bash
$ python run.py
```
you should be able to run the Flask application.

If you're done with coding, you can deactivate the environment with

```bash
$ deactivate
```

## Setup

Install supervisord, in Ubuntu with

```bash
$ sudo apt-get install supervisor
```

Plus, install python dev libaries

```bash
$ apt-get install python3.6-dev pcre
```

Supervisor conf script is located in
```bash
/etc/supervisor/conf.d/stable-split.conf
```

After making changes, reread and reload the config file with
```bash
$ sudo supervisorctl reread; sudo supervisorctl update; sudo supervisorctl restart 'stable-split:'
```

## Database

```bash
$ mongo --host [your mongodb host]:[mongodb port]
> show dbs
> use stablesplit
> db.getCollectionNames()
> db.createCollection('messages')
```
