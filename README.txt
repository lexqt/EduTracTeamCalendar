====================
Team Calendar Plugin
====================

This plugin adds a new tab, Team Calendar, to users with the TEAMCALENDAR_VIEW
permission. This shows a simple tables with dates running down the rows
and team members across the columns. Users with TEAMCALENDAR_UPDATE_OWN
permissions can change the state of the tick boxes under their own name,
and save the results. Users with TEAMCALENDAR_UPDATE_OTHERS permission can
update everyone's.

The 'availability' column in DB table is decimal from 0.00 to 1.00.
So it is possible to store more granular availability,
e.g. half-day, but there is no UI for this at present.

The calendar does not do anything more by itself. However, the 
team_availability table can be used in reports.

Installation
------------

Install using 'setup.py install' or easy_install as normal, and then
enable in trac.ini with:

	[components]
	teamcalendar.* = enabled
	
If you want to display more or fewer weeks before or after the current week
by default, add:

	[team-calendar]
	weeks_prior = 2
	weeks_after = 3
