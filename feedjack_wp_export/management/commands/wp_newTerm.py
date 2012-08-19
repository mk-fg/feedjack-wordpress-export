# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from . import WPRPCCommand, CommandError, load, XMLRPCFault

import itertools as it, operator as op, functools as ft
from optparse import make_option
import sys


class Command(WPRPCCommand):

	help = 'Import new taxonomy terms into a wordpress.\n'\
		'Source data dump should contain a sequence of mappings containing'\
			' wordpress taxonomy term attribute values (other keys will just be ignored,'\
			' also see --strip option) and be piped through stdin or read from specified'\
			' file (with --dump option).\n'\
		'Data format is JSON or YAML (if PyYAML is available).'
	option_list = WPRPCCommand.option_list + (
		make_option('-b', '--blog-id', type='int', default=1,
			help='ID of blog to query (default: %(default)s).'),
		make_option('-t', '--taxonomy',
			help='Use this taxonomy name for all imported terms (example: category).'),
		make_option('-s', '--strip', action='append', default=list(),
			help='Attribute name to strip from imported terms. Can be specified multiple times.'),
		make_option('-e', '--skip-errors', type=int, action='append', default=list(),
			help='Returned RPC fault codes to ignore'
				' (example: 500). Can be specified multiple times.'),
		make_option('-d', '--dump', help='Path to a data-dump file (default: use stdin).'),
	)

	def handle(self, url=None, **optz):
		server, user, password = self.parse_rpc_endpoint(url, **optz)
		dump = open(optz['dump']) if optz.get('dump') and optz['dump'] != '-' else sys.stdin
		terms = load(dump)

		for term_import in terms:
			term = dict( (k, term_import[k])
				for k in ['name', 'taxonomy', 'slug', 'description', 'parent']
				if k in term_import )
			if optz.get('taxonomy'): term['taxonomy'] = optz['taxonomy']
			if 'parent' in term: term['parent'] = int(term['parent'])
			for k in optz['strip']:
				if k in term: del term[k]
			if int(optz['verbosity']) > 2: self.stdout.write('Importing term: {}\n'.format(term))
			try: term_id = server.wp.newTerm(optz['blog_id'], user, password, term)
			except XMLRPCFault as err:
				if err.faultCode in optz['skip_errors']:
					if int(optz['verbosity']) > 1:
						self.stdout.write(( 'Failed importing term (name: {!r}): fault_code={!r},'
							' msg={!r}.\n' ).format(term.get('name'), err.faultCode, err.faultString))
				else: raise
			else:
				if int(optz['verbosity']) > 1:
					self.stdout.write(( 'Imported term:'
						' name={!r}, id={!r}.\n' ).format(term.get('name'), term_id))
