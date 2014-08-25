""" Application configuration """

MONGO_URI = 'mongodb://localhost:27017'

API_URL = 'http://api.worldoftanks.eu/wot'
API_TOKEN = ''
API_REQUEST_TIMEOUT = 10

CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'

try:
    from local_config import *
except ImportError:
    print("local config not found")
    pass