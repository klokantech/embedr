import os
import urllib2
import math
import subprocess
import time
import random
import hashlib
from datetime import datetime
import traceback

import simplejson as json
import redis
from filechunkio import FileChunkIO
import requests

from app.task_queue import task_queue
from models import Item, Batch, Task
from exceptions import NoItemInDb, ErrorItemImport
from helper import getBucket, getCloudSearch


S3_CHUNK_SIZE = int(os.getenv('S3_CHUNK_SIZE', 52428800))
S3_DEFAULT_FOLDER = os.getenv('S3_DEFAULT_FOLDER', '')
MAX_TASK_REPEAT = int(os.getenv('MAX_TASK_REPEAT', 1))
URL_OPEN_TIMEOUT = int(os.getenv('URL_OPEN_TIMEOUT', 10))
CLOUDSEARCH_ITEM_DOMAIN = os.getenv('CLOUDSEARCH_ITEM_DOMAIN', '')
CLOUDSEARCH_BATCH_DOMAIN = os.getenv('CLOUDSEARCH_BATCH_DOMAIN', '')


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
				
				if task.url_order > 0:
					filename = '%s/%s.jp2' % (item_id, task.url_order)

				else:
					filename = '%s.jp2' % item_id

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
			
			if task.url_order == 1:
				# folder creation
				f = bucket.new_key('%s/' % item_id)
				f.set_contents_from_string('')
			
			r = urllib2.urlopen(task.url, timeout=URL_OPEN_TIMEOUT)
			f = open(filename, 'wb')
			f.write(r.read())
			f.close()
		
			if subprocess.check_output(['identify', '-quiet', '-format', '%m', filename]) != 'TIFF':
				subprocess.call(['convert', '-quiet', '-compress', 'none', filename, '%s.tif' % filename])
				os.remove('%s' % filename)
			else:
				os.rename('%s' % filename, '%s.tif' % filename)
	
			test = subprocess.check_output(['identify', '-quiet', '-format', 'width:%w;height:%h;', '%s.tif' % filename])
		
			if test:
				tmp = test.split(';')
				width = int(tmp[0].split(':')[1])
				height = int(tmp[1].split(':')[1])
				task.image_meta = {"width": width, "height": height}
			else:
				raise Exception
		
			subprocess.call(['kdu_compress', '-i', '%s.tif' % filename, '-o', '%s.jp2' % filename, '-rate', '0.5', 'Clayers=1', 'Clevels=7', 'Cprecincts={256,256},{256,256},{256,256},{128,128},{128,128},{64,64},{64,64},{32,32},{16,16}', 'Corder=RPCL', 'ORGgen_plt=yes', 'ORGtparts=R', 'Cblk={64,64}', 'Cuse_sop=yes', '-quiet'])

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
				
		task.save()

	except:
		task.attempts += 1
		
		print(traceback.format_exc())
		
		try:
			if os.path.isfile('%s' % filename):
				os.remove('%s' % filename)
			if os.path.isfile('%s.jp2' % filename):
				os.remove('%s.jp2' % filename)
			if os.path.isfile('%s.tif' % filename):
				os.remove('%s.tif' % filename)
		except:
			pass
		
		if task.attempts < MAX_TASK_REPEAT:
			task.save()
			rand = (task.attempts * 60) + random.randint(task.attempts * 60, task.attempts * 60 * 2)

			return ingestQueue.apply_async(args=[batch_id, item_id, task_id], countdown=rand)
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
	item_data['timestamp'] = datetime.utcnow().isoformat("T") + "Z"
	
	try:
		old_item = Item(item_id)
	except:
		old_item = None

	if old_item:
		if item_data.has_key('status') and item_data['status'] == 'deleted':
			i = 0
			
			while MAX_TASK_REPEAT > i:
				try:
					cloudsearch = getCloudSearch(CLOUDSEARCH_ITEM_DOMAIN)
					cloudsearch.delete(hashlib.sha512(item_id).hexdigest()[:128])
					cloudsearch.commit()
					break
				except:
					if i < MAX_TASK_REPEAT:
						i += 1
						rand = i + random.randint(i, i * 2)
						time.sleep(rand)
					
					continue
			
			if MAX_TASK_REPEAT > i:
				old_item.delete()
			else:
				item_tasks[-1].status = 'error'
				item_tasks[-1].save()
			
			return
		else:
			item_data['image_meta'] = old_item.image_meta
	else:
		item_data['image_meta'] = {}
	
	error = False
	
	for task in item_tasks:
		if task.status == 'pending' or task.status == 'error':
			error = True
		# modification tasks never changes image_meta
		elif task.type == 'mod':
			pass
		elif task.status == 'deleted':
			# if the image is being realy deleted not only being reshaffled
			if not task.url in item_data['url']:
				item_data['image_meta'].pop(task.url, None)
		elif task.status == 'ok':
			item_data['image_meta'][task.url] = task.image_meta

	if not error:
		item = Item(item_id, item_data)
		i = 0
		ordered_image_meta = []
		
		for url in item.url:
			tmp = item.image_meta[url]
			tmp['url'] = url
			ordered_image_meta.append(tmp)
			
		while MAX_TASK_REPEAT > i:
			try:
				cloudsearch = getCloudSearch(CLOUDSEARCH_ITEM_DOMAIN)
				cloudsearch.add(hashlib.sha512(item_id).hexdigest()[:128], {'id': item.id, 'title': item.title, 'creator': item.creator, 'source': item.source, 'institution': item.institution, 'institution_link': item.institution_link, 'license': item.license, 'description': item.description, 'url': json.dumps(item.url), 'timestamp': item.timestamp, 'image_meta': json.dumps(ordered_image_meta)})
				cloudsearch.commit()
				break
			except:
				if i < MAX_TASK_REPEAT:
					i += 1
					rand = i + random.randint(i, i * 2)
					time.sleep(rand)

				continue
			
		if MAX_TASK_REPEAT > i:
			item.save()
			print "Item '%s' finalized" % item.id
		else:
			item_tasks[-1].status = 'error'
			item_tasks[-1].save()
			cleanErrItem(item_id, len(item_data['image_meta']))

	else:
		cleanErrItem(item_id, len(item_data['image_meta']))
	
	batch = Batch(batch_id)
	
	if batch.increment_finished_items() >= len(batch.items):
		finalizeBatch(batch)
	
	return


def finalizeBatch(batch):
	i = 0
	items = batch.items
	
	for item in batch.data:
		unique_id = item['id']
		tmp = []
		item_tasks = {}
				
		for task_id in batch.items[unique_id]:
			task = Task(batch.id, unique_id, task_id)
				
			if not item_tasks.has_key(task.url) or (item_tasks.has_key(task.url) and item_tasks[task.url] != 'ok'):
				item_tasks[task.url] = task.status
		
		for url in item['url']:
			# actualy ingested url
			if item_tasks.has_key(url):
				tmp.append(item_tasks[url])
			# ingested url in past
			else:
				tmp.append('ok')
		
		items[unique_id] = tmp
	
	while MAX_TASK_REPEAT > i:
		try:
			cloudsearch = getCloudSearch(CLOUDSEARCH_BATCH_DOMAIN)
			cloudsearch.add(hashlib.sha512(str(batch.id)).hexdigest()[:128], {'id': batch.id, 'items': json.dumps(items), 'data': json.dumps(batch.data)})
			cloudsearch.commit()
			break
		except:
			if i < MAX_TASK_REPEAT:
				i += 1
				rand = i + random.randint(i, i * 2)
				time.sleep(rand)
			
			continue

	return


def cleanErrItem(item_id, count):
	try:
		bucket = getBucket()
		i = 0
		
		while count > i:
			if i == 0:
				filename = '%s.jp2' % item_id
			else:
				filename = '%s/%s.jp2' % (item_id, i)
			
			i += 1
			
			bucket.delete_key(S3_DEFAULT_FOLDER + filename)
		
		if count > 1:
			filename = '%s/' % item_id
			bucket.delete_key(S3_DEFAULT_FOLDER + filename)
		
	except:
		pass
	
	try:
		cloudsearch = getCloudSearch(CLOUDSEARCH_ITEM_DOMAIN)
		cloudsearch.delete(hashlib.sha512(item_id).hexdigest()[:128])
		cloudsearch.commit()
	except:
		pass

	try:
		Item(item_id).delete()
	except:
		pass
	
	return
