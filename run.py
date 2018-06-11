from myapp import myapp
from myapp.settings import Settings

from celery import current_app    
from celery.bin import worker

application = current_app._get_current_object()
worker = worker.worker(app=application)

options = {
    'broker': myapp.config['CELERY_BROKER_URL'],
    'loglevel': 'INFO',
    'traceback': True,
}

worker.run(**options)
myapp.run(debug=True, host=Settings.serverInfo["IP"], port=Settings.serverInfo["port"])