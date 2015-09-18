"""Module which provides ingest functionality and which can be run by celery"""

import os
import sys
import urllib2
import math
import subprocess
import time
import random
import hashlib
from datetime import datetime
import traceback
import sqlite3
import shutil

import simplejson as json
import redis
from filechunkio import FileChunkIO
import requests
import boto.exception

from app.task_queue import task_queue
from models import Item, Task
from exceptions import NoItemInDb, ErrorItemImport, ErrorImageIdentify
from helper import getBucket, getCloudSearch


S3_CHUNK_SIZE = int(os.getenv('S3_CHUNK_SIZE', 52428800))
S3_DEFAULT_FOLDER = os.getenv('S3_DEFAULT_FOLDER', '')
S3_HOST = os.getenv('S3_HOST', None)
S3_DEFAULT_BUCKET = os.getenv('S3_DEFAULT_BUCKET', None)
MAX_TASK_REPEAT = int(os.getenv('MAX_TASK_REPEAT', 1))
URL_OPEN_TIMEOUT = int(os.getenv('URL_OPEN_TIMEOUT', 10))
CLOUDSEARCH_ITEM_DOMAIN = os.getenv('CLOUDSEARCH_ITEM_DOMAIN', None)

ERR_MESSAGE_CLOUDSEARCH = 5
ERR_MESSAGE_HTTP = 4
ERR_MESSAGE_IMAGE = 3
ERR_MESSAGE_S3 = 2
ERR_MESSAGE_OTHER = 1
ERR_MESSAGE_NONE = 0

@task_queue.task
def ingestQueue(batch_id, item_id, task_id):
	try:
		task = Task(batch_id, item_id, task_id)
	except NoItemInDb, ErrorItemImport:
		return -1
	
	try:
		if S3_HOST is not None and S3_DEFAULT_BUCKET is not None:
			bucket = getBucket()
		else:
			# local storage only
			bucket = None
		
		if task.type == 'del':
			try:
				item = Item(item_id)
				
				if task.url_order > 0:
					filename = '%s/%s.jp2' % (item_id, task.url_order)

				else:
					filename = '%s.jp2' % item_id

				if bucket is not None:
					bucket.delete_key(S3_DEFAULT_FOLDER + filename)
				else:
					os.remove('/data/jp2/%s' % filename)
					
			except NoItemInDb:
				pass

			task.status = 'deleted'
		
		elif task.type == 'mod':
			task.status = 'ok'
		
		elif task.type == 'cloud_search':
			task.status = 'ok'
			
		elif task.type == 'add':
			if task.url_order > 0:
				filename = '/tmp/%s_%s' % (item_id, task.url_order)
				destination = '%s/%s.jp2' % (item_id, task.url_order)
			else:
				filename = '/tmp/%s' % item_id
				destination = '%s.jp2' % item_id
			
			if task.url_order == 1:
				# folder creation
				if bucket is not None:
					f = bucket.new_key('%s/' % item_id)
					f.set_contents_from_string('')
				else:
					if not os.path.exists('/data/jp2/%s' % item_id):
						os.makedirs('/data/jp2/%s/' % item_id)
			
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
				raise ErrorImageIdentify('Error in the image identify process')
		
			subprocess.call(['kdu_compress', '-i', '%s.tif' % filename, '-o', '%s.jp2' % filename, '-rate', '0.5', 'Clayers=1', 'Clevels=7', 'Cprecincts={256,256},{256,256},{256,256},{128,128},{128,128},{64,64},{64,64},{32,32},{16,16}', 'Corder=RPCL', 'ORGgen_plt=yes', 'ORGtparts=R', 'Cblk={64,64}', 'Cuse_sop=yes', '-quiet'])

			source_path = '%s.jp2' % filename
			
			if bucket is not None:
				source_size = os.stat(source_path).st_size
				chunk_count = int(math.ceil(source_size / float(S3_CHUNK_SIZE)))
				mp = bucket.initiate_multipart_upload(S3_DEFAULT_FOLDER + destination)
				
				for i in range(chunk_count):
					offset = S3_CHUNK_SIZE * i
					bytes = min(S3_CHUNK_SIZE, source_size - offset)
					
					with FileChunkIO(source_path, 'r', offset=offset, bytes=bytes) as fp:
						mp.upload_part_from_file(fp, part_num=i + 1)
				
				mp.complete_upload()
			
			else:
				shutil.copy('%s.jp2' % filename, '/data/jp2/%s' % destination)
			
			os.remove('%s.jp2' % filename)
			os.remove('%s.tif' % filename)

			task.status = 'ok'
					
		task.save()

	except:
		exception_type = sys.exc_info()[0]

		if exception_type is urllib2.HTTPError or exception_type is urllib2.URLError:
			task.message = ERR_MESSAGE_HTTP
		elif exception_type is subprocess.CalledProcessError:
			task.message = ERR_MESSAGE_IMAGE
		elif exception_type is boto.exception.S3ResponseError:
			task.message = ERR_MESSAGE_S3
		else:
			task.message = ERR_MESSAGE_OTHER
		
		print '\nFailed attempt numb.: %s\nItem: %s\nUrl: %s\nError message:\n###\n%s###' % (task.attempts + 1, task.item_id, task.url, traceback.format_exc())
		task.attempts += 1
		
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
			task.status = 'pending'
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
	last_task = item_tasks[-1]
	item_data = last_task.item_data
	item_data['timestamp'] = datetime.utcnow().isoformat("T") + "Z"
	
	if item_data.has_key('status') and item_data['status'] == 'deleted':
		whole_item_delete = True
	else:
		whole_item_delete = False
	
	try:
		old_item = Item(item_id)
	except:
		old_item = None

	if old_item:
		if not whole_item_delete:
			item_data['image_meta'] = old_item.image_meta
	else:
		item_data['image_meta'] = {}
	
	error = False
	
	if not whole_item_delete:
		for task in item_tasks:
			if task.status == 'pending' or task.status == 'error':
				error = True
			# modification tasks never changes image_meta
			elif task.type == 'mod':
				pass
			elif task.status == 'deleted':
				# if the image is being really deleted not only being reshuffled
				if not task.url in item_data['url']:
					item_data['image_meta'].pop(task.url, None)
			elif task.status == 'ok':
				item_data['image_meta'][task.url] = task.image_meta

	if not error:
		if not (old_item and whole_item_delete):
			item = Item(item_id, item_data)
			ordered_image_meta = []
		
			for url in item.url:
				tmp = item.image_meta[url]
				tmp['url'] = url
				ordered_image_meta.append(tmp)
			
		if CLOUDSEARCH_ITEM_DOMAIN is not None:
			try:
				cloudsearch = getCloudSearch(CLOUDSEARCH_ITEM_DOMAIN, 'document')
				
				if old_item and whole_item_delete:
					cloudsearch.delete(hashlib.sha512(item_id).hexdigest()[:128])
				else:
					cloudsearch.add(hashlib.sha512(item_id).hexdigest()[:128], {'id': item.id, 'title': item.title, 'creator': item.creator, 'source': item.source, 'institution': item.institution, 'institution_link': item.institution_link, 'license': item.license, 'description': item.description, 'url': json.dumps(item.url), 'timestamp': item.timestamp, 'image_meta': json.dumps(ordered_image_meta)})
				
				cloudsearch.commit()
			
			except:
				if last_task.attempts < MAX_TASK_REPEAT * 2:
					print '\nFailed Cloud Search attempt numb.: %s\nItem: %s\nError message:\n###\n%s###' % (last_task.attempts + 1, task.item_id, traceback.format_exc())
					last_task.attempts += 1
					last_task.status = 'pending'
					last_task.type = 'cloud_search'
					last_task.save()
					rand = (last_task.attempts * 60) + random.randint(last_task.attempts * 60, last_task.attempts * 60 * 2)

					return ingestQueue.apply_async(args=[batch_id, item_id, last_task.task_id], countdown=rand)
				else:
					last_task.status = 'error'
					last_task.message = ERR_MESSAGE_CLOUDSEARCH
					last_task.save()
		
		if last_task.status == 'error':
			cleanErrItem(item_id, len(item_data['image_meta']))
			print "Item '%s' failed" % item_id
		elif old_item and whole_item_delete:
			old_item.delete()
			print "Item '%s' deleted" % item_id
		else:
			item.save()
			print "Item '%s' finalized" % item_id
	
	else:
		cleanErrItem(item_id, len(item_data['image_meta']))
		print "Item '%s' failed" % item_id
	
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
		cloudsearch = getCloudSearch(CLOUDSEARCH_ITEM_DOMAIN, 'document')
		cloudsearch.delete(hashlib.sha512(item_id).hexdigest()[:128])
		cloudsearch.commit()
	except:
		pass

	try:
		Item(item_id).delete()
	except:
		pass
	
	return
