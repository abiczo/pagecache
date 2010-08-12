import unittest
from webtest import TestApp
import time
import memcache

from pagecache import PageCacheMiddleware

MEMCACHED_SERVER = ['127.0.0.1:11211']

# simple WSGI application that counts how many times it was called
class CounterApp(object):
    def __init__(self):
        self.counter = 0

    def __call__(self, environ, start_response):
        self.counter += 1
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return ['']

class TestPageCache(unittest.TestCase):
    def test_cache_works(self):
        app = CounterApp()
        counter_app = app

        memcached = memcache.Client(MEMCACHED_SERVER)
        cached_urls = [('/test_cache_works', 5, 10)]
        app = PageCacheMiddleware(app, cached_urls, memcached)
        app = TestApp(app)

        resp = app.get('/test_cache_works')
        assert counter_app.counter == 1

        resp = app.get('/test_cache_works')
        assert counter_app.counter == 1

    def test_doesnt_cache(self):
        app = CounterApp()
        counter_app = app

        memcached = memcache.Client(MEMCACHED_SERVER)
        cached_urls = [('/test_doesnt_cache', 5, 10)]
        app = PageCacheMiddleware(app, cached_urls, memcached)
        app = TestApp(app)

        resp = app.get('/not-cached')
        assert counter_app.counter == 1

        resp = app.get('/not-cached')
        assert counter_app.counter == 2

    def test_cache_expires(self):
        app = CounterApp()
        counter_app = app

        memcached = memcache.Client(MEMCACHED_SERVER)
        cached_urls = [('/test_cache_expires', 1, 0)]
        app = PageCacheMiddleware(app, cached_urls, memcached)
        app = TestApp(app)

        resp = app.get('/test_cache_expires')
        assert counter_app.counter == 1

        time.sleep(1.5)

        resp = app.get('/test_cache_expires')
        assert counter_app.counter == 2

    def test_cache_grace(self):
        app = CounterApp()
        counter_app = app

        memcached = memcache.Client(MEMCACHED_SERVER)
        cached_urls = [('/test_cache_grace', 1, 5)]
        app = PageCacheMiddleware(app, cached_urls, memcached)
        app = TestApp(app)

        resp = app.get('/test_cache_grace')
        assert counter_app.counter == 1

        time.sleep(1.5)

        resp = app.get('/test_cache_grace')
        assert counter_app.counter == 2
