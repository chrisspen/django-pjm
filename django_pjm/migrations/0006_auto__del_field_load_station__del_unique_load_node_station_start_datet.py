# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'Load', fields ['node', 'station', 'start_datetime', 'end_datetime', 'segment']
        db.delete_unique(u'django_pjm_load', ['node_id', 'station_id', 'start_datetime', 'end_datetime', 'segment'])

        # Deleting field 'Load.station'
        db.delete_column(u'django_pjm_load', 'station_id')

        # Adding unique constraint on 'Load', fields ['node', 'start_datetime', 'end_datetime', 'segment']
        db.create_unique(u'django_pjm_load', ['node_id', 'start_datetime', 'end_datetime', 'segment'])

        # Adding field 'Node.station'
        db.add_column(u'django_pjm_node', 'station',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='loads', null=True, to=orm['django_noaa.Station']),
                      keep_default=False)


    def backwards(self, orm):
        # Removing unique constraint on 'Load', fields ['node', 'start_datetime', 'end_datetime', 'segment']
        db.delete_unique(u'django_pjm_load', ['node_id', 'start_datetime', 'end_datetime', 'segment'])


        # User chose to not deal with backwards NULL issues for 'Load.station'
        raise RuntimeError("Cannot reverse this migration. 'Load.station' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Load.station'
        db.add_column(u'django_pjm_load', 'station',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='loads', to=orm['django_noaa.Station']),
                      keep_default=False)

        # Adding unique constraint on 'Load', fields ['node', 'station', 'start_datetime', 'end_datetime', 'segment']
        db.create_unique(u'django_pjm_load', ['node_id', 'station_id', 'start_datetime', 'end_datetime', 'segment'])

        # Deleting field 'Node.station'
        db.delete_column(u'django_pjm_node', 'station_id')


    models = {
        'django_noaa.station': {
            'Meta': {'ordering': "('wban', 'country', 'state', 'location')", 'unique_together': "(('wban', 'country', 'state', 'location'),)", 'object_name': 'Station'},
            'closing': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'commissioning': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'elevation': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'load_temperatures': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'load_temperatures_max_date_loaded': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'load_temperatures_min_date_loaded': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'load_temperatures_min_year': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'network': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'operation': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'pairing': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'vector': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'wban': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'django_pjm.lmpda': {
            'Meta': {'ordering': "('start_datetime', 'end_datetime', 'day_ahead')", 'unique_together': "(('node', 'start_datetime', 'end_datetime', 'day_ahead'),)", 'object_name': 'LMPDA'},
            'congestion': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '6', 'db_index': 'True'}),
            'day_ahead': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'end_datetime': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'hour': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marginal_loss': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '6', 'db_index': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'prices'", 'to': "orm['django_pjm.Node']"}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '6', 'db_index': 'True'})
        },
        'django_pjm.lmpdastatus': {
            'Meta': {'unique_together': "(('date', 'day_ahead'),)", 'object_name': 'LMPDAStatus'},
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'day_ahead': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaded_zones': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        },
        'django_pjm.load': {
            'Meta': {'unique_together': "(('node', 'start_datetime', 'end_datetime', 'segment'),)", 'object_name': 'Load'},
            'end_datetime': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'load': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'loads'", 'to': "orm['django_pjm.Node']"}),
            'segment': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'django_pjm.node': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Node'},
            'equipment': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'primary_key': 'True'}),
            'lmpda_start_datetime_max': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'lmpda_start_datetime_min': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'station': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'loads'", 'null': 'True', 'to': "orm['django_noaa.Station']"}),
            'type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'voltage': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django_pjm.Node']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['django_pjm']