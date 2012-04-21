from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.db import DatabaseManager

from trac.util.translation import domain_functions

import db_default


__all__ = ['TeamCalendarSetupParticipant']

_, tag_, N_, add_domain = \
    domain_functions('teamcalendar', ('_', 'tag_', 'N_', 'add_domain'))


class TeamCalendarSetupParticipant(Component):

    implements(IEnvironmentSetupParticipant)

    def __init__(self):
        import pkg_resources
        locale_dir = pkg_resources.resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    # IEnvironmentSetupParticipant

    def environment_created(self):
        pass
        
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name=%s", (db_default.name,))
        value = cursor.fetchone()
        if not value:
            self.db_version = 0
            return True
        else:
            self.db_version = int(value[0])
            if self.db_version < db_default.version:
                return True
                
        return False
            
    def upgrade_environment(self, db):
        db_manager, _ = DatabaseManager(self.env)._get_connector()
                
        cursor = db.cursor()
        if not self.db_version:
            cursor.execute("INSERT INTO system (name, value) VALUES (%s, %s)",(db_default.name, db_default.version))
        else:
            cursor.execute("UPDATE system SET value=%s WHERE name=%s",(db_default.version, db_default.name))

        for tbl in db_default.tables:
            for sql in db_manager.to_sql(tbl):
                cursor.execute(sql)

