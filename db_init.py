#!venv/bin/python

"""Script for import initial data to database"""

from app import db, models

image = models.Image(id='000-test2', title='Image title', rights='for free', provider='Klokantech', provider_link='http://www.klokantech.com')
db.session.add(image)

db.session.commit()
