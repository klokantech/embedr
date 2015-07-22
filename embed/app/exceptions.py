"""Module which provides user defined exceptions"""

class NoItemInDb(Exception):
	pass

class ErrorItemImport(Exception):
	pass

class UnsupportedDbBackend(Exception):
	pass

class ErrorImageIdentify(Exception):
	pass

class WrongCloudSearchService(Exception):
	pass
