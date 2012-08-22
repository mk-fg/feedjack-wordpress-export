#-*- coding: utf-8 -*-

import itertools as it, operator as op, functools as ft
from xmlrpclib import ServerProxy,\
	Binary as RPCBinary, Error as RPCError

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.importlib import import_module
from django.utils.functional import lazy, SimpleLazyObject
from django.db.models import signals
from django.db import models
from django.conf import settings

from feedjack.models import Site, Feed, Post
from celery import Task, task, chain

from . import entry_point_processors

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


def hook_function(name):
	mod, func = name.rsplit('.', 1)
	err_ep = None
	try:
		import pkg_resources
		for ep in pkg_resources.iter_entry_points(entry_point_processors):
			if ep.name == mod: return getattr(ep.load(), func)
	except ImportError as err_ep: pass # entry_point functionality is optional
	try:
		mod = import_module(mod)
		return getattr(mod, func)
	except (ImportError, AttributeError) as err:
		raise ImportError( 'Failed to import function {!r} from entry_point/module'
			' {!r} (error(s): {})'.format(func, mod, ', '.join(bytes(e) for e in [err_ep, err] if e)) )


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
	processors = models.TextField( blank=True,
		help_text=(
			'Functions to process each exported Post with, separated by spaces or newlines.'
			' Each one will be passed (lazy) Post object and dict of data to export'
				' to wordpress API as args and "wp_api" keyword arg (in case API access is needed).'
			' It must return a post_data dict to pass to the'
				' next processor (in the same order as they are specified).'
			' post_data returned from the last processor will be exported.'
			' Functions should be specified either as a name of an entry_point'
			' ({}) function in a "{{ep.name}}.{{func_name}}" format (example:'
			' myhandlers.fetch_enclosures), or as a "{{module}}.{{func_name}}"'
			' (if named entry point cannot be found, example: mymodule.feeds.process_post).' )\
			.format(entry_point_processors) )

	class Meta:
		ordering = 'export', '-is_active', 'feed'

	def __unicode__(self):
		return u'{0.feed} to {0.export}{1}'.format(
			self, u' (INACTIVE)' if not self.is_active else u'' )


	def send(self, post, wp_api=None):
		'Prepare and export either Post object or dict of wordpress-api data.'
		if isinstance(post, Post): return self.export_post(post, wp_api=wp_api)
		elif isinstance(post, dict): return self.export_data(post, wp_api=wp_api)
		else:
			raise ValidationError( 'Unknown type'
				' of post to export ({!r}): {!r}'.format(post, type(post)) )

	def export_post(self, post, wp_api=None):
		log.debug('Exporting post {!r} to {!r}'.format(post, self))

		# Initial post_data, passed either to processors or exported as-is
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

		processors = self.processors.strip()
		if processors:
			# Setup processing chain
			processors = processors.split()
			processors = [process_post.s(post_data, processors[0], self.id, post.id)]\
				+ list(
					process_post.s(func=proc, subscriber_id=self.id, post_id=post.id)
					for proc in processors[1:] )\
				+ [export_post.s(subscriber_id=self.id)]
			return chain(*processors).delay()
		else:
			# Export post_data right here, if no further processing is needed
			return self.export_data(post_data, wp_api=wp_api)

	def export_data(self, post_data, wp_api=None):
		assert all(k in post_data for k in ['post_title', 'post_content', 'post_date'])
		# TODO: export through AtomPub as well
		if wp_api is None: wp_api = WPAPIProxy.from_export_object(self.export)
		return wp_api.newPost(post_data)


class WPAPIProxy(object):
	'Proxy object to encapsulate url/user/password for authenticated calls.'

	def __init__(self, api, blog_id, username, password):
		self.direct_api, self.blog_id = api, blog_id
		self.username, self.password = username, password
	def __getattr__(self, k):
		return ft.partial( getattr(self.direct_api.wp, k),
			self.blog_id, self.username, self.password )

	@classmethod
	def from_export_object(cls, export):
		return cls(
			ServerProxy(export.url, use_datetime=True),
			export.blog_id, export.username, export.password )


class PersistentRPCTask(Task):
	abstract = True
	_wp_links = dict() # class-wide cache

	def rpc_link(self, url):
		if url not in self._wp_links:
			self._wp_links[url] = ServerProxy(url, use_datetime=True)
		return self._wp_links[url]

	def api_proxy(self, export):
		# API proxies shouldn't be cached per-export-id, because auth may change
		argz = op.attrgetter('url', 'blog_id', 'username', 'password')(export)
		if argz not in self._wp_links:
			api = self.rpc_link(argz[0])
			self._wp_links[argz] = WPAPIProxy(api, *argz[1:])
		return self._wp_links[argz]

	def api_proxy_lazy(self, subscriber_id):
		assert isinstance(subscriber_id, int)
		# Mainly for processors, which most likely won't use it at all,
		#  so there's just no point in making db queries for each one
		return SimpleLazyObject(lambda: self.api_proxy(
			ExportSubscriber.objects.get(id=subscriber_id).export ))


class ProcessorTask(PersistentRPCTask):
	'Process post_data through a given function.'

	def run(self, post_data, func, subscriber_id, post_id):
		log.debug('Running post processor hook {!r} (post_id: {})'.format(func, post_id))
		return hook_function(func)(
			SimpleLazyObject(lambda: Post.objects.get(id=post_id)),
			post_data, wp_api=self.api_proxy_lazy(subscriber_id) )

process_post = task()(ProcessorTask)


class ExportTask(PersistentRPCTask):
	'Push Post to a wordpress instance, defined by export_id.'

	def run(self, post, subscriber_id):
		assert isinstance(subscriber_id, int)
		assert isinstance(post, (int, dict)) # either post_id or post_data dict
		# Re-fetch objects here to make sure the most up-to-date version is used
		try:
			subscriber = ExportSubscriber.objects.get(id=subscriber_id)
			if isinstance(post, int): post = Post.objects.get(id=post)
		except ObjectDoesNotExist as err:
			log.warn( 'Received export task for'
				' non-existing object id(s): subscriber={}, post={}'.format(subscriber_id, post) )
			return
		try: subscriber.send(post, wp_api=self.api_proxy(subscriber.export))
		except RPCError as err:
			log.debug('Failed to export post: {!r}'.format(post))
			raise self.retry(exc=err)

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
		for post in posts: export_post.delay(post=post.id, subscriber_id=subscriber.id)
	dirty_posts.difference_update(posts)
	log.debug('{} unexported posts left'.format(len(dirty_posts)))

def connect_to_signals():
	signals.post_save.connect(post_update_handler, sender=Post)
	Feed.signal_updated.connect(feed_update_handler)
	log.debug('Connected exports to feedjack signals')

connect_to_signals()
