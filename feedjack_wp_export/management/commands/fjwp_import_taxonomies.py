# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools as it, operator as op, functools as ft
import sys

from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from . import BaseCommand, CommandError, load, make_option
from ...models import TaxonomyTerm


class Command(BaseCommand):

	args = '[ DUMP_PATH ]'
	help = 'Import new taxonomy terms from stdin or a file.\n'\
		'Source data dump should contain a sequence of mappings containing'\
			' wordpress taxonomy term attribute values (only "taxonomy" "name" and'\
			' "term_id" are used, see also --ignore-id).\n'\
		'Data format is JSON or YAML (if PyYAML is available).'
	option_list = BaseCommand.option_list + (
		make_option('-t', '--taxonomy',
			help='Use this taxonomy name for all imported terms (example: category).'),
		make_option('-i', '--ignore-id', action='store_true',
			help='Ignore "term_id" attributes for imported terms.'),
		make_option('-o', '--update-existing', action='store_true',
			help='Update term_id for existing (same taxonomy/name or taxonomy/id) terms.'),
	)

	@transaction.commit_on_success
	def handle(self, dump=None, **optz):
		dump = open(dump) if dump and dump != '-' else sys.stdin
		terms = load(dump)
		attrs = ['name', 'taxonomy']
		if not optz.get('ignore_id'): attrs.append('term_id')

		for term_import in terms:
			term = dict(
				( k, term_import[k].decode('utf-8')
					if isinstance(term_import[k], bytes) else term_import[k] )
				for k in attrs if k in term_import )
			try: term['term_name'] = term.pop('name')
			except KeyError: pass
			if optz.get('taxonomy'): term['taxonomy'] = optz['taxonomy']
			if 'term_id' in term: term['term_id'] = int(term['term_id'])

			term_model = TaxonomyTerm(**term)
			if int(optz['verbosity']) > 2:
				self.stdout.write(u'Importing term: {}\n'.format(term_model))

			try: term_model.save()
			except IntegrityError as err:
				if int(optz['verbosity']) > 2: self.stdout.write(u'Import error: {}\n'.format(err))
				if not optz['update_existing']:
					if int(optz['verbosity']) > 1:
						self.stdout.write(u'Skipping existing term: {}.\n'.format(term_model))
					continue
				# Delete conflicting terms
				for k in 'term_name', 'term_id':
					if k in term:
						TaxonomyTerm.objects.filter(
							taxonomy=term_model.taxonomy, **{k: term[k]} ).delete()
				# Retry
				term_model.save()
