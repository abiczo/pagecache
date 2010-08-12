from setuptools import setup

setup(name='pagecache',
      description='Page caching WSGI middleware',
      long_description='Page caching WSGI middleware',
      author='Andras Biczo',
      author_email='abiczo@gmail.com',
      url='http://github.com/abiczo/pagecache',
      license='MIT',
      version='0.1',
      packages=['pagecache'],
      keywords='cache wsgi',
      zip_safe=False,
      install_requires=['webob'],
      test_suite='nose.collector',
      tests_require=['nose>=0.10.4', 'webtest', 'python-memcached'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ]
     )
