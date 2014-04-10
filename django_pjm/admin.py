from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from admin_steroids.queryset import ApproxCountQuerySet
from admin_steroids.utils import view_related_link
from admin_steroids.options import (
    BetterRawIdFieldsModelAdmin, ReadonlyModelAdmin,
)

import models

class NodeAdmin(BetterRawIdFieldsModelAdmin):
    
    list_display = (
        'id',
        'name',
        'type',
        #'zone',
        'lmpda_start_datetime_min',
        'lmpda_start_datetime_max',
        'station',
    )
    
    list_filter = (
        'type',
    )
    
    search_fields = (
        'name',
    )
    
    raw_id_fields = (
        'station',
    )
    
    def da_prices_link(self, obj=None):
        if not obj:
            return ''
        return view_related_link(obj, 'prices')
    da_prices_link.allow_tags = True
    da_prices_link.short_description = 'day-ahead prices'
    
    def loads_link(self, obj=None):
        if not obj:
            return ''
        return view_related_link(obj, 'loads')
    loads_link.allow_tags = True
    loads_link.short_description = 'loads'
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super(NodeAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    
    def get_readonly_fields(self, request, obj=None):
        exclude = ['station']
        return [f.name for f in self.model._meta.fields if f.name not in exclude] + ['da_prices_link', 'loads_link']
    
    def queryset(self, *args, **kwargs):
        qs = super(NodeAdmin, self).queryset(*args, **kwargs)
        qs = qs._clone(klass=ApproxCountQuerySet)
        return qs

admin.site.register(
    models.Node,
    NodeAdmin)

class LMPDAAdmin(admin.ModelAdmin):
    
    list_display = (
        'node',
        'start_datetime',
        'end_datetime',
        'total',
        'congestion',
        'marginal_loss',
        'day_ahead',
    )
    
    list_filter = (
        'node',
        'day_ahead',
        'start_datetime',
    )
    
    search_fields = (
    )
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super(LMPDAAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    
    def get_readonly_fields(self, request, obj=None):
        exclude = []
        return [f.name for f in self.model._meta.fields if f.name not in exclude] + []
    
    def queryset(self, *args, **kwargs):
        qs = super(LMPDAAdmin, self).queryset(*args, **kwargs)
        qs = qs._clone(klass=ApproxCountQuerySet)
        return qs

admin.site.register(
    models.LMPDA,
    LMPDAAdmin)

class LMPDAStatusAdmin(admin.ModelAdmin):
    
    list_display = (
        'date',
        'loaded_zones',
        'day_ahead',
    )
    
    list_filter = (
        'date',
        'loaded_zones',
        'day_ahead',
    )
    
    search_fields = (
    )
    
    def has_delete_permission(self, request, obj=None):
        #return False
        return True
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super(LMPDAStatusAdmin, self).get_actions(request)
        #del actions['delete_selected']
        return actions
    
    def get_readonly_fields(self, request, obj=None):
        exclude = []
        return [f.name for f in self.model._meta.fields if f.name not in exclude] + []
    
    def queryset(self, *args, **kwargs):
        qs = super(LMPDAStatusAdmin, self).queryset(*args, **kwargs)
        qs = qs._clone(klass=ApproxCountQuerySet)
        return qs

admin.site.register(
    models.LMPDAStatus,
    LMPDAStatusAdmin)

class LoadAdmin(admin.ModelAdmin):
    
    list_display = (
        'id',
        'node',
        #'station',
        'start_datetime',
        'end_datetime',
        'segment',
        'load',
    )
    
    list_filter = (
        'start_datetime',
        'node',
        'segment',
    )
    
    search_fields = (
    )
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super(LoadAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    
    def get_readonly_fields(self, request, obj=None):
        exclude = []
        return [f.name for f in self.model._meta.fields if f.name not in exclude] + []
    
    def queryset(self, *args, **kwargs):
        qs = super(LoadAdmin, self).queryset(*args, **kwargs)
        qs = qs._clone(klass=ApproxCountQuerySet)
        return qs

admin.site.register(
    models.Load,
    LoadAdmin)

class DailySummaryAdmin(ReadonlyModelAdmin):
    
    list_display = (
        'id',
        'node',
        'segment',
        'start_date',
        'sum_load',
        'avg_total',
        'avg_total_da',
        'avg_total2',
        'avg_total2_da',
    )
    
    list_filter = (
        'segment',
        'start_date',
    )
    
    readonly_fields = (
    )
    
    def lookup_allowed(self, key=None, value=None):
        return True
    
admin.site.register(
    models.DailySummary,
    DailySummaryAdmin)
