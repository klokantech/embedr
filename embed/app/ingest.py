import os
import urllib
import math
import subprocess
import time
import random
import re

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
		cloud_search = getCloudSearch()
		
		if task.type == 'del':
			try:
				item = Item(item_id)
				filename = item.image_meta[task.url]['filename']
			
				if filename:
					bucket.delete_key(S3_DEFAULT_FOLDER + filename)
			except NoItemInDb:
				pass

			task.status = 'deleted'
			task.save()
		
		elif task.type == 'mod':
			item = Item(item_id)
			
			cloudsearch.add(item.id[:127], {'id': item.id, 'title': item.title, 'creator': item.creator, 'source': item.source, 'institution': item.institution, 'institution_link': item.institution_link, 'license': item.license, 'description': item.description})
			cloudsearch.commit()
			cloudsearch.clear_sdf()
			
			task.status = 'ok'
			task.save()
			
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
				task.image_meta = json.loads(test.group('size_json'))
				task.image_meta['filename'] = destination
				task.image_meta['order'] = task.url_order
			else:
				raise Exception
		
			os.remove('%s.jp2' % filename)
			os.remove('%s.tif' % filename)

			task.status = 'ok'
			task.save()

	except:
		task.attempts += 1
		
		if task.attempts < MAX_TASK_REPEAT:
			task.save()
			rand = (task.attempts * 60) + random.randint(task.attempts * 60, task.attempts * 60 * 2)

			return ingestQueue.apply_async(args=[batch_id, task.id], countdown=rand)
		else:
			if task.type != 'del':
				task.status = 'error'
			else:
				task.status = 'deleted'
				
			task.save()

	if task.increment_finished_item_tasks() >= task.item_tasks_count:
		finalizeItem(batch_id, item_id, task.item_tasks_count)
		
	return


def finalizeItem(batch_id, item_id, item_tasks_count):
	try:
		cloudsearch = getCloudSearch()
	except:
		cleanUnfinishedItem(item_id)
	
	item_tasks = []
	
	for task_order in range(0, item_tasks_count):
		item_tasks.append(Task(batch_id, item_id, task_order))
	
	# the last task has all item data
	item_data = item_tasks[-1].item_data
	
	try:
		old_item = Item(item_id)
	except:
		old_item = None
	
	if old_item:
		if item_data.has_key('status') and item_data['status'] == 'deleted':
			try:
				cloudsearch.delete(old_item.id[:127])
				cloudsearch.commit()
				cloudsearch.clear_sdf()
				old_item.delete()
			except:
				cleanUnfinishedItem(old_item.id)
			
			return
		else:
			item_data['image_meta'] = old_item.image_meta
	
	for task in item_tasks:
		if task.status == 'pending' or task.status == 'error':
			if task.type != 'del':
				cleanUnfinishedItem(old_item.id)
				return
			else:
				task.status = 'ok'
				task.save()
		elif task.status == 'deleted':
			item_data['image_meta'].pop(task.url, None)
		elif task.status == 'ok':
			item_data['image_meta'][task.url] = task.image_meta

	item = Item(item_id, item_data)
	
	try:
		cloudsearch.add(item.id[:127], {'id': item.id, 'title': item.title, 'creator': item.creator, 'source': item.source, 'institution': item.institution, 'institution_link': item.institution_link, 'license': item.license, 'description': item.description})
		cloudsearch.commit()
		cloudsearch.clear_sdf()
	except:
		cleanUnfinishedItem(old_item.id)
	
	item.save()
	
	return


def cleanUnfinishedItem(item_id):
	try:
		item = Item(item_id)
	except:
		return
	
	try:
		bucket = getBucket()
				
		for url in item.url:
			filename = item.image_meta[url]['filename']
			
			if filename:
				bucket.delete_key(S3_DEFAULT_FOLDER + filename)
	except:
		pass
	
	try:
		cloudsearch = getCloudSearch()
		cloudsearch.delete(item.id[:127])
	except:
		pass

	item.delete()
	
	return
