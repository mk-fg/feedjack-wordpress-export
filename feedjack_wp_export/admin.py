#-*- coding: utf-8 -*-

from django.contrib import admin

from . import models


class ExportAdmin(admin.ModelAdmin):
	list_display = 'url', 'blog_id', 'username'
admin.site.register(models.Export, ExportAdmin)

class TaxonomyTermAdmin(admin.ModelAdmin):
	list_display = 'taxonomy', 'term_name', 'term_id'
admin.site.register(models.TaxonomyTerm, TaxonomyTermAdmin)

class ExportSubscriberAdmin(admin.ModelAdmin):
	list_display = 'export', 'feed', 'is_active', 'processors'
	filter_vertical = 'taxonomies',
admin.site.register(models.ExportSubscriber, ExportSubscriberAdmin)
