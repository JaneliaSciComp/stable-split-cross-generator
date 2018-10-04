#!/bin/bash
source 'env/bin/activate'
sudo rabbitmqctl start
python run.py
python run_celery.py
