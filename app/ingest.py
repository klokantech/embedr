import os
import urllib
import math
import subprocess
import time
import random
import re

import simplejson as json
import redis
import boto
from filechunkio import FileChunkIO
import requests

from app.task_queue import task_queue
from models import Item, Batch, SubBatch


identify_output_regular = re.compile(r'''
	^
	(?P<size_json>.+)
	\n$
	''', re.VERBOSE)


@task_queue.task
def ingestQueue(batch_id, sub_batch_id):
	try:
		batch = Batch(batch_id)
		sub_batch = SubBatch(sub_batch_id, batch_id)
	except NoItemInDb, ErrorItemImport:
		return -1
		
	os.environ['S3_USE_SIGV4'] = 'True'
	s3 = boto.connect_s3(is_secure=False,host='s3.eu-central-1.amazonaws.com')
	bucket = s3.get_bucket('storage.hawk.bucket')
	chunk_size = 52428800
		
	try:
		urllib.urlretrieve (sub_batch.url, '/tmp/%s_%s.jpg' % (sub_batch.item_id, sub_batch.order))
		subprocess.call(['convert', '-compress', 'none', '/tmp/%s_%s.jpg' % (sub_batch.item_id, sub_batch.order), '/tmp/%s_%s.tif' % (sub_batch.item_id, sub_batch.order)])
		subprocess.call(['kdu_compress', '-i', '/tmp/%s_%s.tif' % (sub_batch.item_id, sub_batch.order), '-o', '/tmp/%s_%s.jp2' % (sub_batch.item_id, sub_batch.order), '-rate', '-,0.5', 'Clayers=2', 'Creversible=yes', 'Clevels=8', 'Cprecincts={256,256},{256,256},{128,128}', 'Corder=RPCL', 'ORGgen_plt=yes', 'ORGtparts=R', 'Cblk={64,64}'])

		source_path = '/tmp/%s_%s.jp2' % (sub_batch.item_id, sub_batch.order)
		source_size = os.stat(source_path).st_size
		chunk_count = int(math.ceil(source_size / float(chunk_size)))
		mp = bucket.initiate_multipart_upload('jp2_bl/' + os.path.basename(source_path))
				
		for i in range(chunk_count):
			offset = chunk_size * i
			bytes = min(chunk_size, source_size - offset)
					
			with FileChunkIO(source_path, 'r', offset=offset, bytes=bytes) as fp:
				mp.upload_part_from_file(fp, part_num=i + 1)
				
		mp.complete_upload()
		
		test = identify_output_regular.search(subprocess.check_output(['identify', '-format', '{"width": %w, "height": %h}', '/tmp/%s_%s.jpg' % (sub_batch.item_id, sub_batch.order)]))
		
		if test:
			sub_batch.image_meta = json.loads(test.group('size_json'))
		else:
			raise Exception
		
		os.remove('/tmp/%s_%s.jpg' % (sub_batch.item_id, sub_batch.order))
		os.remove('/tmp/%s_%s.jp2' % (sub_batch.item_id, sub_batch.order))
		os.remove('/tmp/%s_%s.tif' % (sub_batch.item_id, sub_batch.order))

		sub_batch.status = 'ok'
		sub_batch.save()

	except:
		sub_batch.attempts += 1
		
		if sub_batch.attempts < 5:
			sub_batch.save()
			rand = (sub_batch.attempts * 60) + random.randint(sub_batch.attempts * 60, sub_batch.attempts * 60 * 2)

			return ingestQueue.apply_async(args=[batch.id, sub_batch.id], countdown=rand)
		else:
			sub_batch.status = 'error'
			sub_batch.save()

	if batch.increment_finished_images() >= batch.sub_batches_count:
		finalizeIngest(batch)
		
	return


def finalizeIngest(batch):
	item_ids = {}
	
	for sub_batch_id in batch.sub_batches_ids:
		sub_batch = SubBatch(sub_batch_id, batch.id)
				
		if item_ids.has_key(sub_batch.item_id):
			item_ids[sub_batch.item_id].append((sub_batch.url, sub_batch.image_meta, sub_batch.status))
		else:
			item_ids[sub_batch.item_id] = [(sub_batch.url, sub_batch.image_meta, sub_batch.status)]
	
	order = 0
	
	for item_id in item_ids.keys():
		item = Item(item_id)
		item_status = 'ok'
		
		for data in item_ids[item_id]:
			url = data[0]
			image_meta = data[1]
			status = data[2]
			item.image_meta[url] = image_meta
			
			if status != 'ok':
				item_status = status
		
		batch.items[order]['status'] = item_status
		
		item.save()
		order += 1
			
	batch.save()

	return
