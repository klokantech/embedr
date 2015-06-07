"""Module which provides flask aplication factory"""

from flask import Flask

from app import views
from models import db


def app_factory(config):
	app = Flask(__name__)
	app.config.from_pyfile(config)
	db.init_app(app)

	app.route('/')(views.index)
	app.route('/<unique_id>')(views.iFrame)
	app.route('/<unique_id>/manifest.json')(views.iiifMeta)
	app.route('/oembed', methods=['GET'])(views.oEmbed)
	app.route('/ingest', methods=['GET', 'POST'])(views.ingest)

	app.before_request(views.before_request)

	return app
