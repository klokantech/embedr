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
		self.image_meta = []
		
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

		if id == None:
			db.incr('batch@id', 1)
			self.id = db.get('batch@id')
		else:
			self.id = id
			
			tmp = db.get('batch@id:%s' % id)

			if not tmp:
				raise NoItemInDb('No batch with specified id stored in db')
			else:
				try:
					tmp = json.loads(tmp)
					
					if type(tmp) == list:
						self.items = tmp
					
				except:
					raise ErrorItemImport('There is an error in the batch`s model representation %s' % tmp)

	
	def save(self):
		db.set('batch@id:%s' % self.id, json.dumps(self.items))
