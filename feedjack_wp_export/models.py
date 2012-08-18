#-*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.db.models import signals
from django.db import models
from django.conf import settings

from feedjack.models import Site, Post

from xmlrpclib import ServerProxy, Error as XMLRPCError


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
	user = models.CharField(max_length=63)
	password = models.CharField(max_length=63)

	class Meta:
		ordering = 'url', 'blog_id', 'user'
		unique_together = (('url', 'blog_id'),)

	def __unicode__(self):
		return '{0.url} (user: {0.user}, blog_id: {0.blog_id})'.format(self)

	def send(self, posts):
		# TODO: export through AtomPub as well
		server = ServerProxy(self.url, use_datetime=True)
		for post in posts:
			post_data = default_post_parameters.copy()
			post_data.update(
				post_title=post.title,
				post_content=post.content,
				post_date=post.date_modified )
			server.wp.newPost(self.blog_id, self.username, self.password, post_data)


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

def post_update_handler(self, sender, instance, created, **kwz):
	if created: dirty_posts.add(instance) # TODO: processing of modified posts

def site_update_handler(self, site, **kwz):
	exports = Export.objects.filter(subscriber_set__feedjack_site=site)
	if not exports: return
	posts = list(Post.objects.filter(id__in=dirty_posts, feed__subscriber_set__site=site))
	if not posts: return
	# TODO: some queue (celery?) here to handle transient export errors
	for exporter in exports: exporter.send(posts)
	dirty_posts.difference_update(posts)

def connect_to_signals(self):
	signals.post_save.connect(post_update_handler, sender=Post)
	Site.signal_update.connect(site_update_handler)
