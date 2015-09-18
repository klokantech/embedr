"""Module which provides wrapper for database. It can wraps redis and fakeredis for testing"""

import redis
import fakeredis

from exceptions import UnsupportedDbBackend


class DatabaseWrapper():
	"""Class which provides wrapper for database and can be used to instantiate database itself"""
	
	def init_db(self, backend=None):
		"""Method for initialization of database wrapper.
		   'backend' - desired backend for database, it can be redis or fakeredis for testing
		"""
		
		if not isinstance(backend, redis.StrictRedis) and not isinstance(backend, fakeredis.FakeStrictRedis):
			raise UnsupportedDbBackend('%s database backend is not allowed' % backend)
		self.backend = backend
		
		return self
	
	def get(self, key):
		"""Method for getting of data from database by unique key.
		   'key' - unique key to database
		"""
		
		return self.backend.get(key)
	
	def set(self, key, data):
		"""Method for setting of data to database by unique key.
		   'key' - unique key to database
		   'data' - data which have to be pushed to database and be reachable by key
		"""
		
		return self.backend.set(key, data)
	
	def delete(self, key):
		"""Method for deleting of data from database by unique key.
		   'key' - unique key to database
		"""
		
		return self.backend.delete(key)
		
	def incr(self, key, default):
		"""Method for atomically increasing numerical data in database. It is needed for implementation of counters.
		   'key' - unique key to database
		   'default' - numerical value which is set if the key is not available in database
		"""
		
		return self.backend.incr(key, default)
