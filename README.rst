=========
PageCache
=========

WSGI caching middleware.

PageCache is a WSGI middleware that can be used to cache complete responses
from WSGI applications. PageCache works well with memcached but can be used
with other caching backends as well.

PageCache has not been widely tested, use with caution.

Usage
=====

Here's a simple example to get you started::

    from pagecache import PageCacheMiddleware
    
    app = ...
    cache = memcache.Client(...)
    cached_urls = (('/foo', 30, 120), # url prefix, TTL, grace period
                   ('/bar', 3600, 60))
    app = PageCacheMiddleware(app, cached_urls, cache)

Cached urls
-----------

The list of urls to cache is given in the ``cached_urls`` list (or tuple).
Each entry of this list is a tuple in the following format:
``(<url prefix>, <TTL in seconds>, <grace period in seconds>)``

Pages are served from the cache in the TTL period. When the TTL period has
expired the grace period begins. The first request coming in in the grace
period will recalculate the page and store the new result in the cache.
While the new result is being calculated stale results are served from the
cache (until the grace period expires). This is to protect against the
`dog-pile effect <http://kovyrin.net/2008/03/10/dog-pile-effect-and-how-to-avoid-it-with-ruby-on-rails-memcache-client-patch/>`_

The cache object
----------------

PageCache was only tested with memcached, but it may work with other cache
backends as well. The only requirement is that the cache object should have
the following methods with reasonably similar semantics as in memcached:
``get``, ``set``, ``delete``, ``add``

A note on cookies
-----------------

All Set-Cookie headers returned by the application will be ignored.
Also, depending on your application you'll most probably want to make sure
that the application doesn't use any incoming cookie information to calculate
responses that will be cached.

Install
=======

You can install the latest version from the
`github repository <http://github.com/abiczo/pagecache>`_::

    git clone git://github.com/abiczo/pagecache.git
    cd pagecache
    python setup.py install

TODO
====

* more unit testing
* better syntax for the cached urls configuration
* regexp based url matching
* configurable cache keys (so that multiple applications can use the same
  memcached instance without having to worry about having the same cached urls)
* configurable request charset

Patches / pull-requests are welcome.

Contact
=======

abiczo@gmail.com
