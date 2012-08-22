#!/usr/bin/env python

from setuptools import setup, find_packages
import os

pkg_root = os.path.dirname(__file__)

# Error-handling here is to allow package to be built w/o README included
try: readme = open(os.path.join(pkg_root, 'README.txt')).read()
except IOError: readme = ''

setup(

	name = 'feedjack-wordpress-export',
	version = '12.08.0',
	author = 'Mike Kazantsev',
	author_email = 'mk.fraggod@gmail.com',
	license = 'WTFPL',
	keywords = ['feed', 'feedjack', 'wordpress', 'export',
		'rss', 'atom', 'xml-rpc', 'django', 'feedparser', 'celery', 'news'],
	url = 'https://github.com/mk-fg/feedjack-wordpress-export',

	description = 'Django app to export'\
		' RSS/Atom feeds processed by feedjack to wordpress',
	long_description = readme,

	classifiers = [
		'Development Status :: 4 - Beta',
		'Environment :: Console',
		'Environment :: Web Environment',
		'Framework :: Django',
		'Intended Audience :: Developers',
		'Intended Audience :: Information Technology',
		'License :: OSI Approved',
		'Operating System :: POSIX',
		'Operating System :: Unix',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 2 :: Only',
		'Topic :: Internet',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
		'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
		'Topic :: Software Development',
		'Topic :: Software Development :: Libraries :: Python Modules' ],

	install_requires = ['feedjack', 'Django >= 1.4', 'django-celery'],
	extras_require = {
		'db_migration': ['South'],
		'entry_points': ['setuptools'],
		'yaml': ['PyYAML'] },

	packages = find_packages(),
	package_data = {'': ['README.txt']},
	exclude_package_data = {'': ['README.*']} )
