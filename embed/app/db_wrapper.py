import redis
import fakeredis

from exceptions import UnsupportedDbBackend


class DatabaseWrapper():
	def init_db(self, backend=None):
		if not isinstance(backend, redis.StrictRedis) and not isinstance(backend, fakeredis.FakeStrictRedis):
			raise UnsupportedDbBackend('%s database backend is not allowed' % backend)
		self.backend = backend
		
		return self
	
	def get(self, key):
		return self.backend.get(key)
	
	def set(self, key, data):
		return self.backend.set(key, data)
	
	def delete(self, delete):
		return self.backend.delete(key)
		
	def incr(self, key, default):
		return self.backend.incr(key, default)
