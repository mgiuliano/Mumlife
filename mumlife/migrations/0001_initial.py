# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Geocode'
        db.create_table(u'mumlife_geocode', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=125)),
            ('latitude', self.gf('django.db.models.fields.FloatField')()),
            ('longitude', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'mumlife', ['Geocode'])

        # Adding model 'Member'
        db.create_table(u'mumlife_member', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='profile', unique=True, to=orm['auth.User'])),
            ('fullname', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('slug', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('postcode', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('gender', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('dob', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('picture', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('about', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('spouse', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='partner', null=True, to=orm['mumlife.Member'])),
            ('interests', self.gf('tagging.fields.TagField')()),
            ('units', self.gf('django.db.models.fields.IntegerField')(default=1, null=True, blank=True)),
            ('max_range', self.gf('django.db.models.fields.IntegerField')(default=10)),
        ))
        db.send_create_signal(u'mumlife', ['Member'])

        # Adding model 'Kid'
        db.create_table(u'mumlife_kid', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fullname', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('gender', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('dob', self.gf('django.db.models.fields.DateField')(null=True)),
            ('visibility', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal(u'mumlife', ['Kid'])

        # Adding M2M table for field parents on 'Kid'
        db.create_table(u'mumlife_kid_parents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('kid', models.ForeignKey(orm[u'mumlife.kid'], null=False)),
            ('member', models.ForeignKey(orm[u'mumlife.member'], null=False))
        ))
        db.create_unique(u'mumlife_kid_parents', ['kid_id', 'member_id'])

        # Adding model 'Friendships'
        db.create_table(u'mumlife_friendships', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_member', self.gf('django.db.models.fields.related.ForeignKey')(related_name='from_friend', to=orm['mumlife.Member'])),
            ('to_member', self.gf('django.db.models.fields.related.ForeignKey')(related_name='to_friend', to=orm['mumlife.Member'])),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'mumlife', ['Friendships'])

        # Adding model 'Message'
        db.create_table(u'mumlife_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mumlife.Member'])),
            ('area', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('location', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('eventdate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('eventenddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('visibility', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('occurrence', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('occurs_until', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('tags', self.gf('tagging.fields.TagField')()),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='sender', null=True, to=orm['mumlife.Member'])),
            ('is_reply', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('reply_to', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='author', null=True, to=orm['mumlife.Message'])),
        ))
        db.send_create_signal(u'mumlife', ['Message'])

        # Adding model 'Notifications'
        db.create_table(u'mumlife_notifications', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.OneToOneField')(related_name='notifications', unique=True, to=orm['mumlife.Member'])),
            ('total', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('messages', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('friends_requests', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'mumlife', ['Notifications'])

        # Adding M2M table for field events on 'Notifications'
        db.create_table(u'mumlife_notifications_events', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('notifications', models.ForeignKey(orm[u'mumlife.notifications'], null=False)),
            ('message', models.ForeignKey(orm[u'mumlife.message'], null=False))
        ))
        db.create_unique(u'mumlife_notifications_events', ['notifications_id', 'message_id'])

        # Adding M2M table for field threads on 'Notifications'
        db.create_table(u'mumlife_notifications_threads', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('notifications', models.ForeignKey(orm[u'mumlife.notifications'], null=False)),
            ('message', models.ForeignKey(orm[u'mumlife.message'], null=False))
        ))
        db.create_unique(u'mumlife_notifications_threads', ['notifications_id', 'message_id'])


    def backwards(self, orm):
        # Deleting model 'Geocode'
        db.delete_table(u'mumlife_geocode')

        # Deleting model 'Member'
        db.delete_table(u'mumlife_member')

        # Deleting model 'Kid'
        db.delete_table(u'mumlife_kid')

        # Removing M2M table for field parents on 'Kid'
        db.delete_table('mumlife_kid_parents')

        # Deleting model 'Friendships'
        db.delete_table(u'mumlife_friendships')

        # Deleting model 'Message'
        db.delete_table(u'mumlife_message')

        # Deleting model 'Notifications'
        db.delete_table(u'mumlife_notifications')

        # Removing M2M table for field events on 'Notifications'
        db.delete_table('mumlife_notifications_events')

        # Removing M2M table for field threads on 'Notifications'
        db.delete_table('mumlife_notifications_threads')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'mumlife.friendships': {
            'Meta': {'object_name': 'Friendships'},
            'from_member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_friend'", 'to': u"orm['mumlife.Member']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'to_member': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_friend'", 'to': u"orm['mumlife.Member']"})
        },
        u'mumlife.geocode': {
            'Meta': {'object_name': 'Geocode'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {}),
            'longitude': ('django.db.models.fields.FloatField', [], {})
        },
        u'mumlife.kid': {
            'Meta': {'object_name': 'Kid'},
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'gender': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mumlife.Member']", 'symmetrical': 'False'}),
            'visibility': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'mumlife.member': {
            'Meta': {'object_name': 'Member'},
            'about': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'friendships': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'friends_with+'", 'to': u"orm['mumlife.Member']", 'through': u"orm['mumlife.Friendships']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'gender': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interests': ('tagging.fields.TagField', [], {}),
            'max_range': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'picture': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'slug': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'spouse': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'partner'", 'null': 'True', 'to': u"orm['mumlife.Member']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'units': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'mumlife.message': {
            'Meta': {'object_name': 'Message'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'eventdate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'eventenddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_reply': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mumlife.Member']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'occurrence': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'occurs_until': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sender'", 'null': 'True', 'to': u"orm['mumlife.Member']"}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'author'", 'null': 'True', 'to': u"orm['mumlife.Message']"}),
            'tags': ('tagging.fields.TagField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'visibility': ('django.db.models.fields.IntegerField', [], {'default': '2'})
        },
        u'mumlife.notifications': {
            'Meta': {'object_name': 'Notifications'},
            'events': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'notification_events'", 'blank': 'True', 'to': u"orm['mumlife.Message']"}),
            'friends_requests': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'notifications'", 'unique': 'True', 'to': u"orm['mumlife.Member']"}),
            'messages': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'threads': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'notification_threads'", 'blank': 'True', 'to': u"orm['mumlife.Message']"}),
            'total': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['mumlife']