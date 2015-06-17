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
from exceptions import NoItemInDb, ErrorItemImport


identify_output_regular = re.compile(r'''
	^
	(?P<size_json>.+)
	\n$
	''', re.VERBOSE)

S3_HOST = os.getenv('S3_HOST', '')
S3_CHUNK_SIZE = int(os.getenv('S3_CHUNK_SIZE', 52428800))
S3_DEFAULT_FOLDER = os.getenv('S3_DEFAULT_FOLDER', '')
S3_DEFAULT_BUCKET = os.getenv('S3_DEFAULT_BUCKET', '')
MAX_SUB_BATCH_REPEAT = int(os.getenv('MAX_SUB_BATCH_REPEAT', 1))
CLOUDSEARCH_REGION = os.getenv('CLOUDSEARCH_REGION', '')
CLOUDSEARCH_DOMAIN = os.getenv('CLOUDSEARCH_DOMAIN', '')


@task_queue.task
def ingestQueue(batch_id, sub_batch_id):
	try:
		batch = Batch(batch_id)
		sub_batch = SubBatch(sub_batch_id, batch_id)
	except NoItemInDb, ErrorItemImport:
		return -1
	
	try:
		bucket = getBucket()
		
		if sub_batch.type == 'del':
			item = Item(sub_batch.item_id)
			filename = item.image_meta[sub_batch.url]['filename']
			
			if filename:
				bucket.delete_key(S3_DEFAULT_FOLDER + filename)
			
			sub_batch.status = 'deleted'
			sub_batch.save()
			
		else:
			if sub_batch.order > 0:
				filename = '/tmp/%s_%s' % (sub_batch.item_id, sub_batch.order)
				destination = '%s/%s.jp2' % (sub_batch.item_id, sub_batch.order)
			else:
				filename = '/tmp/%s' % sub_batch.item_id
				destination = '%s.jp2' % sub_batch.item_id
			
			urllib.urlretrieve (sub_batch.url, filename)
		
			if subprocess.check_output(['identify', '-format', '%m', filename]) != 'TIFF':
				subprocess.call(['convert', '-compress', 'none', filename, '%s.tif' % filename])
				os.remove('%s' % filename)
			else:
				os.rename('%s' % filename, '%s.tif' % filename)
		
			subprocess.call(['kdu_compress', '-i', '%s.tif' % filename, '-o', '%s.jp2' % filename, '-rate', '-,0.5', 'Clayers=2', 'Creversible=yes', 'Clevels=8', 'Cprecincts={256,256},{256,256},{128,128}', 'Corder=RPCL', 'ORGgen_plt=yes', 'ORGtparts=R', 'Cblk={64,64}'])

			source_path = '%s.jp2' % filename
			source_size = os.stat(source_path).st_size
			chunk_count = int(math.ceil(source_size / float(S3_CHUNK_SIZE)))
			mp = bucket.initiate_multipart_upload(S3_DEFAULT_FOLDER + destination)
				
			for i in range(chunk_count):
				offset = S3_CHUNK_SIZE * i
				bytes = min(S3_CHUNK_SIZE, source_size - offset)
					
				with FileChunkIO(source_path, 'r', offset=offset, bytes=bytes) as fp:
					mp.upload_part_from_file(fp, part_num=i + 1)
				
			mp.complete_upload()
		
			test = identify_output_regular.search(subprocess.check_output(['identify', '-format', '{"width": %w, "height": %h}', '%s.tif' % filename]))
		
			if test:
				sub_batch.image_meta = json.loads(test.group('size_json'))
				sub_batch.image_meta['filename'] = destination
				sub_batch.image_meta['order'] = sub_batch.order
			else:
				raise Exception
		
			os.remove('%s.jp2' % filename)
			os.remove('%s.tif' % filename)

			sub_batch.status = 'ok'
			sub_batch.save()

	except:
		sub_batch.attempts += 1
		
		if sub_batch.attempts < MAX_SUB_BATCH_REPEAT:
			sub_batch.save()
			rand = (sub_batch.attempts * 60) + random.randint(sub_batch.attempts * 60, sub_batch.attempts * 60 * 2)

			return ingestQueue.apply_async(args=[batch.id, sub_batch.id], countdown=rand)
		else:
			if sub_batch.type != 'del':
				sub_batch.status = 'error'
			else:
				sub_batch.status = 'deleted'
				
			sub_batch.save()

	if batch.increment_finished_images() >= batch.sub_batches_count:
		finalizeIngest(batch)
		
	return


def finalizeIngest(batch):
	items = {}

	try:
		cloudsearch = getCloudSearch()
	except:
		cloudsearch = None
	
	for sub_batch_id in batch.sub_batches_ids:
		sub_batch = SubBatch(sub_batch_id, batch.id)
				
		if items.has_key(sub_batch.item_id):
			items[sub_batch.item_id].append((sub_batch.url, sub_batch.image_meta, sub_batch.status))
		else:
			items[sub_batch.item_id] = [(sub_batch.url, sub_batch.image_meta, sub_batch.status)]

	for order in range(0, len(batch.items)):
		item_id = batch.items[order]['id']
		
		if item_id in items.keys():
			item = Item(item_id)
		else:
			continue
		
		if batch.items[order]['status'] == 'deleted':
			item.delete()
			
			# cloudsearch item del
			if cloudsearch is not None:
				cloudsearch.delete(item.id)
		else:
			item_status = 'ok'
		
			for data in items[item_id]:
				url = data[0]
				image_meta = data[1]
				sub_batch_status = data[2]
				
				if sub_batch_status == 'pending' or sub_batch_status == 'error':
					item_status = 'error'
					
					for i in range(0,len(item.url)):
						if item.url[i] == url:
							del item.url[i]
							break
				else:				
					if sub_batch_status == 'deleted':
						# if the image is being realy deleted not only being reshaffled
						if not url in item.url:
							item.image_meta.pop(url, None)
					else:
						item.image_meta[url] = image_meta
		
			batch.items[order]['status'] = item_status
			
			if item_status == 'error':
				try:
					bucket = getBucket()
				
					for url in item.url:
						filename = item.image_meta[url]['filename']
			
						if filename:
							bucket.delete_key(S3_DEFAULT_FOLDER + filename)
				except:
					pass
					
				item.delete()
	
				# cloudsearch item del
				if cloudsearch is not None:
					cloudsearch.delete(item.id)
			else:
				item.lock = False
				item.save()
				
				# cloudsearch item add (or update)
				if cloudsearch is not None:
					cloudsearch.add(item.id, {'id': item.id, 'title': item.title, 'creator': item.creator, 'source': item.source, 'institution': item.institution, 'institution_link': item.institution_link, 'license': item.license, 'description': item.description})
	
	# commit all items to cloudsearch at once
	if cloudsearch is not None:		
		cloudsearch.commit()
		cloudsearch.clear_sdf()
		
	batch.save()

	return


def getBucket():
	os.environ['S3_USE_SIGV4'] = 'True'
	s3 = boto.connect_s3(host=S3_HOST)
	return s3.get_bucket(S3_DEFAULT_BUCKET)


def getCloudSearch():
	return boto.connect_cloudsearch2(region=CLOUDSEARCH_REGION, sign_request=True).lookup(CLOUDSEARCH_DOMAIN).get_document_service()
