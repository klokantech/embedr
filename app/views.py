"""Module which defines views - actions for url passed requests"""

import sys

from flask import request, render_template, abort, url_for, g
import simplejson as json
from flask import current_app as app

from iiif_manifest_factory import ManifestFactory


#@app.before_request
def before_request():
	g.db = app.extensions['redis'].redis


#@app.route('/oembed/<unique_id>')
def oEmbed(unique_id):
	item = g.db.get(unique_id)

	if not item:
		abort(404)

	try:
		item = json.loads(item)
	except:
		abort(500)

	return render_template('oembed.html', data = item)


#@app.route('/<unique_id>')
def iFrame(unique_id):
	item = g.db.get(unique_id)
	
	if not item:
		abort(404)
	
	try:
		item = json.loads(item)
	except:
		abort(500)
	
	if type(item['image_meta']) == list:
		for i in item['image_meta']:
			item['image_meta'] = json.dumps(i)
			break
		
	return render_template('iframe_openseadragon_inline.html', data = item)


#@app.route('/iiif/<unique_id>/manifest.json')
def iiifMeta(unique_id):
	item = g.db.get(unique_id)
	
	if not item:
		abort(404)
	
	try:
		item = json.loads(item)
	except:
		abort(500)
	
	fac = ManifestFactory()
	fac.set_base_metadata_uri(app.config['SERVER_NAME'] + '/iiif')
	fac.set_base_image_uri(app.config['SERVER_NAME'] + '/oembed' + unique_id)
	fac.set_iiif_image_info(2.0, 2)
	
	mf = fac.manifest(ident=url_for('iiifMeta', unique_id=unique_id, _external=True), label=item['title'])
	mf.description = "This is a longer description of the manifest"
	
	seq = mf.sequence(ident='1', label='Sequence 1')

	cvs = seq.canvas(ident=url_for('iiifMeta', unique_id=unique_id, _external=True), label="Canvas 1")
	cvs.set_hw(item['image_meta'][0]['height'], item['image_meta'][0]['width'])
	
	anno = cvs.annotation(ident=url_for('iiifMeta', unique_id=unique_id, _external=True))
	img = anno.image(ident='1')
	img.height = cvs.height
	img.width = cvs.width
	
	return json.JSONEncoder().encode(mf.toJSON()), 200


#@app.route('/ingest', methods=['POST'])
def ingest():
	return "", 200
