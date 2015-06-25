import os
import urllib
import math
import subprocess
import time
import random
import re
import hashlib

import simplejson as json
import redis
from filechunkio import FileChunkIO
import requests

from app.task_queue import task_queue
from models import Item, Batch, Task
from exceptions import NoItemInDb, ErrorItemImport
from helper import getBucket, getCloudSearch


identify_output_regular = re.compile(r'''
	^
	(?P<size_json>.+)
	\n$
	''', re.VERBOSE)

S3_CHUNK_SIZE = int(os.getenv('S3_CHUNK_SIZE', 52428800))
S3_DEFAULT_FOLDER = os.getenv('S3_DEFAULT_FOLDER', '')
MAX_TASK_REPEAT = int(os.getenv('MAX_TASK_REPEAT', 1))


@task_queue.task
def ingestQueue(batch_id, item_id, task_id):
	try:
		task = Task(batch_id, item_id, task_id)
	except NoItemInDb, ErrorItemImport:
		return -1
	
	try:
		bucket = getBucket()
		
		if task.type == 'del':
			try:
				item = Item(item_id)
				filename = item.image_meta[task.url]['filename']
			
				if filename:
					bucket.delete_key(S3_DEFAULT_FOLDER + filename)
			except NoItemInDb:
				pass

			task.status = 'deleted'
		
		elif task.type == 'mod':
			task.status = 'ok'
			
		else:
			if task.url_order > 0:
				filename = '/tmp/%s_%s' % (item_id, task.url_order)
				destination = '%s/%s.jp2' % (item_id, task.url_order)
			else:
				filename = '/tmp/%s' % item_id
				destination = '%s.jp2' % item_id
			
			urllib.urlretrieve (task.url, filename)
		
			if subprocess.check_output(['identify', '-format', '%m', filename]) != 'TIFF':
				subprocess.call(['convert', '-compress', 'none', filename, '%s.tif' % filename])
				os.remove('%s' % filename)
			else:
				os.rename('%s' % filename, '%s.tif' % filename)
	
			test = identify_output_regular.search(subprocess.check_output(['identify', '-format', '{"width": %w, "height": %h}', '%s.tif' % filename]))
		
			if test:
				task.image_meta = json.loads(test.group('size_json'))
				task.image_meta['filename'] = destination
				task.image_meta['order'] = task.url_order
			else:
				raise Exception
		
			subprocess.call(['kdu_compress', '-i', '%s.tif' % filename, '-o', '%s.jp2' % filename, '-rate', '0.5', 'Clayers=1', 'Clevels=7', 'Cprecincts={256,256},{256,256},{256,256},{128,128},{128,128},{64,64},{64,64},{32,32},{16,16}', 'Corder=RPCL', 'ORGgen_plt=yes', 'ORGtparts=R', 'Cblk={64,64}', 'Cuse_sop=yes'])

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
		
			os.remove('%s.jp2' % filename)
			os.remove('%s.tif' % filename)

			task.status = 'ok'
		
		# is this the task with highest id for the specific item? (only last created task for specific item
		# has its data)
		if task.item_data:
			cloudsearch = getCloudSearch()
			
			if task.item_data.has_key('status') and task.item_data['status'] == 'deleted':
				cloudsearch.delete(hashlib.sha512(item_id).hexdigest()[:128])
			else:
				item = Item(item_id, task.item_data)
				cloudsearch.add(hashlib.sha512(item_id).hexdigest()[:128], {'id': item.id, 'title': item.title, 'creator': item.creator, 'source': item.source, 'institution': item.institution, 'institution_link': item.institution_link, 'license': item.license, 'description': item.description})
			
			cloudsearch.commit()
		
		task.save()

	except:
		task.attempts += 1
		
		if task.attempts < MAX_TASK_REPEAT:
			task.save()
			rand = (task.attempts * 60) + random.randint(task.attempts * 60, task.attempts * 60 * 2)

			return ingestQueue.apply_async(args=[batch_id, task.id], countdown=rand)
		else:
			task.status = 'error'
			task.save()

	if task.increment_finished_item_tasks() >= task.item_tasks_count:
		finalizeItem(batch_id, item_id, task.item_tasks_count)
		
	return


def finalizeItem(batch_id, item_id, item_tasks_count):
	item_tasks = []
	
	for task_order in range(0, item_tasks_count):
		item_tasks.append(Task(batch_id, item_id, task_order))
	
	# the task with highest id for the specific item has all item data
	item_data = item_tasks[-1].item_data
	
	try:
		old_item = Item(item_id)
	except:
		old_item = None

	if old_item:
		if item_data.has_key('status') and item_data['status'] == 'deleted':
			old_item.delete()
			
			return
		else:
			item_data['image_meta'] = old_item.image_meta
	else:
		item_data['image_meta'] = {}
	
	error = False
	
	for task in item_tasks:
		if task.status == 'pending' or task.status == 'error':
			error = True
		elif task.status == 'deleted':
			# if the image is being realy deleted not only being reshaffled
			if not task.url in item_data['url']:
				item_data['image_meta'].pop(task.url, None)
		elif task.status == 'ok':
			item_data['image_meta'][task.url] = task.image_meta

	if not error:
		item = Item(item_id, item_data)	
		item.save()
	else:
		cleanErrItem(item_id, item_data['image_meta'])
	
	return


def cleanErrItem(item_id, urls):
	try:
		bucket = getBucket()
		
		for url in urls.keys():
			filename = urls[url]['filename']
			bucket.delete_key(S3_DEFAULT_FOLDER + filename)
	except:
		pass
	
	try:
		cloudsearch = getCloudSearch()
		cloudsearch.delete(hashlib.sha512(item_id).hexdigest()[:128])
		cloudsearch.commit()
	except:
		pass

	try:
		Item(item_id).delete()
	except:
		pass
	
	return
