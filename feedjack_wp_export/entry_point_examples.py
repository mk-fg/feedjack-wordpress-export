#-*- coding: utf-8 -*-

import itertools as it, operator as op, functools as ft
import requests

from feedjack_wp_export.models import RPCBinary

import logging
log = logging.getLogger(__name__)


def fetch_thumbnail(post, post_data, wp_api):
	if post.enclosures:
		for link in post.enclosures:
			if link.get('type', '').startswith('image/') and 'href' in link: break
		else:
			log.warn( 'Failed to find appropriate image'
				' among {} enclosures (Post: {})'.format(len(post.enclosures), post) )
			link = None
		if len(post.enclosures) > 1:
			log.warn(( 'Post {} has {} media enclosures, selecting the'
				' first one (href: {})' ).format(post, len(post.enclosures), link.get('href')))
		if link:
			r = requests.get(link['href'])
			wp_file = wp_api.uploadFile(dict(
				name=link['href'].rsplit('/', 1)[-1],
				type=r.headers.get('content-type', link['type']).rsplit(';', 1)[0],
				bits=RPCBinary(r.content), overwrite=True ))
			post_data['post_thumbnail'] = wp_file['id']
			log.debug('Successfully uploaded enclosure to wp: {}'.format(wp_file))
	else: log.info('No enclosures for post: {}'.format(post))
	return post_data
