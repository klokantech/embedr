import math

from flask import current_app as app


def prepareTileSources(item, url):
	test=item.image_meta[url]['filename']
	item.image_meta[url]['@context'] = 'http://iiif.io/api/image/2/context.json'
	item.image_meta[url]['@id'] = '%s/%s' % (app.config['IIIF_SERVER'], trimFileExtension(item.image_meta[url]['filename']))
	item.image_meta[url]['protocol'] = 'http://iiif.io/api/image'
	item.image_meta[url]['profile'] = ['http://iiif.io/api/image/2/level1.json', {'formats': ['jpg'], 'qualities': ['native', 'color', 'gray'], 'supports': ['regionByPct', 'sizeByForcedWh', 'sizeByWh', 'sizeAboveFull', 'rotationBy90s', 'mirroring', 'gray']}]
		
	num_resolutions = math.log(max(item.image_meta[url]['width'], item.image_meta[url]['height']) / 256.0, 2)
		
	num_resolutions = int(math.ceil(num_resolutions))
		
	scaleFactors = [1]
		
	for i in range(1, num_resolutions + 1):
		scaleFactors.append(int(math.pow(2.0, i)))
		
	item.image_meta[url]['tiles'] = [{'width' : 256, 'height' : 256, 'scaleFactors': scaleFactors}]
	
	return item.image_meta[url]
	

def trimFileExtension(filename):
	"""Trims '.jp2' from filename"""
	return filename[:-4]
