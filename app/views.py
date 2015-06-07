"""Module which defines views - actions for url passed requests"""

import sys
import os
import re
from urlparse import urlparse

from flask import request, render_template, abort, url_for, g
import simplejson as json
from flask import current_app as app

from iiif_manifest_factory import ManifestFactory
from ingest import ingestQueue
from models import Item, Batch
from exceptions import NoItemInDb, ErrorItemImport


item_url_regular = re.compile(r"""
	^/
	(?P<unique_id>.+)
	""", re.VERBOSE)

id_regular = re.compile(r"""
	^([-_.:~a-zA-Z0-9]){1,32}$
	""", re.VERBOSE)

url_regular = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')

#@app.before_request
def before_request():
	g.db = app.extensions['redis'].redis


#@app.route('/')
def index():
	return render_template('index.html')


#@app.route('/<unique_id>')
def iFrame(unique_id):
	try:
		item = Item(unique_id)
	except NoItemInDb as err:
		return err.message, 404
	except ErrorItemImport as err:
		return err.message, 500

	return render_template('iframe_openseadragon_inline.html', item = item)


#@app.route('/<unique_id>/manifest.json')
def iiifMeta(unique_id):
	try:
		item = Item(unique_id)
	except NoItemInDb as err:
		return err.message, 404
	except ErrorItemImport as err:
		return err.message, 500

	if item.image_meta[item.url[0]].has_key('width'):
		width = item.image_meta[item.url[0]]['width']
	else:
		width = 1

	if item.image_meta[item.url[0]].has_key('height'):
		height = item.image_meta[item.url[0]]['height']
	else:
		height = 1
	
	fac = ManifestFactory()
	fac.set_base_metadata_uri(app.config['SERVER_NAME'])
	fac.set_base_metadata_dir(os.path.abspath(os.path.dirname(__file__)))
	fac.set_base_image_uri(app.config['IIIF_SERVER'])
	fac.set_iiif_image_info(2.0, 2)
	
	mf = fac.manifest(ident=url_for('iiifMeta', unique_id=unique_id, _external=True), label=item.title)
	
	seq = mf.sequence(label='Item %s - sequence 1' % unique_id)

	cvs = seq.canvas(ident='http://' + app.config['SERVER_NAME'] + '/canvas/c1.json', label='Item %s - canvas 1' % unique_id)
	cvs.set_hw(height, width)
	
	anno = cvs.annotation()

	img = anno.image(ident='/' + unique_id + '_0/full/full/0/native.jpg')
	img.height = height
	img.width = width
	img.add_service(ident=app.config['IIIF_SERVER'] + '/' + unique_id + '_0', context='http://iiif.io/api/image/2/context.json')

	return json.JSONEncoder().encode(mf.toJSON(top=True)), 200, {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}


#@app.route('/oembed', methods=['GET'])
def oEmbed():
	url = request.args.get('url', None)
	
	if url is None:
		return 'No url parameter provided', 404
	
	format = request.args.get('format', None)
	
	if format is None:
		format = 'json'
	
	if format not in ('json', 'xml'):
		return 'The format parameter must be "json" or "xml" (or blank)', 501
	
	p_url = urlparse(url)
	
	if p_url.scheme != 'http':
		return 'the http scheme must be used', 404
	
	if p_url.netloc != app.config['SERVER_NAME']:
		return 'Only urls on the same server are allowed', 404
	
	test = item_url_regular.search(p_url.path)
		
	if test:
		unique_id = test.group('unique_id')
	else:
		return 'Unsupported format of ID', 404
	
	try:
		item = Item(unique_id)
	except NoItemInDb as err:
		return err.message, 404
	except ErrorItemImport as err:
		return err.message, 500

	maxwidth = request.args.get('maxwidth', None)
	maxheight = request.args.get('maxheight', None)

	if maxwidth is not None:
		maxwidth = int(maxwidth)
	
	if maxheight is not None:
		maxheight = int(maxheight)

	if item.image_meta[item.url[0]].has_key('width'):
		width = int(item.image_meta[item.url[0]]['width'])
	else:
		width = -1

	if item.image_meta[item.url[0]].has_key('height'):
		height = int(item.image_meta[item.url[0]]['height'])
	else:
		height = -1
	
	if width != -1 and height != -1:
		ratio = float(width) / float(height)
	else:
		ratio = 1

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
	data[u'title'] = item.title
	data[u'url'] = app.config['IIIF_SERVER'] + '/' + unique_id + '_0/full/%s/0/native.jpg' % size
	data[u'width'] = '%.0f' % width
	data[u'height'] = '%.0f' % height

	if format == 'xml':
		return render_template('oembed_xml.html', data = data), 200, {'Content-Type': 'text/xml'}
	else:
		return json.dumps(data), 200, {'Content-Type': 'application/json'}


#@app.route('/ingest', methods=['GET', 'POST'])
def ingest():
	if request.method == 'GET':
		batch_id = request.args.get('batch_id', None)

		if batch_id is not None:
			try:
				batch = Batch(batch_id)
			except:
				batch = None
	
			if batch:
				return json.JSONEncoder().encode(batch.items), 200, {'Content-Type': 'application/json'}
		
		abort(404)
	else:
		if request.headers.get('Content-Type') != 'application/json':
			abort(404)
		
		try:
			data = json.loads(request.data)
		except:
			abort(404)

		if type(data) is not list:
			abort(404)
		
		# validation
		for item in data:
			if type(item) is not dict:
				abort(404)

			if not item.has_key('id'):
				abort(404)
					
			if not id_regular.match(item['id']):
				abort(404)
			
			if item.has_key('status') and (len(item) != 2 or item['status'] != 'deleted'):
				abort(404)
			
			if item.has_key('status'):
				continue
			
			if not item.has_key('url') or type(item['url']) != list or len(item['url']) == 0:
				abort(404)
			
			for url in item['url']:
				if not url_regular.match(url):
					abort(404)
		
		batch = Batch()
		
		# processing
		for item_data in data:
			unique_id = item_data['id']
			b = {'id': unique_id, 'images': {}}
			
			if item_data.has_key('status') and item_data['status'] == 'deleted':
				g.db.delete(unique_id)
				b['status'] = 'deleted'
				batch.items.append(b)
				continue
			
			try:
				item = Item(unique_id, item_data)
			except NoItemInDb, ErrorItemImport:
				abort(500)
						
			try:
				old_item = Item(unique_id)
			except NoItemInDb, ErrorItemImport:
				old_item = None
			
#			old_item = None #--------------------------
			
			# already stored item
			if old_item:
				item.image_meta = old_item.image_meta

				for url in item.url:
					# any change in url
					if url not in old_item.url:
						item.image_meta[url] = {}
						b['images'][url] = 'pending'

			# new item
			else:
				item.image_meta = {}
				
				for url in item.url:
					b['images'][url] = 'pending'
			
			item.save()
			
			if b['images']:
				b['status'] = 'pending'
			else:
				b['status'] = 'ok'
			
			batch.items.append(b)
			
		batch.save()
		
		for b_item in batch.items:
			order = 0
			
			for url in b_item['images']:
				ingestQueue.delay(batch.id, b_item['id'], url, order)
				order += 1
		
	return json.JSONEncoder().encode({'batch_id': batch.id}), 200, {'Content-Type': 'application/json'}
