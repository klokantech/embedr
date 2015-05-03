"""Module which defines data models"""

from app import db

class Image(db.Model):
	"""Class which defines user model"""
	id = db.Column(db.String(64), primary_key = True)
	title = db.Column(db.String(256))
	rights = db.Column(db.String(64))
	provider = db.Column(db.String(64))
	provider_link = db.Column(db.String(128))
	created = db.Column(db.DateTime)
	updated = db.Column(db.DateTime)
