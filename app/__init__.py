"""Module which initialize flask aplication on start time"""

from flask import Flask
import redis

app = Flask(__name__)
app.config.from_object('config')

db = redis.StrictRedis(host=app.config['REDIS_HOST'],
          port=app.config['REDIS_PORT'],
          db=0)

from app import views
