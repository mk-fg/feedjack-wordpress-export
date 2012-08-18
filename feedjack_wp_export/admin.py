#-*- coding: utf-8 -*-

from django.contrib import admin

from . import models

class ExportAdmin(admin.ModelAdmin):
	list_display = 'url', 'blog_id', 'username'
admin.site.register(models.Export, ExportAdmin)

class ExportSubscriberAdmin(admin.ModelAdmin):
	list_display = 'export', 'feed', 'is_active'
admin.site.register(models.ExportSubscriber, ExportSubscriberAdmin)
