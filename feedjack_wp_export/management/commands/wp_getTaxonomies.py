# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import WPRPCCommand

from optparse import make_option


class Command(WPRPCCommand):

	help = 'Get list of taxonomies or taxonomy terms for a blog.'
	option_list = WPRPCCommand.option_list + (
		make_option('-b', '--blog-id', type='int', default=1,
			help='ID of blog to query (default: %(default)s).'),
		make_option('-t', '--taxonomy',
			help='Get terms for the specified taxonomy name (example: category).'),
	)

	def handle(self, url=None, **optz):
		server, user, password = self.parse_rpc_endpoint(url, **optz)
		if not optz.get('taxonomy'):
			self.print_data(server.wp.getTaxonomies(
				optz['blog_id'], user, password ), header='Taxonomies')
		else:
			self.print_data(
				server.wp.getTerms(optz['blog_id'], user, password, optz['taxonomy']),
				header='Defined terms for taxonomy {!r}'.format(optz['taxonomy']) )
