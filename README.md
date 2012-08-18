feedjack-wordpress-export
--------------------

Django app to export RSS/Atom feeds processed by feedjack to wordpress.

**IMPORTANT:** Does not work with the original feedjack from http://www.feedjack.org, only with [this fork](https://github.com/mk-fg/feedjack) (and derivatives).



Installation
--------------------


### Requirements

* [Python 2.7 (not 3.X)](http://python.org/)

* [Django](http://djangoproject.com)
* [django-celery](http://celeryproject.org)
* (optional, recommended) [South](http://south.aeracode.org) - for automated
	database schema updates


### Deployment / configuration


##### settings.py

from feedjack_wp_export.settings_base import update_settings
update_settings(__name__)


##### Celery

BROKER_URL = 'amqp://user:password@host:port//'

CELERY_TASK_PUBLISH_RETRY

CELERY_TASK_PUBLISH_RETRY_POLICY

http://docs.celeryproject.org/en/latest/configuration.html#error-e-mails


##### Django Admin Interface

INSTALLED_APPS = (
	...
	'django.contrib.admin',
)

urlpatterns = patterns('',
	...
	url(r'^admin/', include(admin.site.urls)),
)


##### Database

	./manage.py syncdb
	./manage.py migrate



Usage
--------------------

* Add Export and ExportSubscriber objects in Django Admin Interface.
* [Start celery workers](http://docs.celeryproject.org/en/latest/userguide/workers.html).
* ./manage.py feedjack_update
