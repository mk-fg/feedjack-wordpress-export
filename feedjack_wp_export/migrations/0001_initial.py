# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Export'
        db.create_table('feedjack_wp_export_export', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=2047)),
            ('blog_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('user', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=63)),
        ))
        db.send_create_signal('feedjack_wp_export', ['Export'])

        # Adding unique constraint on 'Export', fields ['url', 'blog_id']
        db.create_unique('feedjack_wp_export_export', ['url', 'blog_id'])

        # Adding model 'ExportSubscriber'
        db.create_table('feedjack_wp_export_exportsubscriber', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('export', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'subscriber_set', to=orm['feedjack_wp_export.Export'])),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'exports', to=orm['feedjack.Feed'])),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('feedjack_wp_export', ['ExportSubscriber'])

        # Adding unique constraint on 'ExportSubscriber', fields ['export', 'feed']
        db.create_unique('feedjack_wp_export_exportsubscriber', ['export_id', 'feed_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'ExportSubscriber', fields ['export', 'feed']
        db.delete_unique('feedjack_wp_export_exportsubscriber', ['export_id', 'feed_id'])

        # Removing unique constraint on 'Export', fields ['url', 'blog_id']
        db.delete_unique('feedjack_wp_export_export', ['url', 'blog_id'])

        # Deleting model 'Export'
        db.delete_table('feedjack_wp_export_export')

        # Deleting model 'ExportSubscriber'
        db.delete_table('feedjack_wp_export_exportsubscriber')


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
            'Meta': {'ordering': "(u'url', u'blog_id', u'user')", 'unique_together': "((u'url', u'blog_id'),)", 'object_name': 'Export'},
            'blog_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2047'}),
            'user': ('django.db.models.fields.CharField', [], {'max_length': '63'})
        },
        'feedjack_wp_export.exportsubscriber': {
            'Meta': {'ordering': "(u'export', u'is_active', u'feed')", 'unique_together': "((u'export', u'feed'),)", 'object_name': 'ExportSubscriber'},
            'export': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'subscriber_set'", 'to': "orm['feedjack_wp_export.Export']"}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'exports'", 'to': "orm['feedjack.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['feedjack_wp_export']