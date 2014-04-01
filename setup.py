#!/usr/bin/env python
import os
import urllib

from setuptools import setup, find_packages, Command

import django_pjm

setup(
    name = 'django-pjm',
    version = django_pjm.__version__,
    packages = find_packages(),
#    package_data = {
#        'django_sec': [
#            'templates/*.*',
#            'templates/*/*.*',
#            'templates/*/*/*.*',
#            'static/*.*',
#            'static/*/*.*',
#            'static/*/*/*.*',
#        ],
#    },
    author = "Chris Spencer",
    author_email = "chrisspen@gmail.com",
    description = "A Django app for managing public PJM energy pricing data.",
    license = "MIT",
    url = "https://github.com/chrisspen/django-pjm",
    classifiers = [
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    zip_safe = False,
    install_requires = [
        'Django>=1.4.0',
        #'fixed2csv>=0.2.0',
        'django-admin-steroids>=0.2.0',
    ],
)
