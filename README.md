feedjack-wordpress-export
--------------------

Django app to export RSS/Atom feeds processed by Feedjack to WordPress.

**IMPORTANT:** Does not work with the original Feedjack from
http://www.feedjack.org, only with [this
fork](https://github.com/mk-fg/feedjack) (and derivatives).


Installation
--------------------

It's a regular package for Python 2.7 (not 3.X), but not in pypi, so can be
installed from a git checkout with something like that:

	% git clone --depth=1 https://github.com/mk-fg/feedjack-wordpress-export
	% cd feedjack-wordpress-export
	% python setup.py install

Better way would be to use [pip](http://pip-installer.org/) to install all the
necessary dependencies as well:

	% pip install 'git+https://github.com/mk-fg/feedjack-wordpress-export.git#egg=feedjack-wordpress-export'

Note that to install stuff in system-wide PATH and site-packages, elevated
privileges are often required.
Use "install --user",
[~/.pydistutils.cfg](http://docs.python.org/install/index.html#distutils-configuration-files)
or [virtualenv](http://pypi.python.org/pypi/virtualenv) to do unprivileged
installs into custom paths.


### Requirements

* [Python 2.7 (not 3.X)](http://python.org/)

* [Django](http://djangoproject.com)
* [django-celery](http://celeryproject.org)

* (optional) [PyYAML](http://pyyaml.org/wiki/PyYAML) - to export stuff in a sane
	human-editable format from management commands

* (optional, recommended) [South](http://south.aeracode.org) - for automated
	database schema updates


### Deployment / configuration

As a django app, feedjack-wordpress-export should deployed as a part of "django
project", which is - at it's minimum - just a few [configuration
files](https://docs.djangoproject.com/en/dev/topics/settings/), specifying which
database to use, and which apps should handle which URLs.

This app only works in combination with [Feedjack](https://github.com/mk-fg/feedjack),
so it'd make sense to install and configure that one first.


##### TL;DR

	cd myproject

	# Update settings.py (at least db should be pre-configured there)
	echo -e >>myproject/settings.py \
		'from feedjack_wp_export.settings_base import update_settings' \
		'\nupdate_settings(__name__)'

	# Create database schema
	./manage.py syncdb --noinput

	 # Only if South is installed
	./manage.py migrate feedjack_wp_export --noinput


##### settings.py

For convenience, you can add these two lines to the end of your settings.py:

	from feedjack_wp_export.settings_base import update_settings
	update_settings(__name__)

These should do all the things listed below in fairly safe way for any common
setup. If that won't work for some reason, read on.

"feedjack_wp_export" and "djcelery" (django-celery, see [it's own setup
instructions](http://docs.celeryproject.org/en/latest/django/index.html)) should
be added to INSTALLED_APPS and CELERY_IMPORTS should include
"feedjack_wp_export.models".

Django-Celery also might need BROKER_URL option set to something like
"amqp://user:password@host:port//" (it can also use db as a queue backend, see
it's own docs), and these lines in settings.py:

	import djcelery
	djcelery.setup_loader()

Also it'd make sense to add "south" to INSTALLED_APPS as well and use "migrate"
along with syncdb to allow db migrations.


##### Celery

There's a lot of tunables in [Celery](http://docs.celeryproject.org/), which you
might want to tweak (like [error
reporting](http://docs.celeryproject.org/en/latest/configuration.html#error-e-mails),
for example).

At the bare minimum, [set the
BROKER_URL](http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html#celerytut-broker)
according to whichever queue backend is available.


##### Django admin site

The only way to configure exports (aside from the code) at the moment, so should
probably be enabled.  Consult [Django
docs](https://docs.djangoproject.com/en/dev/ref/contrib/admin/) on how to do it
properly, but the gist is just adding "django.contrib.admin" to INSTALLED_APPS
and "admin.autodiscover()" with "url(r'^admin/', include(admin.site.urls))" to
urls.py.


##### Database

If South is not installed or enabled, necessary db schema can be created with
`./manage.py syncdb`, otherwise also run `./manage.py migrate` afterwards, and
after every feedjack-wordpress-export update (to apply db schema and data
migrations).



Usage
--------------------

* Add Export and ExportSubscriber objects in Django Admin Interface.
* [Start celery workers](http://docs.celeryproject.org/en/latest/userguide/workers.html).
* Fetch feeds as usual with Feedjack (`./manage.py feedjack_update`).

Every fetched Post on Feed which has ExportSubscriber attached to it will be
queued for processing and export to a wordpress site, specified by related
Export object.
Such export is asynchronous (and maybe delayed) and should not slow or otherwise
affect feedjack itself, regardless of it's performance.


### Helper commands

App adds some management commands for convenience.

Use these like any other django commands throught django-admin.py or manage.py
script in the django project root, like this:

	./manage.py wp_getTaxonomies http://localhost/wordpress/xmlrpc.php -u admin:waka_waka -t category

Get more info on each command and instructions on how to use it through -h or --help options:

	./manage.py -h # will list all available commands under "[feedjack_wp_export]"
	./manage.py wp_getTaxonomies -h


### Post processors

Whole point of the project is to create a processing pipelines for feeds, so
each ExportSubscriber allows attaching an arbitrary handler functions to each
passed Post object.

Functions can be imported from specified entry points
("feedjack_wp_export.post_processors") or modules.

Each such function should look like this:

	def proc_func(post, post_data, wp_api):
		# do_stuff to change post_data, passed to wordpress api
		return post_data

For more real-world example, see [included entry point
module](https://github.com/mk-fg/feedjack-wordpress-export/blob/master/feedjack_wp_export/entry_point_examples.py).

Note that passed wp_api object can be queried like `wp_file =
wp_api.uploadFile(dict(name=..., ...))` and represents [WordPress XML-RPC
API](https://codex.wordpress.org/XML-RPC_WordPress_API) with authentication and
blog_id parameters already specified.
