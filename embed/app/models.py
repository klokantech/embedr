"""Module which defines data model"""

import simplejson as json

from exceptions import NoItemInDb, ErrorItemImport
from db_wrapper import DatabaseWrapper

db = DatabaseWrapper()


class Item():
	"""Class which defines the Item model.
	'id' - item ID which is unique in whole db
	'data' - dictionary with Item's metadata
	"""
	
	def __init__(self, id, data=None):
		self.id = id
		self.title = ''
		self.creator = ''
		self.source = ''
		self.institution = ''
		self.institution_link = ''
		self.license = ''
		self.description = ''
		self.url = []
		self.image_meta = {}
		self.timestamp = ''
		
		if data:
			try:
				data = json.loads(json.JSONEncoder().encode(data))
			except:
				raise ErrorItemImport('There is an error in the item`s model representation %s' % data)
		else:
			data = db.get('item_id@%s' % id)
			
			if not data:
				raise NoItemInDb('No item with specified id stored in db')
			else:
				try:
					data = json.loads(data)
				except:
					raise ErrorItemImport('There is an error in the item`s model representation %s' % data)	
					
		if data.has_key('url'):
			self.url = data['url']
			
			if type(self.url) != list:
				raise ErrorItemImport('There is an error in the batch`s model representation %s' % data)
			
			for i,u in enumerate(self.url):
				self.url[i] = str(u)
		else:
			raise ErrorItemImport('The item doesn`t have all required params')
					
		if data.has_key('title'):
			self.title = data['title']
		if data.has_key('creator'):
			self.creator = data['creator']
		if data.has_key('source'):
			self.source = data['source']
		if data.has_key('institution'):
			self.institution = data['institution']
		if data.has_key('institution_link'):
			self.institution_link = data['institution_link']
		if data.has_key('license'):
			self.license = data['license']
		if data.has_key('description'):
			self.description = data['description']
		if data.has_key('image_meta'):
			self.image_meta = data['image_meta']
		if data.has_key('timestamp'):
			self.timestamp = data['timestamp']

	def save(self):
		db.set('item_id@%s' % self.id, json.dumps({'url': self.url, 'title': self.title, 'creator': self.creator, 'source': self.source, 'institution': self.institution, 'institution_link': self.institution_link, 'license': self.license, 'description': self.description, 'image_meta': self.image_meta, 'timestamp': self.timestamp}))
		
	def delete(self):
		db.delete('item_id@%s' % self.id)


class Task():
	"""Class which defines the Task model.
	'batch_id' - ID of parent Batch
	'item_id' - ID of processed Item
	'task_id' - ID of Task, it is order of tasks for one Item 
	'data' - dictionary with Task's metadata
	"""
	
	def __init__(self, batch_id, item_id, task_id, data=None):
		self.task_id = task_id
		self.batch_id = batch_id
		self.item_id = item_id
		self.status = 'pending'
		self.url = ''
		self.url_order = 0
		self.image_meta = ''
		self.attempts = 0
		self.type = 'mod'
		self.item_data = {}
		self.item_tasks_count = 0
		self.message = 0
		
		safe = True
		
		if data is None:
			data = db.get('batch@id@%s@item@id%s@task@id@%s' % (self.batch_id, self.item_id, self.task_id))

			if not data:
				raise NoItemInDb('No task with specified id stored in db')
			else:
				try:
					data = json.loads(data)
					safe = False
						
				except:
					raise ErrorItemImport('There is an error in the batch`s model representation %s' % data)
		
		if data.has_key('status'):
			self.status = data['status']
		if data.has_key('url'):
			self.url = data['url']
		if data.has_key('url_order'):
			self.url_order = data['url_order']
		if data.has_key('image_meta'):
			self.image_meta = data['image_meta']
		if data.has_key('attempts'):
			self.attempts = data['attempts']
		if data.has_key('type'):
			self.type = data['type']
		if data.has_key('item_data'):
			self.item_data = data['item_data']
		if data.has_key('item_tasks_count'):
			self.item_tasks_count = data['item_tasks_count']
		if data.has_key('message'):
			self.message = data['message']
		
		if safe:
			self.save()
	
	def save(self):
		db.set('batch@id@%s@item@id%s@task@id@%s' % (self.batch_id, self.item_id, self.task_id), json.dumps({'status': self.status, 'url': self.url, 'url_order': self.url_order, 'image_meta': self.image_meta, 'attempts': self.attempts, 'type': self.type, 'item_data': self.item_data, 'item_tasks_count': self.item_tasks_count, 'message': self.message}))
	
	def increment_finished_item_tasks(self):
		if self.item_id != '':
			return db.incr('batch@id@%s@item@id%s' % (self.batch_id, self.item_id), 1)
	
	def delete(self):
		db.delete('batch@id@%s@item@id%s@task@id@%s' % (self.batch_id, self.item_id, self.task_id))
