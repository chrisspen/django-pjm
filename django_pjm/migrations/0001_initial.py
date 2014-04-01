# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Node'
        db.create_table(u'django_pjm_node', (
            ('id', self.gf('django.db.models.fields.PositiveIntegerField')(unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('voltage', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('equipment', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=100, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=100, null=True, blank=True)),
            ('zone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_pjm.Node'], null=True, blank=True)),
            ('lmpda_start_datetime_min', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('lmpda_start_datetime_max', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal('django_pjm', ['Node'])

        # Adding model 'LMPDA'
        db.create_table(u'django_pjm_lmpda', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(related_name='day_ahead_prices', to=orm['django_pjm.Node'])),
            ('start_datetime', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('end_datetime', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('total', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=6, db_index=True)),
            ('congestion', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=6, db_index=True)),
            ('marginal_loss', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=6, db_index=True)),
        ))
        db.send_create_signal('django_pjm', ['LMPDA'])

        # Adding unique constraint on 'LMPDA', fields ['node', 'start_datetime', 'end_datetime']
        db.create_unique(u'django_pjm_lmpda', ['node_id', 'start_datetime', 'end_datetime'])


    def backwards(self, orm):
        # Removing unique constraint on 'LMPDA', fields ['node', 'start_datetime', 'end_datetime']
        db.delete_unique(u'django_pjm_lmpda', ['node_id', 'start_datetime', 'end_datetime'])

        # Deleting model 'Node'
        db.delete_table(u'django_pjm_node')

        # Deleting model 'LMPDA'
        db.delete_table(u'django_pjm_lmpda')


    models = {
        'django_pjm.lmpda': {
            'Meta': {'ordering': "('start_datetime', 'end_datetime')", 'unique_together': "(('node', 'start_datetime', 'end_datetime'),)", 'object_name': 'LMPDA'},
            'congestion': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '6', 'db_index': 'True'}),
            'end_datetime': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marginal_loss': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '6', 'db_index': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'day_ahead_prices'", 'to': "orm['django_pjm.Node']"}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '6', 'db_index': 'True'})
        },
        'django_pjm.node': {
            'Meta': {'ordering': '()', 'object_name': 'Node'},
            'equipment': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.PositiveIntegerField', [], {'unique': 'True', 'primary_key': 'True'}),
            'lmpda_start_datetime_max': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'lmpda_start_datetime_min': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'voltage': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django_pjm.Node']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['django_pjm']