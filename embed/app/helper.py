"""Module which defines some useful helper functions"""

import os
import math

import boto
from flask import current_app as app

from exceptions import WrongCloudSearchService

S3_HOST = os.getenv('S3_HOST', '')
S3_DEFAULT_BUCKET = os.getenv('S3_DEFAULT_BUCKET', '')
CLOUDSEARCH_REGION = os.getenv('CLOUDSEARCH_REGION', '')


def prepareTileSources(item, url, order):
	"""Function which returns item with properly formated data for IIIF zooming.
	   'item' - item whose data have to be formated
	   'url' - base url of processed image
	   'order' - order number of specified image
	"""
	
	if order == 0:
		filename = item.id
	else:
		filename = '%s/%s' % (item.id, order)
		
	item.image_meta[url]['@context'] = 'http://iiif.io/api/image/2/context.json'
	item.image_meta[url]['@id'] = 'http://%s/%s' % (app.config['IIIF_SERVER'], filename)
	item.image_meta[url]['protocol'] = 'http://iiif.io/api/image'
	item.image_meta[url]['profile'] = ['http://iiif.io/api/image/2/level1.json', {'formats': ['jpg'], 'qualities': ['native', 'color', 'gray'], 'supports': ['regionByPct', 'sizeByForcedWh', 'sizeByWh', 'sizeAboveFull', 'rotationBy90s', 'mirroring', 'gray']}]
		
	num_resolutions = math.log(max(item.image_meta[url]['width'], item.image_meta[url]['height']) / 256.0, 2)
		
	num_resolutions = int(math.ceil(num_resolutions))
		
	scaleFactors = [1]
		
	for i in range(1, num_resolutions + 1):
		scaleFactors.append(int(math.pow(2.0, i)))
		
	item.image_meta[url]['tiles'] = [{'width' : 256, 'height' : 256, 'scaleFactors': scaleFactors}]
	
	return item.image_meta[url]


def getBucket():
	"""Function which returns S3 bucket defined by environment variable"""
	
	os.environ['S3_USE_SIGV4'] = 'True'
	s3 = boto.connect_s3(host=S3_HOST)
	return s3.get_bucket(S3_DEFAULT_BUCKET)


def getCloudSearch(domain, service):
	"""Function which returns Cloud Search service (document or search)
	   'domain' - Cloud Search domain to return service for
	   'service' - type of service, can be document or search
	"""
	
	if service == 'document':
		return boto.connect_cloudsearch2(region=CLOUDSEARCH_REGION, sign_request=True).lookup(domain).get_document_service()
	elif service == 'search':
		return boto.connect_cloudsearch2(region=CLOUDSEARCH_REGION, sign_request=True).lookup(domain).get_search_service()
	else:
		raise WrongCloudSearchService('Wrong type of Cloud Search service "%s"' % service)	
