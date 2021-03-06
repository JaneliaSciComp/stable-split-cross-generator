# stable-split-cross-generator

The split generator is a website which runs an algorithm to create output files of available crosses of fly lines.

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

Within the folder myapp, there are two template settings files. Copy them to create the two files `sscg-config.cfg` and `settings.py` within the same folder.

With

```bash
$ python run.py
```
you should be able to run the Flask application.

If you're done with coding, you can deactivate the environment with

```bash
$ deactivate
```

## Development

Start rabbitmq server, in Ubuntu with:
```bash
sudo rabbitmqctl start
```

To start celery from the command line, run the following commands within the project folder:

```bash
$ celery -A myapp.views worker -l info
$ celery -A myapp.views beat -l info
```

The first celery command waits for line names to be processed, the second command periodically
checks whether folders within the output directory have to be deleted, because they are older than 3 days.

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
