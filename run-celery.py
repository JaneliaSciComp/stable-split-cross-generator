# import sys, os

# #add ImagingEcoSystem to the python path
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# imagingeco_path = os.path.join(BASE_DIR, 'myapp/libs/ImagingEcosystem/bin')
# sys.path.insert(0, imagingeco_path)

from myapp import myapp
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
#myapp.run(debug=True, host=Settings.serverInfo["IP"], port=Settings.serverInfo["port"])
