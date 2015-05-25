"""Module which defines views - actions for url passed requests"""

import sys
import os

from flask import request, render_template, abort, url_for, g
import simplejson as json
from flask import current_app as app

from iiif_manifest_factory import ManifestFactory


#@app.before_request
def before_request():
	g.db = app.extensions['redis'].redis


#@app.route('/')
def index():
	return render_template('index.html')


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
	
	if item.has_key('image_meta') and item['image_meta'][0].has_key('height'):
		height = item['image_meta'][0]['height']
	else:
		height = 1

	if item.has_key('image_meta') and item['image_meta'][0].has_key('width'):
		width = item['image_meta'][0]['width']
	else:
		width = 1
	
	fac = ManifestFactory()
	fac.set_base_metadata_uri(app.config['SERVER_NAME'] + '/iiif')
	fac.set_base_metadata_dir(os.path.abspath(os.path.dirname(__file__)))
	fac.set_base_image_uri(app.config['IIIF_SERVER'])
	fac.set_iiif_image_info(2.0, 2)
	
	mf = fac.manifest(ident=url_for('iiifMeta', unique_id=unique_id, _external=True), label='Manifest of ' + unique_id)
	
	seq = mf.sequence(label='Item %s - sequence 1' % unique_id)

	cvs = seq.canvas(ident='http://' + app.config['SERVER_NAME'] + '/canvas/c1.json', label='Item %s - canvas 1' % unique_id)
	cvs.set_hw(height, width)
	
	anno = cvs.annotation()

	img = anno.image(ident='/' + unique_id + '/full/full/0/native.jpg')
	img.height = height
	img.width = width
	img.add_service(ident=app.config['IIIF_SERVER'] + '/' + unique_id, context='http://iiif.io/api/image/2/context.json')

	return json.JSONEncoder().encode(mf.toJSON(top=True)), 200, {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}


#@app.route('/ingest', methods=['POST'])
def ingest():
	return "", 200
