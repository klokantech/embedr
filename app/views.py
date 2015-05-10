"""Module which defines views - actions for url passed requests"""

import sys

from flask import request, render_template, flash, redirect, abort, url_for, json
import requests

from app import app
from models import Image


@app.route('/oembed/<unique_id>')
def oEmbed(unique_id):
	image = Image.query.get_or_404(unique_id)
	
	return render_template('oembed.html', data = image)


@app.route('/<unique_id>')
def iFrame(unique_id):
	print unique_id
	image = Image.query.get_or_404(unique_id)
	r = requests.get(app.config['IIIF_SERVER'] + '/' + unique_id + '/info.json')
	image.meta = json.dumps(r.json())
	
	return render_template('iframe_openseadragon_inline.html', data = image)


@app.route('/iiif/<unique_id>/manifest.json')
def iiifMeta(unique_id):
	image = Image.query.get_or_404(unique_id)
	r = requests.get(app.config['IIIF_SERVER'] + '/' + unique_id + '/info.json')
	image.meta = r.text
	
	return render_template('iiifmeta.html', data = image)


@app.route('/ingest', methods=['POST'])
def ingest():
	ingestion_task()
	return "", 200
