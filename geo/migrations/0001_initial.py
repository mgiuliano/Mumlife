# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Postcode'
        db.create_table(u'geo_postcode', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('postcode', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('latitude', self.gf('django.db.models.fields.FloatField')()),
            ('longitude', self.gf('django.db.models.fields.FloatField')()),
            ('easting', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('northing', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('grid_ref', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('town_area', self.gf('django.db.models.fields.TextField')()),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('postcodes', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('active_postcodes', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'geo', ['Postcode'])


    def backwards(self, orm):
        # Deleting model 'Postcode'
        db.delete_table(u'geo_postcode')


    models = {
        u'geo.postcode': {
            'Meta': {'object_name': 'Postcode'},
            'active_postcodes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'easting': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'grid_ref': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {}),
            'northing': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'postcodes': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'town_area': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['geo']