import os
import unittest

import fakeredis
import simplejson as json

from app import app_factory
from app.models import Item, Batch


class EmbedTestCase(unittest.TestCase):
	def setUp(self):
		app = app_factory(fakeredis.FakeStrictRedis())

		app.config.update(
			SERVER_NAME='127.0.0.1:5000',
			IIIF_SERVER='iiifhawk.klokantech.com'
		)
		
		self.app = app.test_client()
		app.extensions['redis'].set('item_id@test_id', json.dumps({'url': ['http://unittest_url.org', 'http://unittest_url2.org'], 'title': 'Unittest title', 'creator': 'Unittest creator', 'source': 'http://unittest_source.org','institution': 'Unittest institution', 'institution_link': 'http://unittest_institution_link.org', 'license': 'http://unittest_license_link.org', 'description': 'Unittest description', 'image_meta': {'http://unittest_url.org': {'width': 1000, 'height': 1000, 'filename': 'test_id.jp2', 'order': 0}, 'http://unittest_url2.org': {'width': 100, 'height': 100, 'filename': 'test_id/1.jp2', 'order': 1}}, 'lock': False}))

	def tearDown(self):
		pass
	
	def test_root(self):
		rv = self.app.get('/')
		assert rv.status_code == 200
	
	def test_iFrame0(self):
		rv = self.app.get('/test')
		assert rv.status_code == 404
	
	def test_iFrame1(self):
		rv = self.app.get('/test_id')
		assert rv.status_code == 200
		assert '<meta name="dc:title" content="Unittest title"/>' in rv.data
		assert '<meta name="dc:creator" content="Unittest creator"/>' in rv.data
		assert '<meta name="dc:source" content="http://unittest_source.org"/>' in rv.data
		assert '<meta name="dc:publisher" content="Unittest institution"/>' in rv.data
		assert '<meta name="dc:rights" content="http://unittest_license_link.org"/>' in rv.data
		assert '<meta name="dc:description" content="Unittest description"/>' in rv.data
		assert '<link rel="alternate" type="application/json+oembed" href="http://127.0.0.1:5000/oembed?url=http%3A//127.0.0.1%3A5000/test_id/0&format=json" title="Unittest title oEmbed Profile" />' in rv.data
		assert '<link rel="alternate" type="text/xml+oembed" href="http://127.0.0.1:5000/oembed?url=http%3A//127.0.0.1%3A5000/test_id/0&format=xml" title="Unittest title oEmbed Profile" />' in rv.data
		assert '''tileSources: [{"@context": "http://iiif.io/api/image/2/context.json", "@id": "http://iiifhawk.klokantech.com/test_id", "filename": "test_id.jp2", "height": 1000, "order": 0, "profile": ["http://iiif.io/api/image/2/level1.json", {"formats": ["jpg"], "qualities": ["native", "color", "gray"], "supports": ["regionByPct", "sizeByForcedWh", "sizeByWh", "sizeAboveFull", "rotationBy90s", "mirroring", "gray"]}], "protocol": "http://iiif.io/api/image", "tiles": [{"height": 256, "scaleFactors": [1, 2, 4], "width": 256}], "width": 1000}, {"@context": "http://iiif.io/api/image/2/context.json", "@id": "http://iiifhawk.klokantech.com/test_id/1", "filename": "test_id/1.jp2", "height": 100, "order": 1, "profile": ["http://iiif.io/api/image/2/level1.json", {"formats": ["jpg"], "qualities": ["native", "color", "gray"], "supports": ["regionByPct", "sizeByForcedWh", "sizeByWh", "sizeAboveFull", "rotationBy90s", "mirroring", "gray"]}], "protocol": "http://iiif.io/api/image", "tiles": [{"height": 256, "scaleFactors": [1], "width": 256}], "width": 100}]''' in rv.data

	def test_iFrame2(self):
		rv = self.app.get('/test_id/0')
		assert rv.status_code == 200
		assert '<link rel="alternate" type="application/json+oembed" href="http://127.0.0.1:5000/oembed?url=http%3A//127.0.0.1%3A5000/test_id/0&format=json" title="Unittest title oEmbed Profile" />' in rv.data
		assert '<link rel="alternate" type="text/xml+oembed" href="http://127.0.0.1:5000/oembed?url=http%3A//127.0.0.1%3A5000/test_id/0&format=xml" title="Unittest title oEmbed Profile" />' in rv.data
		assert '''tileSources: [{"@context": "http://iiif.io/api/image/2/context.json", "@id": "http://iiifhawk.klokantech.com/test_id", "filename": "test_id.jp2", "height": 1000, "order": 0, "profile": ["http://iiif.io/api/image/2/level1.json", {"formats": ["jpg"], "qualities": ["native", "color", "gray"], "supports": ["regionByPct", "sizeByForcedWh", "sizeByWh", "sizeAboveFull", "rotationBy90s", "mirroring", "gray"]}], "protocol": "http://iiif.io/api/image", "tiles": [{"height": 256, "scaleFactors": [1, 2, 4], "width": 256}], "width": 1000}]''' in rv.data
    
	def test_iFrame3(self):
		rv = self.app.get('/test_id/1')
		assert rv.status_code == 200
		assert '<link rel="alternate" type="application/json+oembed" href="http://127.0.0.1:5000/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1&format=json" title="Unittest title oEmbed Profile" />' in rv.data
		assert '<link rel="alternate" type="text/xml+oembed" href="http://127.0.0.1:5000/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1&format=xml" title="Unittest title oEmbed Profile" />' in rv.data
		assert '''tileSources: [{"@context": "http://iiif.io/api/image/2/context.json", "@id": "http://iiifhawk.klokantech.com/test_id/1", "filename": "test_id/1.jp2", "height": 100, "order": 1, "profile": ["http://iiif.io/api/image/2/level1.json", {"formats": ["jpg"], "qualities": ["native", "color", "gray"], "supports": ["regionByPct", "sizeByForcedWh", "sizeByWh", "sizeAboveFull", "rotationBy90s", "mirroring", "gray"]}], "protocol": "http://iiif.io/api/image", "tiles": [{"height": 256, "scaleFactors": [1], "width": 256}], "width": 100}]''' in rv.data

	def test_iFrame4(self):
		rv = self.app.get('/test_id/2')
		assert rv.status_code == 404
		assert 'Wrong item sequence' in rv.data

	def test_iFrame5(self):
		item = Item('test_id')
		item.lock = True
		item.save()
		
		rv = self.app.get('/test_id')
		assert rv.status_code == 404
		assert 'The item is being ingested' in rv.data
		
		item.lock = False
		item.save()
		
		rv = self.app.get('/test_id')
		assert rv.status_code == 200
	
	def test_iiifMeta0(self):
		rv = self.app.get('/test_id/manifest.json')
		assert rv.status_code == 200
		assert '''{"@context": "http://iiif.io/api/presentation/2/context.json", "@id": "http://127.0.0.1:5000/test_id/manifest.json", "@type": "sc:Manifest", "label": "Unittest title", "metadata": [{"label": "Author", "value": "Unittest creator"}, {"label": "Source", "value": "http://unittest_source.org"}, {"label": "Institution", "value": "Unittest institution"}, {"label": "Institution link", "value": "http://unittest_institution_link.org"}], "description": "Unittest description", "license": "http://unittest_license_link.org", "sequences": [{"@id": "http://127.0.0.1:5000/sequence/s.json", "@type": "sc:Sequence", "label": "Item test_id - sequence 1", "canvases": [{"@id": "http://127.0.0.1:5000/canvas/c0.json", "@type": "sc:Canvas", "label": "Item test_id - image 0", "height": 1000, "width": 1000, "images": [{"@type": "oa:Annotation", "motivation": "sc:painting", "resource": {"@id": "http://iiifhawk.klokantech.com/test_id/full/full/0/native.jpg", "@type": "dctypes:Image", "height": 1000, "width": 1000, "service": {"@context": "http://iiif.io/api/image/2/context.json", "@id": "http://iiifhawk.klokantech.com/test_id", "profile": "http://iiif.io/api/image/2/profiles/level2.json"}}, "on": "http://127.0.0.1:5000/canvas/c0.json"}]}, {"@id": "http://127.0.0.1:5000/canvas/c1.json", "@type": "sc:Canvas", "label": "Item test_id - image 1", "height": 100, "width": 100, "images": [{"@type": "oa:Annotation", "motivation": "sc:painting", "resource": {"@id": "http://iiifhawk.klokantech.com/test_id/1/full/full/0/native.jpg", "@type": "dctypes:Image", "height": 100, "width": 100, "service": {"@context": "http://iiif.io/api/image/2/context.json", "@id": "http://iiifhawk.klokantech.com/test_id/1", "profile": "http://iiif.io/api/image/2/profiles/level2.json"}}, "on": "http://127.0.0.1:5000/canvas/c1.json"}]}]}]}''' in rv.data
	
	def test_oEmbed0(self):
		rv = self.app.get('/oembed')
		assert rv.status_code == 404
		assert 'No url parameter provided' in rv.data
	
	def test_oEmbed1(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1&format=wrong_format')
		assert rv.status_code == 501
		assert 'The format parameter must be "json" or "xml" (or blank)' in rv.data

	def test_oEmbed2(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1&format=json')
		assert rv.status_code == 200
		assert '{"provider_url": "http://unittest_institution_link.org", "title": "Unittest title", "url": "http://iiifhawk.klokantech.com/test_id/1/full/full/0/native.jpg", "author_name": "Unittest creator", "height": "100", "width": "100", "version": "1.0", "author_url": "http://unittest_source.org", "provider_name": "Unittest institution", "type": "photo"}' in rv.data

	def test_oEmbed3(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1&format=xml')
		assert rv.status_code == 200
		assert '''<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<oembed>
	<version>1.0</version>
    <type>photo</type>
    <title>Unittest title</title>
    <url>http://iiifhawk.klokantech.com/test_id/1/full/full/0/native.jpg</url>
    <width>100</width>
    <height>100</height>
    <author_name>Unittest creator</author_name>
    <author_url>http://unittest_source.org</author_url>
    <provider_name>Unittest institution</provider_name>
    <provider_url>http://unittest_institution_link.org</provider_url>
</oembed>''' in rv.data

	def test_oEmbed4(self):
		rv = self.app.get('/oembed?url=https%3A//127.0.0.1%3A5000/test_id/1&format=json')
		assert rv.status_code == 404
		assert 'The http scheme must be used' in rv.data

	def test_oEmbed5(self):
		rv = self.app.get('/oembed?url=http%3A//192.168.1.1%3A5000/test_id/1&format=json')
		assert rv.status_code == 404
		assert 'Only urls on the same server are allowed' in rv.data

	def test_oEmbed6(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/@test_id/1&format=json')
		assert rv.status_code == 404
		assert 'Unsupported format of ID' in rv.data

	def test_oEmbed7(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/test_id/2&format=json')
		assert rv.status_code == 404
		assert 'Wrong item sequence' in rv.data

	def test_oEmbed8(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1')
		assert rv.status_code == 200
		assert '{"provider_url": "http://unittest_institution_link.org", "title": "Unittest title", "url": "http://iiifhawk.klokantech.com/test_id/1/full/full/0/native.jpg", "author_name": "Unittest creator", "height": "100", "width": "100", "version": "1.0", "author_url": "http://unittest_source.org", "provider_name": "Unittest institution", "type": "photo"}' in rv.data

	def test_oEmbed9(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1&maxwidth=50')
		assert rv.status_code == 200
		assert '{"provider_url": "http://unittest_institution_link.org", "title": "Unittest title", "url": "http://iiifhawk.klokantech.com/test_id/1/full/50,/0/native.jpg", "author_name": "Unittest creator", "height": "50", "width": "50", "version": "1.0", "author_url": "http://unittest_source.org", "provider_name": "Unittest institution", "type": "photo"}' in rv.data

	def test_oEmbed10(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1&maxheight=50')
		assert rv.status_code == 200
		assert '{"provider_url": "http://unittest_institution_link.org", "title": "Unittest title", "url": "http://iiifhawk.klokantech.com/test_id/1/full/,50/0/native.jpg", "author_name": "Unittest creator", "height": "50", "width": "50", "version": "1.0", "author_url": "http://unittest_source.org", "provider_name": "Unittest institution", "type": "photo"}' in rv.data

	def test_oEmbed11(self):
		rv = self.app.get('/oembed?url=http%3A//127.0.0.1%3A5000/test_id/1&maxheight=25&maxwidth=50')
		assert rv.status_code == 200
		assert '{"provider_url": "http://unittest_institution_link.org", "title": "Unittest title", "url": "http://iiifhawk.klokantech.com/test_id/1/full/!50,25/0/native.jpg", "author_name": "Unittest creator", "height": "25", "width": "25", "version": "1.0", "author_url": "http://unittest_source.org", "provider_name": "Unittest institution", "type": "photo"}' in rv.data

	def test_ingest0(self):
		rv = self.app.get('/ingest')
		assert rv.status_code == 404

	def test_ingest1(self):
		rv = self.app.get('/ingest?batch_id=1')
		assert rv.status_code == 404

#	def test_ingest2(self):
#		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id",
#  "url": ["http://unittest_url.org", "http://unittest_url2.org"],
#  "title": "Unittest title",
#  "creator": "Unittest creator",
#  "source": "http://unittest_source.org",
#  "institution": "Unittest institution",
#  "institution_link": "http://unittest_institution_link.org",
#  "license": "http://unittest_license_link.org",
#  "description": "Unittest description"}]))
#  		print rv.data
#		assert rv.status_code == 200
#		assert '{"batch_id": 1}' in rv.data

#	def test_ingest3(self):
#		rv = self.app.get('/ingest?batch_id=1')
#		assert rv.status_code == 200
#		assert '[{"status": "pending", "id": "test_id", "urls": ["ok", "ok"]}]' in rv.data

	def test_ingest4(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "@test_id"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 must have valid ID", "The item num. 0 doesn't have url field, or it isn't a list or a list is empty"]}''' in rv.data

	def test_ingest5(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id@"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 must have valid ID", "The item num. 0 doesn't have url field, or it isn't a list or a list is empty"]}''' in rv.data

	def test_ingest6(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "/test_id"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 must have valid ID", "The item num. 0 doesn't have url field, or it isn't a list or a list is empty"]}''' in rv.data

	def test_ingest7(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "\\test_id"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 must have valid ID", "The item num. 0 doesn't have url field, or it isn't a list or a list is empty"]}''' in rv.data

	def test_ingest8(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 doesn't have url field, or it isn't a list or a list is empty"]}''' in rv.data

	def test_ingest9(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": "test"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 doesn't have url field, or it isn't a list or a list is empty"]}''' in rv.data

	def test_ingest10(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": []}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 doesn't have url field, or it isn't a list or a list is empty"]}''' in rv.data

	def test_ingest11(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": ["test"]}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The 'test' url in the item num. 0 isn't valid url"]}''' in rv.data

	def test_ingest12(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": ["http://unittest_url.org"], "wrong_field": "test"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 has a not allowed field 'wrong_field'"]}''' in rv.data

	def test_ingest13(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": ["http://unittest_url.org"], "source": "test"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 doesn't have valid url 'test' in the Source field"]}''' in rv.data

	def test_ingest14(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": ["http://unittest_url.org"], "source": "http://unittest_source.org", "institution_link": "test"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 doesn't have valid url 'test' in the InstitutionLink field"]}''' in rv.data

	def test_ingest15(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": ["http://unittest_url.org"], "source": "http://unittest_source.org", "institution_link": "http://unittest_institution_link.org", "license": "test"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 doesn't have valid url 'test' in the License field"]}''' in rv.data

	def test_ingest16(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": ["http://unittest_url.org"], "status": "http://unittest_source.org"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 has status, but it isn't set to 'deleted' or there are more fields"]}''' in rv.data

	def test_ingest17(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "url": ["http://unittest_url.org"], "status": "deleted"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 has status, but it isn't set to 'deleted' or there are more fields"]}''' in rv.data

	def test_ingest18(self):
		rv = self.app.post('/ingest', headers={'Content-Type': 'application/json'}, data=json.dumps([{"id": "test_id", "status": "http://unittest_source.org"}]))
		assert rv.status_code == 404
		assert '''{"errors": ["The item num. 0 has status, but it isn't set to 'deleted' or there are more fields"]}''' in rv.data

if __name__ == '__main__':
	unittest.main()
