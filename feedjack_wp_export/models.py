#-*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.db.models import signals
from django.db import models
from django.conf import settings

from feedjack.models import Site, Feed, Post

import itertools as it, operator as op, functools as ft
from xmlrpclib import ServerProxy, Error as XMLRPCError

import logging
log = logging.getLogger(__name__)


# See wp_newPost in wp-includes/class-wp-xmlrpc-server.php for details on these.

default_post_parameters = dict(
	post_type = 'post', # 'page', 'attachment', 'revision', 'nav_menu_item', ...
	post_status = 'publish', # 'draft', 'private', 'pending'
	comment_status = 'open', # 'closed'
	ping_status = 'open', # 'closed'
)
# post_title = None,
# post_content = None,
# post_date = None, # datetime, can also be submitted as post_date_gmt
# post_password = '',
# post_author = None, # int, can only be provided by configuration, probably
# post_excerpt = '',
# post_format = '', # 'aside', 'link', 'gallery', 'status', 'quote', 'image'
# sticky = False,
# post_thumbnail = 0,
# post_parent = 0,
# custom_fields = dict(), # { str: str }, can also be an ordered sequence of 2-element tuples
# terms = dict(), # { taxonomy_name: list of term ids }
# terms_names = dict(), # { taxonomy_name: list of term names }
# enclosure = None, # dict(url=str, length=int, type=str)
# # + any other fields supported by wp_insert_post,
# #  see https://codex.wordpress.org/Function_Reference/wp_insert_post

# TODO: per-export defaults
default_post_parameters.update(getattr( settings,
	'FEEDJACK_WP_EXPORT_POST_DEFAULTS', dict() ))


class Export(models.Model):
	url = models.CharField( max_length=2047,
		help_text='URL of an XML-RPC interface, usually'
				' something like https://mywordpress.com/xmlrpc.php' )
	blog_id = models.PositiveIntegerField(
		help_text='ID of a wordpress blog to import posts to.'
			' Use django wp_getUsersBlogs management command'
				' ("./manage.py wp_getUsersBlogs --help" for more info)'
				' to get a list of these (along with blog-specific XML-RPC URLs).' )
	username = models.CharField(max_length=63)
	password = models.CharField(max_length=63)

	class Meta:
		ordering = 'url', 'blog_id', 'username'
		unique_together = (('url', 'blog_id'),)

	def __unicode__(self):
		return '{0.url} (user: {0.username}, blog_id: {0.blog_id})'.format(self)

	def send(self, posts):
		# TODO: export through AtomPub as well
		# TODO: per-post error handling to prevent exporting the same posts
		server = ServerProxy(self.url, use_datetime=True)
		for post in posts:
			log.debug('Exporting post {!r} to {!r}'.format(post, self))
			post_data = default_post_parameters.copy()
			post_data.update(
				post_title=post.title,
				post_content=post.content,
				post_date=post.date_modified )
			result = server.wp.newPost(self.blog_id, self.username, self.password, post_data)
			log.debug('Exporting post {!r} to {!r}'.format(post, self))


class ExportSubscriber(models.Model):
	export = models.ForeignKey('Export', related_name='subscriber_set')
	feed = models.ForeignKey(
		'feedjack.Feed', related_name='exports' )
	is_active = models.BooleanField( 'is active', default=True,
		help_text='If disabled, this subscriber will not appear in the site or in the site\'s feed.' )

	class Meta:
		ordering = 'export', 'is_active', 'feed'
		unique_together = (('export', 'feed'),)

	def __unicode__(self):
		return '{0.feed} to {0.export}{1}'.format(
			self, ' (INACTIVE)' if not self.is_active else '' )


dirty_posts = set()

def post_update_handler(sender, instance, created=False, **kwz):
	# TODO: processing of modified posts
	if created:
		log.debug('Detected new post to export: {!r}'.format(instance))
		dirty_posts.add(instance)

def feed_update_handler(sender, instance, **kwz):
	exports = Export.objects.filter(subscriber_set__feed=instance)
	if not exports: return
	posts = list(instance.posts.filter(id__in=set(it.imap(op.attrgetter('id'), dirty_posts))))
	if not posts: return
	# TODO: some queue (celery?) here to handle transient export errors
	for n, exporter in enumerate(exports, 1):
		log.debug('Exporting {} posts to {!r} ({}/{})'.format(len(posts), exporter, n, len(exports)))
		exporter.send(posts)
	dirty_posts.difference_update(posts)
	log.debug('{} unexported posts left'.format(len(dirty_posts)))

def connect_to_signals():
	signals.post_save.connect(post_update_handler, sender=Post)
	Feed.signal_updated.connect(feed_update_handler)
	log.debug('Connected exports to feedjack signals')

connect_to_signals()
