"""Module which defines views - actions for url passed requests"""

import sys
import os
import re
from urlparse import urlparse

from flask import request, render_template, abort, url_for, g
import simplejson as json
from flask import current_app as app

from iiif_manifest_factory import ManifestFactory


oembed_url_regular = re.compile(r"""
	^/oembed/
	(?P<unique_id>.+)
	""", re.VERBOSE)


#@app.before_request
def before_request():
	g.db = app.extensions['redis'].redis


#@app.route('/')
def index():
	return render_template('index.html')


#@app.route('/oembedprovider', methods=['GET'])
def oEmbed_API():
	url = request.args.get('url', None)
	
	if url is None:
		abort(404)
	
	format = request.args.get('format', None)
	
	if format is None:
		format = 'json'
	
	if format not in ('json', 'xml'):
		abort(501)
	
	p_url = urlparse(url)
	
	if p_url.scheme != 'http':
		abort(404)
	
	if p_url.netloc != app.config['SERVER_NAME']:
		abort(404)
	
	test = oembed_url_regular.search(p_url.path)
		
	if test:
		unique_id = test.group('unique_id')
	else:
		abort(404)
	
	item = g.db.get(unique_id)

	if not item:
		abort(404)

	try:
		item = json.loads(item)
	except:
		abort(500)

	maxwidth = request.args.get('maxwidth', None)
	maxheight = request.args.get('maxheight', None)

	if maxwidth is not None:
		maxwidth = int(maxwidth)
	
	if maxheight is not None:
		maxheight = int(maxheight)

	if item.has_key('image_meta') and item['image_meta'][0].has_key('width'):
		width = int(item['image_meta'][0]['width'])
	else:
		width = -1

	if item.has_key('image_meta') and item['image_meta'][0].has_key('height'):
		height = int(item['image_meta'][0]['height'])
	else:
		height = -1
	
	if width != -1 and height != -1:
		ratio = float(width) / float(height)
	else:
		ratio = 1
	
	if item.has_key('title'):
		title = item['title']
	else:
		title = ''

	if width != -1:
		if maxwidth is not None and maxwidth < width:
			outwidth = maxwidth
		else:
			outwidth = 'full'
	else:
		if maxwidth is not None:
			outwidth = maxwidth
		else:
			outwidth = 'full'
	
	if height != -1:
		if maxheight is not None and maxheight < height:
			outheight = maxheight
		else:
			outheight = 'full'
	else:
		if maxheight is not None:
			outheight = maxheight
		else:
			outheight = 'full'
	
	if outwidth == 'full' and outheight == 'full':
		size = 'full'
	elif outwidth == 'full':
		size = ',%s' % outheight
		width = float(outheight) * ratio
		height =  outheight
	elif outheight == 'full':
		size = '%s,' % outwidth
		width = outwidth
		height = float(outwidth) / ratio
	else:
		size = '!%s,%s' % (outwidth, outheight)

		if ratio > (float(outwidth) / float(outheight)):
			width = outwidth
			height = float(outwidth) / ratio
		else:
			width = float(outheight) * ratio
			height = outheight
	
	data = {}
	data[u'version'] = '1.0'
	data[u'type'] = 'photo'
	data[u'title'] = title
	data[u'url'] = app.config['IIIF_SERVER'] + '/' + unique_id + '/full/%s/0/native.jpg' % size
	data[u'width'] = '%.0f' % width
	data[u'height'] = '%.0f' % height

	if format == 'xml':
		return render_template('oembed_xml.html', data = data), 200, {'Content-Type': 'text/xml'}
	else:
		return json.dumps(data), 200, {'Content-Type': 'application/json'}

#@app.route('/oembed/<unique_id>')
def oEmbed(unique_id):
	item = g.db.get(unique_id)

	if not item:
		abort(404)

	try:
		item = json.loads(item)
	except:
		abort(500)
	
	if not item.has_key('title'):
		item['title'] = ''

	return render_template('img.html', data = item)


#@app.route('/<unique_id>')
def iFrame(unique_id):
	item = g.db.get(unique_id)
	
	if not item:
		abort(404)
	
	try:
		item = json.loads(item)
	except:
		abort(500)
	
	if not item.has_key('title'):
		item['title'] = ''
	
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
	
	if item.has_key('image_meta') and item['image_meta'][0].has_key('width'):
		width = item['image_meta'][0]['width']
	else:
		width = 1

	if item.has_key('image_meta') and item['image_meta'][0].has_key('height'):
		height = item['image_meta'][0]['height']
	else:
		height = 1
	
	if item.has_key('title'):
		title = item['title']
	else:
		title = ''
	
	fac = ManifestFactory()
	fac.set_base_metadata_uri(app.config['SERVER_NAME'] + '/iiif')
	fac.set_base_metadata_dir(os.path.abspath(os.path.dirname(__file__)))
	fac.set_base_image_uri(app.config['IIIF_SERVER'])
	fac.set_iiif_image_info(2.0, 2)
	
	mf = fac.manifest(ident=url_for('iiifMeta', unique_id=unique_id, _external=True), label=title)
	
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
