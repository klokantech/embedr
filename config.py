"""Module for main configuration"""

import os

# Set complete name with domain
SERVER_NAME = 'localhost:5000'

# IIIF server
IIIF_SERVER = 'http://iiifhawk.klokantech.com'

# Redis config
REDIS_HOST = 'redis'
REDIS_PORT = '6379'

# Database config - you don't need to change it
basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
