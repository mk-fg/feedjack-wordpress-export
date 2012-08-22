# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ExportSubscriber.processors'
        db.add_column('feedjack_wp_export_exportsubscriber', 'processors',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ExportSubscriber.processors'
        db.delete_column('feedjack_wp_export_exportsubscriber', 'processors')


    models = {
        'feedjack.feed': {
            'Meta': {'ordering': "('name', 'feed_url')", 'object_name': 'Feed'},
            'etag': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'}),
            'feed_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'feeds'", 'blank': 'True', 'to': "orm['feedjack.Filter']"}),
            'filters_logic': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'immutable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_checked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'skip_errors': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tagline': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'feedjack.filter': {
            'Meta': {'object_name': 'Filter'},
            'base': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'filters'", 'to': "orm['feedjack.FilterBase']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
        },
        'feedjack.filterbase': {
            'Meta': {'object_name': 'FilterBase'},
            'crossref': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'crossref_rebuild': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'crossref_span': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'crossref_timeline': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'handler_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        'feedjack_wp_export.export': {
            'Meta': {'ordering': "('url', 'blog_id', 'username')", 'unique_together': "(('url', 'blog_id'),)", 'object_name': 'Export'},
            'blog_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2047'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '63'})
        },
        'feedjack_wp_export.exportsubscriber': {
            'Meta': {'ordering': "('export', '-is_active', 'feed')", 'object_name': 'ExportSubscriber'},
            'export': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscriber_set'", 'to': "orm['feedjack_wp_export.Export']"}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exports'", 'to': "orm['feedjack.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'processors': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'taxonomies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['feedjack_wp_export.TaxonomyTerm']", 'null': 'True', 'blank': 'True'})
        },
        'feedjack_wp_export.taxonomyterm': {
            'Meta': {'ordering': "('taxonomy', 'term_name', 'term_id')", 'unique_together': "(('taxonomy', 'term_name'), ('taxonomy', 'term_id'))", 'object_name': 'TaxonomyTerm'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'taxonomy': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'term_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'term_name': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'})
        }
    }

    complete_apps = ['feedjack_wp_export']