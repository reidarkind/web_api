"""
Set up of celery worker.
This file is used two places: in /api and in /celery
The file in /celery is created as a symbolic link (hard link) with (in Windows):
mklink /h worker.py ..\api\worker.py
When docker image (DockerfileCelery) is created, the symbolic link is deleted and the actual file is copied
into the image.
"""
import os

from celery import Celery
from dotenv import load_dotenv, find_dotenv

# load environment variables that are defined in a .env file
# in the same folder as this folder, or its parents
load_dotenv(find_dotenv())

# set up celery application, and add address to broker and server from environment variables
celery_app = Celery(__name__)
broker_url = os.environ.get("CELERY_BROKER_URL")
backend = os.environ.get("CELERY_RESULT_BACKEND")

celery_app.conf.broker_url = broker_url
celery_app.conf.result_backend = backend
