from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from admin_steroids.queryset import ApproxCountQuerySet
from admin_steroids.utils import view_related_link

import models

class NodeAdmin(admin.ModelAdmin):
    
    list_display = (
        'id',
        'name',
        'type',
        #'zone',
        'lmpda_start_datetime_min',
        'lmpda_start_datetime_max',
    )
    
    list_filter = (
        'type',
    )
    
    search_fields = (
        'name',
    )
    
    def da_prices_link(self, obj=None):
        if not obj:
            return ''
        return view_related_link(obj, 'day_ahead_prices')
    da_prices_link.allow_tags = True
    da_prices_link.short_description = 'day-ahead prices'
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_actions(self, request):
        actions = super(NodeAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
    
    def get_readonly_fields(self, request, obj=None):
        exclude = []
        return [f.name for f in self.model._meta.fields if f.name not in exclude] + ['da_prices_link']
    
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
    )
    
    list_filter = (
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
