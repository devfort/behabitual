# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Bucket'
        db.create_table(u'habits_bucket', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('habit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='buckets', to=orm['habits.Habit'])),
            ('index', self.gf('django.db.models.fields.IntegerField')()),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
            ('resolution', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'habits', ['Bucket'])

        # Adding field 'Habit.start'
        db.add_column(u'habits_habit', 'start',
                      self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2013, 3, 8, 0, 0)),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'Bucket'
        db.delete_table(u'habits_bucket')

        # Deleting field 'Habit.start'
        db.delete_column(u'habits_habit', 'start')


    models = {
        u'accounts.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '500', 'db_index': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'habits.bucket': {
            'Meta': {'object_name': 'Bucket'},
            'habit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'buckets'", 'to': u"orm['habits.Habit']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {}),
            'resolution': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'habits.habit': {
            'Meta': {'object_name': 'Habit'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resolution': ('django.db.models.fields.CharField', [], {'default': "'day'", 'max_length': '10'}),
            'start': ('django.db.models.fields.DateField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'habits'", 'to': u"orm['accounts.User']"})
        }
    }

    complete_apps = ['habits']