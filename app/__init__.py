"""Module which initialize flask aplication on start time"""

from flask import Flask
from app import views
from flask.ext.redis import Redis


def app_factory(config):
	app = Flask(__name__)
	app.config.from_pyfile(config)
	redis = Redis()
	redis.init_app(app)

	app.route('/oembed/<unique_id>')(views.oEmbed)
	app.route('/<unique_id>')(views.iFrame)
	app.route('/iiif/<unique_id>/manifest.json')(views.iiifMeta)

	app.before_request(views.before_request)

	return app
