import csv
import os
import sys
import zipfile
import gzip
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

from django_noaa.models import to_fahrenheit

import settings as _settings
import constants as c

REFERENCE_DIR = os.path.abspath(os.path.join(os.path.split(__file__)[0], 'reference'))

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
    
    station = models.ForeignKey(
        'django_noaa.Station',
        verbose_name=_('weather station'),
        related_name='loads',
        blank=True,
        null=True)
    
    class Meta:
        app_label = APP_LABEL
        ordering = (
            'name',
        )
        
    natural_keys = ('id',)
    
    def natural_key(self):
        return (self.id,)
    
    def __unicode__(self):
        #return u'%s: %s' % (self.id, self.name)
        return self.name

    def save(self, *args, **kwargs):
        
        if self.id:
            aggs = self.prices.all()\
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
        
        #start_date=date(2010,11,7)#TODO:remove
        assert start_date <= end_date, 'Start date must be before end date.'
        while start_date <= end_date:
            for da in xrange(2):
                # Non-day-ahead prices may be posted several days after
                # their date. So don't even bother downloading it the day of.
                if not da and start_date == date.today():
                    continue
                status, _ = LMPDAStatus.objects.get_or_create(date=start_date, day_ahead=da)
                #TODO:add separate flags for loading other rows
                if not status.loaded_zones:
                    cls.load_date(load_date=start_date, only_type=only_type, day_ahead=da)
                    status.loaded_zones = True
                    status.save()
            start_date += timedelta(days=1)

    @classmethod
    @commit_on_success
    def load_date(cls, load_date, only_type=None, day_ahead=True):
        print 'Loading PJM LMPDA data for %s.' % (load_date,)
        
        if day_ahead:
            PATTERN1 = settings.PJM_LMPDA_URL
            PATTERN2 = settings.PJM_LMPDA_URL2
        else:
            PATTERN1 = settings.PJM_LMP_URL
            PATTERN2 = settings.PJM_LMP_URL2
        
        def get_data():
            
            url = PATTERN1.format(
                year=load_date.year,
                month=load_date.month,
                day=load_date.day)
#            print url
            #data = urllib2.urlopen(url1).readlines()[6:]
            try:
                request = urllib2.Request(url)
                print 'Downloading raw data from %s...' % (url,)
                response = urllib2.urlopen(request)
                content_type = response.info().getheader('Content-Type')
    #            print 'content_type1:',content_type
                if content_type in ('application/octet-stream',):
                    return response.readlines()
            except urllib2.HTTPError, e:
                # The most recent files are CSV but older ones are deleted
                # and replaced with ZIP archives, so if we get a 404 for the
                # CSV then ignore it and try the ZIP.
                if e.code != 404:
                    raise
            
            url = PATTERN2.format(
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
            
        data = list(get_data())
        FIELD_MAP = {'TotalLMP':'total', 'CongestionPrice': 'congestion', 'MarginalLossPrice': 'marginal_loss'}
        total = len(data) - 1
        lines = csv.reader(data)
        lines = list(lines)
        i = 0
        headers = None
        hours_line = None
        start_found = False
        price_fields = None
        for line in lines:
            i += 1
            if i == 1 or not i % 10 or i == total:
                print '\rProcessing line %i of %i %.02f%%.' % (i, total, i/float(total)*100),
                sys.stdout.flush()
            try:
                
                if not start_found and line:
                    if day_ahead and line[0].strip() == 'Start of Day Ahead LMP Data':
                        start_found = True
                        hours_line = line
                        continue
                    elif not day_ahead and line[0].strip() == 'Start of Real Time LMP Data':
                        start_found = True
                        hours_line = line
                        continue
                    else:
                        # Otherwise ignore the many extraneous pre-header rows.
                        continue
                
                if headers is None:
                    headers = line
                    continue
                elif not line:
                    continue
                elif line[0].strip().lower().startswith('end of day'):
                    continue
                elif line[0].strip().lower().startswith('end of real'):
                    continue
                
#                print 'headers:',headers
#                print 'hours_line:',hours_line
#                print 'line:',line
                price_fields = zip(headers[7:], hours_line[7:], line[7:])
#                print 'price_fields:',price_fields
#                raw_input('enter')
                
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
                price_dict = defaultdict(dict)
                for name, hour, value in price_fields:
                    if not hour.strip():
                        continue
                    if not value.strip():
                        continue
                    if not hour.strip().isdigit():
                        # Ignore [0-9]+\[DST\] columns.
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
                        day_ahead=bool(day_ahead),
                    )
                    if LMPDA.objects.filter(**price_key).exists():
                        #TODO:overwrite existing data?
                        pass
                    else:
                        price_data.update(price_key)
                        price_data['hour'] = hour
                        price_data['day_ahead'] = day_ahead
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
        editable=False,
        db_index=True)
    
    day_ahead = models.BooleanField(
        default=True,
        db_index=True,
        editable=False)
    
    loaded_zones = models.BooleanField(
        default=False,
        editable=False,
        db_index=True)
    
    class Meta:
        app_label = APP_LABEL
        verbose_name = _('price import status')
        verbose_name_plural = _('prices import statuses')
        unique_together = (
            ('date', 'day_ahead'),
        )
    
class LMPDA(models.Model):
    """
    Stores location marginal price day-ahead data published at
    http://www.pjm.com/markets-and-operations/energy/day-ahead/lmpda.aspx
    """
    
    node = models.ForeignKey('Node', related_name='prices')
    
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
        decimal_places=6,
        help_text=_('Price in $/MW'))
    
    congestion = models.DecimalField(
        blank=False,
        null=False,
        db_index=True,
        editable=False,
        max_digits=10,
        decimal_places=6,
        #help_text=_('Price in $/MW')
    )
    
    marginal_loss = models.DecimalField(
        blank=False,
        null=False,
        db_index=True,
        editable=False,
        max_digits=10,
        decimal_places=6,
        #help_text=_('Price in $/MW')
    )
    
    day_ahead = models.BooleanField(
        default=True,
        db_index=True,
        editable=False)
    
    class Meta:
        app_label = APP_LABEL
        verbose_name = _('price')
        verbose_name_plural = _('prices')
        unique_together = (
            ('node', 'start_datetime', 'end_datetime', 'day_ahead'),
        )
        ordering = (
            'start_datetime', 'end_datetime', 'day_ahead',
        )
        
    natural_keys = ('node', 'start_datetime', 'end_datetime')
    
    def natural_key(self):
        return self.node.natural_key() + (self.start_datetime, self.end_datetime)
    
    def __unicode__(self):
        return u'%s: %s to %s' % (self.node, self.start_datetime, self.end_datetime)

    def save(self, *args, **kwargs):
        super(LMPDA, self).save(*args, **kwargs)

class Load(models.Model):
    
    node = models.ForeignKey(
        'Node',
        related_name='loads',
        verbose_name=_('zone'))
    
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
    
    segment = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        db_index=True,
        editable=False)
    
    load = models.FloatField(
        blank=False,
        null=False,
        db_index=True,
        editable=False,
        verbose_name=_('load factor'),
        help_text=_('An estimate of the load on the power distribution system.'))
    
    class Meta:
        app_label = APP_LABEL
        unique_together = (
            ('node', 'start_datetime', 'end_datetime', 'segment'),
        )
    
    @classmethod
    def calculate(cls, zone, *args, **kwargs):
        getattr(cls, 'calculate_%s' % zone.lower())(*args, **kwargs)
    
    @classmethod
    @commit_on_success
    def calculate_ppl(cls, year, month, segment):
        from django_noaa.models import Station
        #station = Station.objects.get(wban=station_id)
        
        node = Node.objects.get(name='PPL', type=c.ZONE)
        station = node.station
        assert station, 'No weather station set for node %s.' % (node,)
        assert station.load_temperatures, \
            'No temperatures loaded for station %s.' % (station,)
        
        # Prior to 2013, the files contained a LOW_5/HIGH_5 column that was
        # essentially unused. These columns were removed in the 2013 file
        # and onwards.
#        if year < 2013:
#            raise NotImplementedError
        
        def compute_load_from_temp(temp0, temp_cutoffs, C0, coeffs):
            if ((len(coeffs)==0) or (len(temp_cutoffs)!=len(coeffs))):
                return 0
            ret = C0;
            low0 = 0;
            for ii in xrange(0, len(temp_cutoffs)-1):
                if temp0 < temp_cutoffs[ii]:
                    return ret+coeffs[ii]*(temp0-low0)
                else:
                    ret += coeffs[ii]*(temp_cutoffs[ii]-low0)
                    low0 = temp_cutoffs[ii]
            return ret
        
        equations_fn = os.path.join(
            REFERENCE_DIR,
            'ppl/ProfileEquations_{year:04d}-cropped.txt.gz'.format(year=year))
        print 'equations_fn:',equations_fn
        assert os.path.isfile(equations_fn), 'File %s does not exist.' % (equations_fn,)
        
        equation_lines_by_day_hour = {}
        total = gzip.open(equations_fn, 'rb').read().count('\n')
        fin = csv.DictReader(gzip.open(equations_fn, 'rb'), delimiter='~')
        i = 0
        unique_days = set()
        for row in fin:
            i += 1
            if i == 1 or not i % 10:
                print '\rReading equations %i of %i %.02f%%.' % (i, total, i/float(total)*100),
                sys.stdout.flush()
            segment0 = row['PROFILE_CLASS']
            year0 = int(float(row['YEAR']))
            month0 = int(float(row['MONTH']))
            if segment0 == segment and month0 == month and year0 == year:
                day0 = int(float(row['DAY']))
                unique_days.add(day0)
                hour0 = int(float(row['HOUR'])/100.) - 1
                equation_lines_by_day_hour[(day0, hour0)] = row
        print

        for day0 in sorted(unique_days):
            date0 = date(year, month, day0)
            print 'Processing date %s.' % (date0,)
            loads0 = []
            previous_temp = 0
            for hour0 in xrange(24):
                data = equation_lines_by_day_hour[(day0, hour0)]
                temp_cutoffs = []
                coeffs = []
                
                temp_cutoffs = [float(data[_]) for _ in sorted(data.iterkeys()) if _.startswith('HIGH_') and data[_].strip()]
                coeffs = [float(data[_]) for _ in sorted(data.iterkeys()) if _.startswith('COEFF_') and data[_].strip()]
                const_coeff = float(data['CONSTANT'])
                
                obs_start_datetime = datetime(year, month, day0, hour0).replace(tzinfo=UTC)
                obs_end_datetime = (datetime(year, month, day0, hour0) + timedelta(hours=1)).replace(tzinfo=UTC)
                
                # Lookup temperature.
                q = station.temperatures.filter(
                    obs_start_datetime=obs_start_datetime,
                    obs_end_datetime=obs_end_datetime)
                if not q.exists():
                    raise Exception, ('No temperatures have been loaded for '\
                        'datetime range %s to %s!') \
                            % (obs_start_datetime, obs_end_datetime)
                temp0 = to_fahrenheit(q[0].t_hr_avg)
                
                # Some weather stations mis some measurements. In these
                # instances, the value will be something outrageous
                # like -99999. So we ignore this and use the previous value,
                # assuming the missing temperature was probably close to that.
                if temp0 < -100: temp0 = previous_temp
                previous_temp = temp0
                
                # Calculate load for this hour.
                load0 = compute_load_from_temp(
                    temp0=temp0,
                    temp_cutoffs=temp_cutoffs,
                    C0=const_coeff,
                    coeffs=coeffs,
                )

                key = dict(
                    node=node,
                    #station=station,
                    start_datetime=obs_start_datetime,
                    end_datetime=obs_end_datetime,
                    segment=segment,
                )
                if Load.objects.filter(**key).exists():
                    Load.objects.filter(**key).update(load=load0)
                else:
                    key['load'] = load0
                    Load.objects.create(**key)

class DailySummary(models.Model):
    
    id = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        editable=False,
        primary_key=True)
    
    node = models.ForeignKey(
        'Node',
        editable=False,
        blank=False,
        null=False,
        db_column='node_id')

    segment = models.CharField(
        max_length=100,
        editable=False,
        blank=True,
        null=True)
    
    start_date = models.DateField(
        blank=False,
        null=False,
        editable=False)
    
    sum_load = models.FloatField(
        editable=False,
        verbose_name=_('sum load factor'))
    
    avg_total = models.FloatField(
        blank=False,
        null=False,
        editable=False,
        verbose_name=_('mean total real-time price'),
        help_text=_('$/MW'))
    
    avg_total_da = models.FloatField(
        blank=False,
        null=False,
        editable=False,
        verbose_name=_('mean total day-ahead price'),
        help_text=_('$/MW'))
    
    avg_total2 = models.FloatField(
        blank=False,
        null=False,
        editable=False,
        verbose_name=_('mean total real-time comprehensive price'),
        help_text=_('$/MW'))
    
    avg_total2_da = models.FloatField(
        blank=False,
        null=False,
        editable=False,
        verbose_name=_('mean total day-ahead comprehensive price'),
        help_text=_('$/MW'))
    
    class Meta:
        app_label = APP_LABEL
        managed = False
        verbose_name_plural = _('daily summaries')
        ordering = ('start_date',)
        