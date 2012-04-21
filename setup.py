#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

extra = {} 
try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py',                'python', None),
            ('**/templates/**.html', 'genshi', None),
            ('**/templates/**.txt',  'genshi', {
                'template_class': 'genshi.template:NewTextTemplate',
            }),
        ]
        extra['message_extractors'] = {
            'teamcalendar': extractors,
        }
except ImportError:
    pass

setup(
    name = 'EduTracTeamCalendar',
    author = 'Aleksey A. Porfirov',
    author_email = 'lexqt@yandex.ru',
    description = 'EduTrac plugin for managing team availability',
    version = '0.2',
    license='BSD',
    packages=['teamcalendar'],
    package_data={'teamcalendar': ['templates/*.html', 
                                   'htdocs/css/*.css',
                                   'locale/*/LC_MESSAGES/*.mo']},
    entry_points = {
        'trac.plugins': [
            'teamcalendar = teamcalendar'
        ]
    },
    **extra
)

#### AUTHORS ####
## Author of original TeamCalendarPlugin:
## Martin Aspeli
## optilude@gmail.com
##
## Maintainer of original TeamCalendarPlugin:
## Chris Nelson
## Chris.Nelson@SIXNET.com
##
## Author of EduTrac adaptation, fixes and enhancements:
## Aleksey A. Porfirov
## lexqt@yandex.ru
## github: lexqt
