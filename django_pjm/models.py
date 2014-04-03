import csv
import os
import sys
import zipfile
import urllib2
from collections import defaultdict
from datetime import datetime, date, timedelta
from cStringIO import StringIO

import dateutil.parser

from pytz import UTC

from django.db import models, transaction
from django.db.models import Min, Max
from django.db.transaction import commit_on_success
from django.conf import settings
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils import timezone

try:
    from admin_steroids.utils import StringWithTitle
    APP_LABEL = StringWithTitle('django_pjm', 'PJM')
except ImportError:
    APP_LABEL = 'django_pjm'

import settings as _settings
import constants as c

#REFERENCE_DIR = os.path.abspath(os.path.join(os.path.split(__file__)[0], 'reference'))

class Node(models.Model):
    """
    Represents a pricing measurement point in PJM.
    """
    
    id = models.PositiveIntegerField(
        blank=False,
        null=False,
        unique=True,
        primary_key=True,
        verbose_name=_('PnodeID'),
    )
    
    name = models.CharField(
        max_length=100,
        editable=False,
        blank=True,
        null=True)
    
    voltage = models.PositiveIntegerField(
        db_index=True,
        editable=False,
        blank=True,
        null=True)
    
    equipment = models.CharField(
        max_length=100,
        db_index=True,
        editable=False,
        blank=True,
        null=True)
    
    type = models.CharField(
        max_length=100,
        db_index=True,
        editable=False,
        blank=True,
        null=True)
    
    zone = models.ForeignKey(
        'self',
        editable=False,
        blank=True,
        null=True)
    
    lmpda_start_datetime_min = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('minimum LMPDA start datetime'),
        db_index=True,
        editable=False)
    
    lmpda_start_datetime_max = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('maximum LMPDA start datetime'),
        db_index=True,
        editable=False)
    
    class Meta:
        app_label = APP_LABEL
        ordering = (
        )
        
    natural_keys = ('id',)
    
    def natural_key(self):
        return (self.id,)
    
    def __unicode__(self):
        return u'%s: %s' % (self.id, self.name)

    def save(self, *args, **kwargs):
        
        if self.id:
            aggs = self.day_ahead_prices.all()\
                .aggregate(Min('start_datetime'), Max('start_datetime'))
            self.lmpda_start_datetime_min = aggs['start_datetime__min']
            self.lmpda_start_datetime_max = aggs['start_datetime__max']
            
        super(Node, self).save(*args, **kwargs)
        
    @classmethod
    def load(cls, start_year=0, end_year=0, only_type=None, auto_reprocess_days=0):
        only_type = (only_type or '').strip().upper()
        assert not only_type or only_type in c.TYPES, \
            'Invalid only-type: %s' % (only_type,)
            
        if start_year:
            start_date = date(start_year, 1, 1)
        elif auto_reprocess_days:
            start_date = date.today() - timedelta(days=auto_reprocess_days)
        else:
            start_date = date.today()
        print 'start_date:',start_date
            
        if end_year:
            end_date = date(end_year, 1, 1)
        else:
            end_date = date.today()
        print 'end_date:',end_date
        
        assert start_date <= end_date, 'Start date must be before end date.'
        while start_date <= end_date:
            status, _ = LMPDAStatus.objects.get_or_create(date=start_date)
            #TODO:add separate flags for loading other rows
            if not status.loaded_zones:
                cls.load_date(load_date=start_date, only_type=only_type)
                status.loaded_zones = True
                status.save()
            start_date += timedelta(days=1)

    @classmethod
    @commit_on_success
    def load_date(cls, load_date, only_type=None):
        print 'Loading PJM LMPDA data for %s.' % (load_date,)
        
        def get_data():
            
            url = settings.PJM_LMPDA_URL.format(
                year=load_date.year,
                month=load_date.month,
                day=load_date.day)
#            print url
            #data = urllib2.urlopen(url1).readlines()[6:]
            request = urllib2.Request(url)
            print 'Downloading raw data from %s...' % (url,)
            response = urllib2.urlopen(request)
            content_type = response.info().getheader('Content-Type')
#            print 'content_type1:',content_type
            if content_type in ('application/octet-stream',):
                return response.readlines()
            
            url = settings.PJM_LMPDA_URL2.format(
                year=load_date.year,
                month=load_date.month,
                day=load_date.day)
#            print url
            request = urllib2.Request(url)
            print 'Downloading archived data from %s...' % (url,)
            response = urllib2.urlopen(request)
            content_type = response.info().getheader('Content-Type')
#            print 'content_type2:',content_type
            if content_type in ('application/x-zip-compressed',):
                zip = zipfile.ZipFile(StringIO(response.read()))
                return zip.read(zip.namelist()[0]).split('\n')
            
            raise Exception, 'No data found.'
            
        data = get_data()[6:]
        hours_line = data[0].strip().split(',')
        #print 'hours_line:',hours_line
        data = data[1:]
        #print data[0]
        #return
        FIELD_MAP = {'TotalLMP':'total', 'CongestionPrice': 'congestion', 'MarginalLossPrice': 'marginal_loss'}
        total = len(data) - 1
        lines = csv.reader(data)
        lines = list(lines)
        i = 0
        headers = None
        for line in lines:
            i += 1
            if i == 1 or not i % 10:
                print '\rProcessing line %i of %i %.02f%%.' % (i, total, i/float(total)*100),
                sys.stdout.flush()
            try:
                
                if i == 1:
                    headers = line
                    continue
                elif not line:
                    continue
                elif line[0].strip().lower().startswith('end of day'):
                    continue
                
                dt, pnodeid, name, voltage, equipment, type_str, zone = line[:7]
                raw_dt = dt
                dt = datetime(int(dt[:4]), int(dt[4:6]), int(dt[6:8]))
                pnodeid = int(pnodeid)
                type_str = type_str.strip()
                if only_type and type_str != only_type:
                    continue
                #print line
                #print 'dt:',raw_dt,dt
                
                voltage = voltage.strip()
                if not voltage:
                    voltage = None
                elif voltage.endswith(' KV'):
                    voltage = int(voltage[:-2].strip())
                else:
                    raise Exception, 'Unknown voltage representation: %s' % voltage
                
                zone = zone.strip()
                if zone:
                    zone = Node.objects.get(name=zone, type=c.ZONE)
                else:
                    zone = None
                
                node, _ = Node.objects.get_or_create(
                    id=pnodeid,
                    defaults=dict(
                        name=name,
                        voltage=voltage,
                        equipment=equipment.strip(),
                        type=type_str.strip().upper(),
                        zone=zone,
                    ),
                )
                #print 'node:',node
                price_fields = zip(headers[7:], hours_line[7:], line[7:])
                #print 'price_fields:',price_fields
                price_dict = defaultdict(dict)
                for name, hour, value in price_fields:
                    if not hour.strip():
                        continue
                    if not value.strip():
                        continue
                    price_dict[int(hour)/100][FIELD_MAP[name.strip()]] = value
                for hour, price_data in price_dict.iteritems():
                    # Hours are in Eastern Prevailing Time (EPT), which has
                    # a GMT/UTC offset of -5, so we have to add 5 hours to get
                    # the UTC datetime.
                    start_datetime = (dt + timedelta(hours=hour) - timedelta(hours=1) + timedelta(hours=5)).replace(tzinfo=UTC)
                    end_datetime = (dt + timedelta(hours=hour) + timedelta(hours=5)).replace(tzinfo=UTC)
                    #print 'price dates:',hour,start_datetime,end_datetime
                    node.lmpda_start_datetime_min = min(node.lmpda_start_datetime_min or start_datetime, start_datetime)
                    node.lmpda_start_datetime_max = min(node.lmpda_start_datetime_max or start_datetime, start_datetime)
                    price_key = dict(
                        node=node,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                    )
                    if LMPDA.objects.filter(**price_key).exists():
                        #TODO:overwrite existing data?
                        pass
                    else:
                        price_data.update(price_key)
                        price_data['hour'] = hour
                        #print 'price_data:',price_data
                        LMPDA.objects.create(**price_data)
                node.save()
            except Exception, e:
                print>>sys.stderr, 'Error processing line %i: %s' % (i, e)
                print>>sys.stderr, line
                raise
    
        print '\r%i of %i %.02f%%' % (total, total, 100),
        print
        print 'Done!'
        sys.stdout.flush()

class LMPDAStatus(models.Model):
    
    date = models.DateField(
        blank=False,
        null=False,
        unique=True,
        editable=False,
        db_index=True)
    
    loaded_zones = models.BooleanField(
        default=False,
        editable=False,
        db_index=True)
    
    class Meta:
        app_label = APP_LABEL
        verbose_name = _('day-ahead locational marginal price import status')
        verbose_name_plural = _('day-ahead locational marginal prices import statuses')
    
class LMPDA(models.Model):
    """
    Stores location marginal price day-ahead data published at
    http://www.pjm.com/markets-and-operations/energy/day-ahead/lmpda.aspx
    """
    
    node = models.ForeignKey('Node', related_name='day_ahead_prices')
    
    start_datetime = models.DateTimeField(
        blank=False,
        null=False,
        db_index=True,
        editable=False)
    
    end_datetime = models.DateTimeField(
        blank=False,
        null=False,
        db_index=True,
        editable=False)
    
    hour = models.PositiveIntegerField(
        blank=False,
        null=False,
        db_index=True,
        editable=False)
    
    total = models.DecimalField(
        blank=False,
        null=False,
        db_index=True,
        editable=False,
        max_digits=10,
        decimal_places=6)
    
    congestion = models.DecimalField(
        blank=False,
        null=False,
        db_index=True,
        editable=False,
        max_digits=10,
        decimal_places=6)
    
    marginal_loss = models.DecimalField(
        blank=False,
        null=False,
        db_index=True,
        editable=False,
        max_digits=10,
        decimal_places=6)
    
    class Meta:
        app_label = APP_LABEL
        verbose_name = _('day-ahead locational marginal price')
        verbose_name_plural = _('day-ahead locational marginal prices')
        unique_together = (
            ('node', 'start_datetime', 'end_datetime'),
        )
        ordering = (
            'start_datetime', 'end_datetime',
        )
        
    natural_keys = ('node', 'start_datetime', 'end_datetime')
    
    def natural_key(self):
        return self.node.natural_key() + (self.start_datetime, self.end_datetime)
    
    def __unicode__(self):
        return u'%s: %s to %s' % (self.node, self.start_datetime, self.end_datetime)

    def save(self, *args, **kwargs):
        super(LMPDA, self).save(*args, **kwargs)
