"""Module which provides flask aplication factory"""

import os

from flask import Flask

from app import views
from models import db


def app_factory():
	app = Flask(__name__)

	app.config.update(
		SERVER_NAME=os.getenv('SERVER_NAME', '127.0.0.1:5000'),
		IIIF_SERVER=os.getenv('IIIF_SERVER', None),
		REDIS_URL=os.getenv('REDIS_URL', 'redis://localhost'),
		DEBUG=os.getenv('DEBUG', False),
		HOST=os.getenv('HOST', '127.0.0.1'),
		PORT=int(os.getenv('PORT', 5000))
	)
	
	db.init_app(app)

	app.route('/')(views.index)
	app.route('/<unique_id>')(views.iFrame)
	app.route('/<unique_id>/<order>')(views.iFrame)
	app.route('/<unique_id>/manifest.json')(views.iiifMeta)
	app.route('/oembed', methods=['GET'])(views.oEmbed)
	app.route('/ingest', methods=['GET', 'POST'])(views.ingest)

	app.before_request(views.before_request)

	return app
