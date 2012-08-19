# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

from optparse import make_option
from xmlrpclib import ServerProxy, Error as XMLRPCError
from pprint import pformat
import getpass


class WPRPCCommand(BaseCommand):
	default_url = 'http://localhost/xmlrpc.php'

	args = '[ XML-RPC URL (default: {}) ]'.format(default_url)
	help = 'Call to Wordpress XML-RPC interface.'
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

	def parse_rpc_endpoint(self, url=None, **optz):
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

		return server, user, password

	def print_data(self, data, header=None):
		if header: self.stdout.write('{}:\n'.format(header))
		self.stdout.write('{}\n'.format(pformat(data)))
