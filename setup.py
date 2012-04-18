#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'EduTracTeamCalendar',
    author = 'Martin Aspeli, Aleksey A. Porfirov',
    author_email = 'lexqt@yandex.ru',
    description = 'EduTrac plugin for managing team availability',
    version = '0.1',
    license='BSD',
    packages=['teamcalendar'],
    package_data={'teamcalendar': ['templates/*.html', 
                                   'htdocs/css/*.css',]},
    entry_points = {
        'trac.plugins': [
            'teamcalendar = teamcalendar'
        ]
    },
)

#### AUTHORS ####
## Author of original TeamCalendarPlugin:
## Martin Aspeli
## optilude@gmail.com
##
## Author of EduTrac adaptation and some fixes and enhancements:
## Aleksey A. Porfirov
## lexqt@yandex.ru
## github: lexqt
