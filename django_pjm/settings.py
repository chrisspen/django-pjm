from django.conf import settings

LMPDA_URL = settings.PJM_LMPDA_URL = getattr(
    settings,
    'PJM_LMPDA_URL',
    'http://www.pjm.com/pub/account/lmpda/{year:04d}{month:02d}{day:02d}-da.csv')

LMPDA_URL2 = settings.PJM_LMPDA_URL2 = getattr(
    settings,
    'PJM_LMPDA_URL2',
    'http://www.pjm.com/pub/account/lmpda/{year:04d}{month:02d}{day:02d}-da.zip')
