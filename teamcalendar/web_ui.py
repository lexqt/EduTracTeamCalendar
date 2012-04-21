from datetime import date, timedelta
from pkg_resources import resource_filename
from decimal import Decimal

from genshi.builder import tag

from trac.config import IntOption, ListOption
from trac.perm import IPermissionRequestor
from trac.core import Component, implements
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_script, \
                            add_warning
from trac.util.datefmt import parse_date_only, pretty_timedelta
from trac.project.api import ProjectManagement

from api import TeamCalendarSetupParticipant, _


__all__ = ['TeamCalendar']

TWOPLACES = Decimal(10) ** -2



class TeamCalendar(Component):

    implements(INavigationContributor, IRequestHandler, IPermissionRequestor, ITemplateProvider)

    # How much to display by default?
    weeks_prior = IntOption('team-calendar', 'weeks_prior', 1,
                            doc="Defines how many weeks before the current week to show by default",
                            switcher=True)
    weeks_after = IntOption('team-calendar', 'weeks_after', 3,
                            doc="Defines how many weeks after the current week to show by default",
                            switcher=True)

    # Default work week.
    work_days = ListOption('team-calendar', 'work_days',
                            doc="Lists days of week that are worked. Defaults to none.  0 is Monday.",
                            switcher=True)

    MAX_INTERVAL = 60

    def __init__(self):
        TeamCalendarSetupParticipant(self.env) # init main component
        self.pm = ProjectManagement(self.env)

    # INavigationContributor

    def get_active_navigation_item(self, req):
        return 'teamcalendar'

    def get_navigation_items(self, req):
        if 'TEAMCALENDAR_VIEW' in req.perm:
            yield ('mainnav', 'teamcalendar',
                   tag.a(_('Team Calendar'), href=req.href.teamcalendar()))

    # IPermissionRequestor

    def get_permission_actions(self):
        return ['TEAMCALENDAR_VIEW', 'TEAMCALENDAR_UPDATE_OTHERS', 'TEAMCALENDAR_UPDATE_OWN']

    # ITemplateProvider

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('teamcalendar', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler

    def match_request(self, req):
        return req.path_info.startswith('/teamcalendar')

    def process_request(self, req):
        req.perm.require('TEAMCALENDAR_VIEW')
        pid = self.pm.get_current_project(req)
        syllabus_id = req.data['syllabus_id']
        self.pm.check_component_enabled(self, syllabus_id=syllabus_id)

        work_days = [int(d) for d in self.work_days.syllabus(syllabus_id)]
        weeks_prior = self.weeks_prior.syllabus(syllabus_id)
        weeks_after = self.weeks_after.syllabus(syllabus_id)

        data = {}

        from_date = req.args.get('from_date', '')
        to_date   = req.args.get('to_date', '')
        from_date = from_date and parse_date_only(from_date) or self.find_default_start(weeks_prior)
        to_date   = to_date   and parse_date_only(to_date)   or self.find_default_end(weeks_after)

        # Check time interval
        force_default = True
        delta = (to_date - from_date).days
        if delta < 0:
            add_warning(req, _('Negative time interval selected. Using default.'))
        elif delta > self.MAX_INTERVAL:
            add_warning(req, _('Too big time interval selected (%(interval)s). '
                               'Using default.', interval=pretty_timedelta(to_date, from_date)))
        else:
            force_default = False

        # Reset interval to default
        if force_default:
            from_date = self.find_default_start(weeks_prior)
            to_date   = self.find_default_end(weeks_after)

        # Message
        data['message'] = ''

        # Current user
        data['authname'] = authname = req.authname

        # Can we update?

        data['can_update_own']    = can_update_own    = ('TEAMCALENDAR_UPDATE_OWN'    in req.perm)
        data['can_update_others'] = can_update_others = ('TEAMCALENDAR_UPDATE_OTHERS' in req.perm)
        data['can_update']        = can_update_own or can_update_others

        # Store dates
        data['today']     = date.today()
        data['from_date'] = from_date
        data['to_date']   = to_date

        # Get all people
        data['people'] = people = self.pm.get_project_users(pid)

        # Update timetable if required
        if 'update_calendar' in req.args:
            req.perm.require('TEAMCALENDAR_UPDATE_OWN')

            # deliberately override dates: want to show result of update
            from_date = current_date = parse_date_only(req.args.get('orig_from_date', ''))
            to_date   = parse_date_only(req.args.get('orig_to_date', ''))
            tuples = []
            while current_date <= to_date:
                if can_update_others:
                    for person in people:
                        status = Decimal(req.args.get(u'%s.%s' % (current_date.isoformat(), person), False))
                        tuples.append((current_date, person, status,))
                elif can_update_own:
                    status = Decimal(req.args.get(u'%s.%s' % (current_date.isoformat(), authname), False))
                    tuples.append((current_date, authname, status,))
                current_date += timedelta(1)

            self.update_timetable(tuples, pid, from_date, to_date)
            data['message'] = _('Timetable updated.')

        # Get the current timetable
        timetable = self.get_timetable(from_date, to_date, people, pid, work_days)

        data['timetable'] = []
        current_date = from_date
        while current_date <= to_date:
            data['timetable'].append(dict(date=current_date, people=timetable[current_date]))
            current_date += timedelta(1)

        add_stylesheet(req, 'common/css/jquery-ui/jquery.ui.core.css')
        add_stylesheet(req, 'common/css/jquery-ui/jquery.ui.datepicker.css')
        add_stylesheet(req, 'common/css/jquery-ui/jquery.ui.theme.css')
        add_script(req, 'common/js/jquery.ui.core.js')
        add_script(req, 'common/js/jquery.ui.widget.js')
        add_script(req, 'common/js/jquery.ui.datepicker.js')
        add_script(req, 'common/js/datepicker.js')

        add_stylesheet(req, 'teamcalendar/css/calendar.css')

        data['_'] = _
        return 'teamcalendar.html', data, None

    def get_timetable(self, from_date, to_date, people, pid, work_days):
        db = self.env.get_read_db()
        timetable_cursor = db.cursor()
        timetable_cursor.execute('''
            SELECT ondate, username, availability
            FROM team_availability
            WHERE project_id = %s
            AND ondate >= %s AND ondate <= %s
            ORDER BY ondate, username, availability
        ''', (pid, from_date.isoformat(), to_date.isoformat()))

        empty_day = dict([(p, Decimal(False)) for p in people])
        full_day  = dict([(p, Decimal(True))  for p in people])

        # fill timetable with default work days
        timetable = {}
        current_date = from_date
        while current_date <= to_date:
            if current_date.weekday() in work_days:
                timetable[current_date] = full_day.copy()
            else:
                timetable[current_date] = empty_day.copy()
            current_date += timedelta(1)

        # overwrite timetable with values from DB
        for row in timetable_cursor:
            timetable[row[0]][row[1]] = row[2]

        return timetable

    def update_timetable(self, tuples, pid, from_date, to_date):
        '''Update timetable with a list of tuples like
            [(datetime.date(2011, 11, 28), u'admin', <Decimal>),
             (datetime.date(2011, 11, 28), u'chrisn', <Decimal>),
             ...]
        '''

        for idx, row in enumerate(tuples):
            tuples[idx] = (row[0], row[1], row[2].quantize(TWOPLACES))

        db = self.env.get_read_db()

        # See what's already in the database for the same date range.
        users    = []
        for (date, user, _) in tuples:
            if user not in users:
                users.append(user)
        cursor = db.cursor()
        cursor.execute('''
            SELECT ondate, username, availability
            FROM team_availability
            WHERE project_id = %s
            AND ondate >= %s AND ondate <= %s
            AND username IN %s
        ''', (pid, from_date.isoformat(), to_date.isoformat(), tuple(users)))

        updates = []
        keys    = [(t[0], t[1]) for t in tuples]
        for row in cursor:
            key = (row[0], row[1])
            # If the whole db row is in tuples (date, person, and
            # availability match) take it out of tuples, we don't need
            # to do anything to the db
            if row in tuples:
                tuples.remove(row)
                keys.remove(key)
            # If the db key in this row has a value in tuples, we need
            # to update availability
            elif key in keys:
                index = keys.index(key)
                updates.append(tuples.pop(index))
                keys.pop(index)
            # The query results should cover the same date range as
            # tuples.  We might get here if tuples has more users than
            # the db.  We fall through and add any tuples that don't
            # match the DB so this is OK
            else:
                self.env.log.info('TeamCalendar: UI and DB inconsistent.')

        # Duplicates and updates have been removed from tuples so
        # what's left is things to insert.
        inserts = tuples

        @self.env.with_transaction()
        def do_insert_update(db):
            if len(inserts):
                insert_cursor = db.cursor()
                clause = ','.join(('(%s,%s,%s,%s)',) * len(inserts))
                inserts_ = [(t[0], t[1], t[2], pid) for t in inserts]
                # Quickly flatten the list.
                flat = [item for sublist in inserts_ for item in sublist]
                insert_cursor.execute('''
                    INSERT INTO team_availability
                        (ondate, username, availability, project_id)
                    VALUES %s''' % clause, flat)

            if len(updates):
                update_cursor = db.cursor()
                for t in updates:
                    update_cursor.execute('''
                        UPDATE team_availability
                        SET availability = %s
                        WHERE project_id = %s AND ondate = %s
                        AND username = %s
                    ''', (t[2], pid, t[0], t[1]))

    def find_default_start(self, weeks):
        today = date.today()
        offset = (today.isoweekday() - 1) + (7 * weeks)
        return today - timedelta(offset)

    def find_default_end(self, weeks):
        today = date.today()
        offset = (7 - today.isoweekday()) + (7 * weeks)
        return today + timedelta(offset)

