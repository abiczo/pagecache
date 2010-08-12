import unittest
from webtest import TestApp
import time
import threading
import Queue
import memcache

from pagecache import PageCacheMiddleware

MEMCACHED_SERVER = ['127.0.0.1:11211']

# simple WSGI application that counts how many times it was called
class CounterApp(object):
    def __init__(self, sleep=0):
        self.counter = 0
        self.sleep = sleep

    def __call__(self, environ, start_response):
        if self.sleep > 0:
            time.sleep(self.sleep)

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

    def test_serve_stale(self):
        app = CounterApp(sleep=1)
        counter_app = app

        memcached = memcache.Client(MEMCACHED_SERVER)
        cached_urls = [('/test_serve_stale', 2, 5)]
        app = PageCacheMiddleware(app, cached_urls, memcached)
        app = TestApp(app)

        def test_req(app, counter_app, name, sleep, url, q):
            time.sleep(sleep)
            app.get(url)
            q.put((name, counter_app.counter))


        # this is what should happen:
        #
        #                app
        # t=0.0  R1 ----> |
        # t=1.0  R1 <---- |            counter == 1
        # t=2.0           |
        # t=3.1  R2 ----> |
        # t=3.5           | <---- R3
        # t=3.5           | ----> R3   counter == 1 since stale content was served
        # t=4.0  R2 <---- |            counter == 2

        q = Queue.Queue()

        # app should calculate the response on the first request
        R1 = threading.Thread(target=test_req, args=(
            app, counter_app, 'R1', 0, '/test_serve_stale', q))

        # app should recalculate the response on the first request
        # in the grace period
        R2 = threading.Thread(target=test_req, args=(
            app, counter_app, 'R2', 3.1, '/test_serve_stale', q))

        # pagecache should serve stale data on the second request
        # in the grace period
        R3 = threading.Thread(target=test_req, args=(
            app, counter_app, 'R3', 3.5, '/test_serve_stale', q))

        reqs = [R1, R2, R3]

        for r in reqs:
            r.start()

        for r in reqs:
            r.join()

        qr = [q.get() for _ in reqs]

        assert qr == [('R1', 1), ('R3', 1), ('R2', 2)]
