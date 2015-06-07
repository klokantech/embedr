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

from app.task_queue import task_queue
from models import Item, Batch


@task_queue.task
def ingestQueue(batch_id, item_id, url, order):
	try:
		batch = Batch(batch_id)
		item = Item(item_id)
	except:
		return
		
	os.environ['S3_USE_SIGV4'] = 'True'
	s3 = boto.connect_s3(is_secure=False,host='s3.eu-central-1.amazonaws.com')
	bucket = s3.get_bucket('storage.hawk.bucket')
	chunk_size = 52428800
		
	try:
		urllib.urlretrieve (url, 'tmp/%s_%s.jpg' % (item_id, order))
		subprocess.call(['convert', '-compress', 'none', 'tmp/%s_%s.jpg' % (item_id, order), 'tmp/%s_%s.tif' % (item_id, order)])
		subprocess.call(['kdu_compress', '-i', 'tmp/%s_%s.tif' % (item_id, order), '-o', 'tmp/%s_%s.jp2' % (item_id, order), '-rate', '-,0.5', 'Clayers=2', 'Creversible=yes', 'Clevels=8', 'Cprecincts={256,256},{256,256},{128,128}', 'Corder=RPCL', 'ORGgen_plt=yes', 'ORGtparts=R', 'Cblk={64,64}'])

		source_path = 'tmp/%s_%s.jp2' % (item_id, order)
		source_size = os.stat(source_path).st_size
		chunk_count = int(math.ceil(source_size / float(chunk_size)))
		mp = bucket.initiate_multipart_upload('jp2_bl/' + os.path.basename(source_path))
				
		for i in range(chunk_count):
			offset = chunk_size * i
			bytes = min(chunk_size, source_size - offset)
					
			with FileChunkIO(source_path, 'r', offset=offset, bytes=bytes) as fp:
				mp.upload_part_from_file(fp, part_num=i + 1)
				
		mp.complete_upload()
		os.remove('tmp/%s_%s.jpg' % (item_id, order))
		os.remove('tmp/%s_%s.jp2' % (item_id, order))
		os.remove('tmp/%s_%s.tif' % (item_id, order))
		batch.items[order]['images'][url] = 'ok'
		time.sleep(2)
		r = requests.get('http://iiifhawk.klokantech.com/%s_%s/info.json' % (item_id, order))
		item.image_meta[url] = r.json()
		item.save()
		new_status = 'ok'
				
	except:
		new_status = 'error'

	batch.items[order]['images'][url] = new_status
			
	for status in batch.items[order]['images'].values():
		if status == 'error':
			new_status = 'error'
			break
		elif status == 'pending':
			new_status = 'pending'
			break
			
	batch.items[order]['status'] = new_status
	batch.save()
		
	return
