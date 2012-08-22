#-*- coding: utf-8 -*-

import itertools as it, operator as op, functools as ft
from xmlrpclib import ServerProxy, Error as XMLRPCError

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import signals
from django.db import models
from django.conf import settings

from feedjack.models import Site, Feed, Post
from celery import Task, task

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
		unique_together = ('url', 'blog_id'),

	def __unicode__(self):
		return u'{0.url} (user: {0.username}, blog_id: {0.blog_id})'.format(self)


class TaxonomyTerm(models.Model):
	taxonomy = models.CharField(max_length=63)
	term_name = models.CharField(max_length=254, blank=True,
		help_text='Name of taxonomy term.'
			' term_id is preferred over this name, if available.'
			' Either term_name, term_id or both of these must be set.' )
	term_id = models.PositiveIntegerField( blank=True, null=True,
		help_text='Wordpress ID for this taxonomy term.'
			' Preferred over term_name, if available.' )

	class Meta:
		ordering = 'taxonomy', 'term_name', 'term_id'
		unique_together = ('taxonomy', 'term_name'), ('taxonomy', 'term_id')

	def __unicode__(self):
		dump = u'{}: '.format(self.taxonomy) + (self.term_name or u'')
		if self.term_id: dump += (u' (id: {})' if dump else u'id={}').format(self.term_id)
		return dump

	def save(self, *argz, **kwz):
		if not self.term_name and not self.term_id:
			raise ValidationError( 'Either term_name or'
				' term_id should be non-empty for TaxonomyTerm' )
		super(TaxonomyTerm, self).save(*argz, **kwz)


class ExportSubscriber(models.Model):
	export = models.ForeignKey('Export', related_name='subscriber_set')
	feed = models.ForeignKey(
		'feedjack.Feed', related_name='exports' )

	is_active = models.BooleanField( 'is active', default=True,
		help_text='If disabled, this subscriber will not appear in the site or in the site\'s feed.' )

	taxonomies = models.ManyToManyField( TaxonomyTerm,
		null=True, blank=True, help_text='Taxonomy terms to add to each imported Post.' )

	class Meta:
		ordering = 'export', '-is_active', 'feed'

	def __unicode__(self):
		return u'{0.feed} to {0.export}{1}'.format(
			self, u' (INACTIVE)' if not self.is_active else u'' )

	def send(self, post, wp_link=None):
		# TODO: export through AtomPub as well
		if wp_link is None: wp_link = ServerProxy(self.export.url, use_datetime=True)
		log.debug('Exporting post {!r} to {!r}'.format(post, self))
		post_data = default_post_parameters.copy()
		post_data.update(
			post_title=post.title,
			post_content=post.content,
			post_date=post.date_modified )
		if self.taxonomies.count():
			for term in self.taxonomies.all():
				if term.term_id: # use term_id, if possible
					post_data.setdefault('terms', dict())\
						.setdefault(term.taxonomy, list()).append(term.term_id)
				elif term.term_name:
					post_data.setdefault('terms_names', dict())\
						.setdefault(term.taxonomy, list()).append(term.term_name)
				else:
					log.warn( 'Linked (subscriber: {}) taxonomy term does not have'
						' neither term_name nor term_id set (id: {}, term: {})'.format(self, term.id, term) )
		return wp_link.wp.newPost( self.export.blog_id,
			self.export.username, self.export.password, post_data )


class ExportTask(Task):
	'Task to push the post to a wordpress instance, defined by export_id.'

	_wp_links = dict()
	def rpc_link(self, url):
		if url not in self._wp_links:
			self._wp_links[url] = ServerProxy(url, use_datetime=True)
		return self._wp_links[url]

	def run(self, subscriber_id, post_id):
		# Re-fetch objects here to make sure the most up-to-date version is used
		try:
			post = Post.objects.get(id=post_id)
			subscriber = ExportSubscriber.objects.get(id=subscriber_id)
		except ObjectDoesNotExist as err:
			log.warn( 'Received export task for'
				' non-existing object id(s): subscriber={}, post={}'.format(subscriber_id, post_id) )
			return
		try: subscriber.send(post, wp_link=self.rpc_link(subscriber.export.url))
		except XMLRPCError as err:
			log.debug('Failed to export post: {!r}'.format(post))
			raise self.retry(exc=err)
		log.debug('Post {!r} was successfully exported.'.format(post))

export_post = task(ignore_result=True)(ExportTask)


dirty_posts = set()

def post_update_handler(sender, instance, created=False, **kwz):
	# TODO: processing of modified posts
	if created:
		log.debug('Detected new post to export: {!r}'.format(instance))
		dirty_posts.add(instance)

def feed_update_handler(sender, instance, **kwz):
	subscribers = ExportSubscriber.objects.filter(feed=instance, is_active=True)
	if not subscribers: return
	posts = list(instance.posts.filter(id__in=set(it.imap(op.attrgetter('id'), dirty_posts))))
	if not posts: return
	for n, subscriber in enumerate(subscribers, 1):
		log.debug( 'Exporting {} posts to {!r} ({}/{})'\
			.format(len(posts), subscriber, n, len(subscribers)) )
		for post in posts: export_post.delay(subscriber.id, post.id)
	dirty_posts.difference_update(posts)
	log.debug('{} unexported posts left'.format(len(dirty_posts)))

def connect_to_signals():
	signals.post_save.connect(post_update_handler, sender=Post)
	Feed.signal_updated.connect(feed_update_handler)
	log.debug('Connected exports to feedjack signals')

connect_to_signals()
