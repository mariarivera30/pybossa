# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2018 Scifabric LTD.
#
# PYBOSSA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PYBOSSA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with PYBOSSA.  If not, see <http://www.gnu.org/licenses/>.
"""Module with data access helper functions."""


def get_valid_project_levels_for_task(task):
    from pybossa.core import data_access_levels

    if not data_access_levels:
        return True

    task_level = (task.info or {}).get('data_access')
    return set(data_access_levels['valid_project_levels_for_task_level'].get(task_level, []))


def get_valid_task_levels_for_project(project):
    from pybossa.core import data_access_levels

    if not data_access_levels:
        return True

    assigned_project_levels = (project.info or {}).get('data_access', [])
    return set([
        level for apl in assigned_project_levels
        for level in data_access_levels['valid_task_levels_for_project_level'].get(apl, [])
    ])


def can_add_task_to_project(task, project):
    from pybossa.core import data_access_levels

    if not data_access_levels:
        return True

    task_levels = get_valid_project_levels_for_task(task)
    project_levels = get_valid_task_levels_for_project(project)
    return bool(task_levels & project_levels)


def valid_access_levels(levels):
    """check if levels are valid levels"""

    from pybossa.core import data_access_levels

    access_levels = data_access_levels['valid_access_levels']
    access_levels = [level[0] for level in access_levels]
    return [l for l in levels if l in access_levels] == levels


def can_assign_user(levels, user_levels):
    """check if user be assigned to an object(project/task) based on
    whether user_levels matches objects levels """

    from pybossa.core import data_access_levels

    if not data_access_levels:
        return True

    if not (valid_access_levels(levels) and valid_access_levels(user_levels)):
        return False

    access_levels = data_access_levels['valid_access_levels']
    access_levels = [level[0] for level in access_levels]

    valid_user_levels_for_project_task_level = data_access_levels['valid_user_levels_for_project_task_level']
    valid_project_task_levels_for_user_level = data_access_levels['valid_project_task_levels_for_user_level']

    all_user_levels = get_all_access_levels(user_levels, valid_project_task_levels_for_user_level)
    all_levels = get_all_access_levels(levels, valid_user_levels_for_project_task_level)
    return bool(all_levels.intersection(all_user_levels))


def get_all_access_levels(levels, implicit_levels):
    """based on access level for an object(project/task/user), obtain
    all access levels considering default_levels for an objects"""

    all_levels = set(levels)
    for level in levels:
        for dlevel in implicit_levels[level]:
            all_levels.add(dlevel)
    return all_levels


def get_data_access_db_clause(access_levels):

    from pybossa.core import data_access_levels

    if not valid_access_levels(access_levels):
        return

    valid_user_levels_for_project_task_level = data_access_levels['valid_user_levels_for_project_task_level']

    levels = set([level for level in access_levels])
    for level in access_levels:
        for dlevels in valid_user_levels_for_project_task_level.get(level):
            levels.add(dlevels)
    sql_clauses = [' info->\'data_access\' @> \'["{}"]\''.format(level) for level in levels]
    return ' OR '.join(sql_clauses)


def get_data_access_db_clause_for_task_assignment(user_id):

    from pybossa.core import data_access_levels
    from pybossa.cache.users import get_user_access_levels_by_id

    if not data_access_levels:
        return ''

    user_levels = get_user_access_levels_by_id(user_id)
    if not valid_access_levels(user_levels):
        raise Exception('Invalid user access level')

    valid_project_task_levels_for_user_level = data_access_levels['valid_project_task_levels_for_user_level']
    levels = set([level for level in user_levels])
    for level in user_levels:
        for dlevels in valid_project_task_levels_for_user_level.get(level):
            levels.add(dlevels)

    levels = ['\'\"{}\"\''.format(level) for level in levels]
    sql_clause = ' AND task.info->\'data_access\' @> ANY(ARRAY[{}]::jsonb[]) '.format(', '.join(levels))
    return sql_clause
