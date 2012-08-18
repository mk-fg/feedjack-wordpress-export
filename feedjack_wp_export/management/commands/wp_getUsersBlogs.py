# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools as it, operator as op, functools as ft
from datetime import datetime
from optparse import make_option
from time import time
import getpass

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import get_default_timezone

from xmlrpclib import ServerProxy, Error as XMLRPCError
from pprint import pformat


class Command(BaseCommand):
	default_url = 'http://localhost/xmlrpc.php'

	args = '[ XML-RPC URL (default: {}) ]'.format(default_url)
	help = 'Get list of blogs on a wordpress installation.'
	option_list = BaseCommand.option_list + (
		make_option('-u', '--username',
			help='Username (password will'
				' be prompted interactively) or username:password for authentication.'),
		make_option('-f', '--auth-file',
			help='Path to file with username (or'
				' username:password) to use on the first line.'),
		make_option('--noinput', action='store_true',
			help='Tells Django to NOT prompt the user for input of any kind.'),
	)

	def handle(self, url=None, **optz):
		if url is None:
			url = self.default_url
			if int(optz['verbosity']) >= 1: self.stdout.write('Using default URL: {}\n'.format(url))
		server = ServerProxy(url, use_datetime=True)

		user = password = None
		if not optz['username'] and not optz['auth_file']:
			if not optz['noinput']:
				user = getpass.getuser()
				user = raw_input('Username{}: '.format(
					' (leave blank to use {!r})'.format(user) if user else '' ))
			if not user:
				raise CommandError( 'Either --username'
					' or --auth-file option must be specified.' )
		elif optz['username']: user = optz['username']
		elif optz['auth_file']:
			with open(optz['auth_file']) as src:
				user = src.readline().rstrip('\r\n')
		if ':' in user: user, password = user.split(':', 1)
		if not password:
			if optz['noinput']:
				raise CommandError('No password specified for a given username ({}).'.format(user))
			password = getpass.getpass(prompt='Password: ')
			if not password: raise CommandError('Aborted.')

		self.stdout.write('Blog data:\n{}\n'.format(
			pformat(server.wp.getUsersBlogs(user, password)) ))
