# -*- coding: utf8 -*-
# This file is part of PYBOSSA.
#
# Copyright (C) 2015 Scifabric LTD.
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


class ProjectAuth(object):
    _specific_actions = ['publish']

    def __init__(self, task_repo, result_repo):
        self.task_repo = task_repo
        self.result_repo = result_repo

    @property
    def specific_actions(self):
        return self._specific_actions

    @staticmethod
    def only_admin_or_subadminowner(user, project):
        return (user.is_authenticated() and
                (user.admin or
                    (user.subadmin and
                        user.id in project.owners_ids)))

    @staticmethod
    def only_admin_or_subadmin(user):
        return (user.is_authenticated() and
                (user.admin or user.subadmin))

    @staticmethod
    def only_project_users(user, project):
        return user.is_authenticated() and \
            user.id in project.info.get('project_users', [])

    def can(self, user, action, taskrun=None):
        action = ''.join(['_', action])
        return getattr(self, action)(user, taskrun)

    def _create(self, user, project=None):
        if project is not None and self.only_admin_or_subadmin(user):
            return project.published != True
        return self.only_admin_or_subadmin(user)

    def _read(self, user, project=None):
        from pybossa.core import data_access_levels

        if project is not None and project.published is False:
            return self.only_admin_or_subadminowner(user, project)
        if project is not None and data_access_levels:
            return self.only_admin_or_subadminowner(user, project) or \
                self.only_project_users(user, project)
        return user.is_authenticated()

    def _update(self, user, project):
        return self.only_admin_or_subadminowner(user, project)

    def _delete(self, user, project):
        if self.result_repo.get_by(project_id=project.id):
            return False
        return self.only_admin_or_subadminowner(user, project)

    def _publish(self, user, project):
        return (project.has_presenter() and
            len(self.task_repo.filter_tasks_by(project_id=project.id)) > 0 and
            self.only_admin_or_subadminowner(user, project))
