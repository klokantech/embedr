import simplejson as json
from flask.ext.redis import Redis

from exceptions import NoItemInDb, ErrorItemImport

db = Redis()


class Item():
	def __init__(self, id, data=None):
		self.id = id
		self.title = ''
		self.creator = ''
		self.source = ''
		self.institution = ''
		self.institution_link = ''
		self.licence = ''
		self.description = ''
		self.url = []
		self.image_meta = {}
		
		if data:
			try:
				data = json.loads(json.JSONEncoder().encode(data))
			except:
				raise ErrorItemImport('There is an error in the item`s model representation %s' % data)
		else:
			data = db.get(id)
			
			if not data:
				raise NoItemInDb('No item with specified id stored in db')
			else:
				try:
					data = json.loads(data)
				except:
					raise ErrorItemImport('There is an error in the item`s model representation %s' % data)	
					
		if data.has_key('id') and data.has_key('url'):
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
		if data.has_key('licence'):
			self.licence = data['licence']
		if data.has_key('description'):
			self.description = data['description']
		if data.has_key('image_meta'):
			self.image_meta = data['image_meta']


	def save(self):
		db.set(self.id, json.dumps(self.__dict__))
		
		
class Batch():
	def __init__(self, id=None):
		self.items = []
		self.sub_batches_count = 0
		self.finished_images = 0
		self.sub_batches_ids = []
		self.status = 'pending'

		if id is None:
			self.id = db.incr('batch@id', 1)
		else:
			self.id = id
			
			data = db.get('batch@id:%s' % id)

			if not data:
				raise NoItemInDb('No batch with specified id stored in db')
			else:
				try:
					data = json.loads(data)
					
					if data.has_key('items'):
						self.items = data['items']
						
						if type(self.items) != list:
							raise ErrorItemImport('There is an error in the batch`s model representation %s' % data)
					if data.has_key('sub_batches_count'):
						self.sub_batches_count = int(data['sub_batches_count'])
					if data.has_key('sub_batches_ids'):
						self.sub_batches_ids = data['sub_batches_ids']
						
						if type(self.sub_batches_ids) != list:
							raise ErrorItemImport('There is an error in the batch`s model representation %s' % data)
							
					finished_images = db.get('batch@id:%s:finished_images' % self.id)
					
					if finished_images:
						self.finished_images = int(finished_images)
					
					if data.has_key('status'):
						self.status = data['status']
											
				except:
					raise ErrorItemImport('There is an error in the batch`s model representation %s' % data)

	
	def save(self):
		db.set('batch@id:%s' % self.id, json.dumps({'items': self.items, 'sub_batches_count': self.sub_batches_count, 'sub_batches_ids': self.sub_batches_ids}))
	
	
	def increment_finished_images(self):
		return db.incr('batch@id:%s:finished_images' % self.id, 1)


class SubBatch():
	def __init__(self, id, batch_id, data=None):
		self.id = id
		self.batch_id = batch_id
		self.status = 'pending'
		self.url = ''
		self.order = 0
		self.item_id = ''
		self.image_meta = ''
		self.attempts = 0
		
		safe = True
		
		if data is None:
			data = db.get('batch@id:%s:sub_batch:id:%s' % (self.batch_id, self.id))

			if not data:
				raise NoItemInDb('No sub_batch with specified id stored in db')
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
		if data.has_key('order'):
			self.order = data['order']
		if data.has_key('item_id'):
			self.item_id = data['item_id']
		if data.has_key('image_meta'):
			self.image_meta = data['image_meta']
		if data.has_key('attempts'):
			self.attempts = data['attempts']
		
		if safe:
			self.save()

	
	def save(self):
		db.set('batch@id:%s:sub_batch:id:%s' % (self.batch_id, self.id), json.dumps(self.__dict__))
