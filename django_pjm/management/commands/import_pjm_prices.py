from optparse import make_option

from django.core.management.base import NoArgsCommand, BaseCommand

from django_pjm import models

class Command(BaseCommand):
    help = "Imports PJM locational marginal pricing day-ahead data."
    args = ''
    option_list = BaseCommand.option_list + (
        make_option('--start-year', default=0),
        make_option('--end-year', default=0),
        make_option('--only-type', default=None),
        make_option('--auto-reprocess-days', default=0),
    )
    
    def handle(self, **options):
        models.Node.load(
            start_year=int(options['start_year']),
            end_year=int(options['end_year']),
            only_type=options['only_type'].strip(),
            auto_reprocess_days=int(options['auto_reprocess_days']),
        )
        