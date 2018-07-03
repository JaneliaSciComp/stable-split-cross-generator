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

Start the celery script

```bash
$ python run-celery.py
```

## Database

```bash
mongo --host [your mongodb host]:[mongodb port]
show dbs
use stable-split
db.getCollectionNames()
db.createCollection('messages')
```