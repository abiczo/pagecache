import time
import hashlib
import webob

class PageCacheMiddleware(object):
    def __init__(self, app, cached_urls, cache):
        self.app = app
        self.cached_urls = cached_urls
        self.cache = cache

    def __call__(self, environ, start_response):
        req = webob.Request(environ, charset='utf-8')

        # is this an url we should cache?
        cache_opts = None
        for url, ttl, grace in self.cached_urls:
            if req.path_qs.startswith(url):
                cache_opts = (url, ttl, grace)
                break

        if cache_opts:
            _, ttl, grace = cache_opts
            path_md5 = hashlib.md5(req.path_qs).hexdigest()
            data_key = 'pagecache:data:%s' % path_md5
            lock_key = 'pagecache:lock:%s' % path_md5

            update_lock = None
            cached = self.cache.get(data_key)
            if cached:
                expires = cached[0]
                curr_ts = time.time()

                # check whether TTL has expired
                if curr_ts > expires:
                    # we're in the grace period, content needs to be updated
                    update_lock = self.cache.add(lock_key, 'LOCK',
                                                 time=expires + grace)
                    if update_lock:
                        # acquired the update lock, recalculate content
                        cached = None
                    else:
                        # another process is already updating the content,
                        # serve stale data from the cache in the meantime
                        pass

            if cached:
                # serve response from the cache
                _, headers, body, status, content_type = cached
                resp = webob.Response(headers=headers,
                                      body=body,
                                      status=status,
                                      content_type=content_type)
            else:
                # NOTE: we don't delete any incoming cookies, it is the
                # application's responsibility to ignore any cookies when
                # calculating cacheable responses

                # recalculate response
                resp = req.get_response(self.app)

                # do not store any cookie information in the cached responses
                if 'Set-Cookie' in resp.headers:
                    del resp.headers['Set-Cookie']

                # store response in the cache
                expires = time.time() + ttl
                to_cache = [expires, resp.headers, resp.body, resp.status, resp.content_type]
                self.cache.set(data_key, to_cache, time=ttl + grace)

                # delete the update lock if needed
                if update_lock:
                    self.cache.delete(lock_key)

            return resp(environ, start_response)


        return self.app(environ, start_response)
