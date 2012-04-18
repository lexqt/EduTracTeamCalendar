from trac.db import Table, Column, ForeignKey, Constraint

name = 'teamcalendar'
version = 1

tables = [
    Table('team_availability', key=('username', 'project_id', 'ondate'))[
        Column('username', type='varchar (255)'),
        Column('project_id', type='int'),
        Column('ondate', type='date', default='CURRENT_DATE'),
        Column('availability', type='decimal(3, 2)', null=False, default='0.0'),
        ForeignKey('project_id', 'projects', 'id', on_delete='CASCADE'),
        ForeignKey('username', 'users', 'username', on_delete='CASCADE', on_update='CASCADE'),
        Constraint('CHECK (availability >= 0 AND availability <= 1)', 'availability_scale')
    ],
]
