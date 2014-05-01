from datetime import date
from monthdelta import MonthDelta as monthdelta

from optparse import make_option

from django.core.management.base import NoArgsCommand, BaseCommand

import dateutil.parser

from django_pjm import models

class Command(BaseCommand):
    help = "Imports PJM load values."
    args = ''
    option_list = BaseCommand.option_list + (
        make_option('--start-date', default=None),
        make_option('--end-date', default=None),
        make_option('--zone', default=None),
        make_option('--segments', default=None),
        #make_option('--only-type', default=None),
        #make_option('--auto-reprocess-days', default=0),
    )
    
    def handle(self, **options):
        
        start_date = (options['start_date'] or '').strip()
        if start_date:
            start_date = dateutil.parser.parse(start_date)
            start_date = date(start_date.year, start_date.month, start_date.day)
        else:
            start_date = date.today() - monthdelta(1)
            
        end_date = (options['end_date'] or '').strip()
        if end_date:
            end_date = dateutil.parser.parse(end_date)
            end_date = date(end_date.year, end_date.month, end_date.day)
        else:
            end_date = date.today()
        
        segments = [_ for _ in options['segments'].split(',') if _.strip()]
        
        while start_date <= end_date:
            for segment in segments:
                print 'Calculating for segment %s on start date %s.' % (segment, start_date)
                models.Load.calculate(
                    year=start_date.year,
                    month=start_date.month,
                    zone=options['zone'],
                    segment=segment,
                )
            start_date += monthdelta(1)
            