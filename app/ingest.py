import os
import urllib
import math
import subprocess
import time

import simplejson as json
import redis
import boto
from filechunkio import FileChunkIO
import requests

from app.queue import queue_app


@queue_app.task
def ingestQueue(batch_id):
	db = redis.StrictRedis(host='redis', port=6379, db=0)
	batch = db.get(batch_id)
	
	if batch:
		try:
			batch = json.loads(batch)
		except:
			return
		
		os.environ['S3_USE_SIGV4'] = 'True'
		s3 = boto.connect_s3(is_secure=False,host='s3.eu-central-1.amazonaws.com')
		bucket = s3.get_bucket('storage.hawk.bucket')
		del os.environ['S3_USE_SIGV4']
		chunk_size = 52428800
		
		item_count = 0
		
		for item in batch:

			if len(item['images']) == 0:
				continue
			
			old_item = db.get(item['id'])
			
			try:
				old_item = json.loads(old_item)
			except:
				continue
				
			
			url_count = 0
			
			for url in item['images'].keys():
				try:
					urllib.urlretrieve (url, 'tmp/%s_%s.jpg' % (item['id'], url_count))
					subprocess.call(['convert', '-compress', 'none', 'tmp/%s_%s.jpg' % (item['id'], url_count), 'tmp/%s_%s.tif' % (item['id'], url_count)])
					subprocess.call(['kdu_compress', '-i', 'tmp/%s_%s.tif' % (item['id'], url_count), '-o', 'tmp/%s_%s.jp2' % (item['id'], url_count), '-rate', '-,0.5', 'Clayers=2', 'Creversible=yes', 'Clevels=8', 'Cprecincts={256,256},{256,256},{128,128}', 'Corder=RPCL', 'ORGgen_plt=yes', 'ORGtparts=R', 'Cblk={64,64}'])

					source_path = 'tmp/%s_%s.jp2' % (item['id'], url_count)
					source_size = os.stat(source_path).st_size
					chunk_count = int(math.ceil(source_size / float(chunk_size)))
					mp = bucket.initiate_multipart_upload('jp2_bl/' + os.path.basename(source_path))
				
					for i in range(chunk_count):
						offset = chunk_size * i
						bytes = min(chunk_size, source_size - offset)
					
						with FileChunkIO(source_path, 'r', offset=offset, bytes=bytes) as fp:
							mp.upload_part_from_file(fp, part_num=i + 1)
				
					mp.complete_upload()
					os.remove('tmp/%s_%s.jpg' % (item['id'], url_count))
					os.remove('tmp/%s_%s.jp2' % (item['id'], url_count))
					os.remove('tmp/%s_%s.tif' % (item['id'], url_count))
					batch[item_count]['images'][url] = 'ok'
					time.sleep(2)
					r = requests.get('http://iiifhawk.klokantech.com/%s_%s/info.json' % (item['id'], url_count))
					old_item['image_meta'][url] = json.dumps(r.json())
				
				except:
					batch[item_count]['images'][url] = 'error'
					continue
				
				url_count += 1
			
			db.set(item['id'], json.JSONEncoder().encode(old_item))
			
			new_status = 'ok'
			
			for status in item['images'].values():
				if status == 'error':
					new_status = 'error'
					break
				elif status == 'pending':
					new_status = 'pending'
					break
			
			batch[item_count]['status'] = new_status
			item_count += 1
		
		db.set(batch_id, json.JSONEncoder().encode(batch))
		
	return
