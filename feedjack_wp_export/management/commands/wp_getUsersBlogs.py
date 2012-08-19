# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import WPRPCCommand


class Command(WPRPCCommand):

	help = 'Get list of blogs on a wordpress installation.'

	def handle(self, url=None, **optz):
		server, user, password = self.parse_rpc_endpoint(url, **optz)
		self.print_data(server.wp.getUsersBlogs(user, password), header='Blog data')
