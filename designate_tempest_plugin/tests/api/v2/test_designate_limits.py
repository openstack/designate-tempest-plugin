# Copyright 2021 Red Hat.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


from designate_tempest_plugin.tests import base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class DesignateLimit(base.BaseDnsV2Test):
    credentials = ["admin", "system_admin", "system_reader", "primary", "alt",
                   "project_member", "project_reader"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(DesignateLimit, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(DesignateLimit, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = (cls.os_system_admin.dns_v2.
                                DesignateLimitClient())
        else:
            cls.admin_client = cls.os_admin.dns_v2.DesignateLimitClient()
        cls.primary_client = cls.os_primary.dns_v2.DesignateLimitClient()
        cls.alt_client = cls.os_alt.dns_v2.DesignateLimitClient()

    @decorators.idempotent_id('828572be-8662-11eb-8ff2-74e5f9e2a801')
    def test_list_designate_limits_as_primary_user(self):
        expected_default_limits_fields = [
            "max_page_limit", "max_recordset_name_length",
            "max_recordset_records", "max_zone_name_length",
            "max_zone_records", "max_zone_recordsets",
            "max_zones", "min_ttl"].sort()
        project_limits = self.primary_client.list_designate_limits()
        LOG.info(
            'Retrieved designate limits are: {} '.format(project_limits))
        self.assertEqual(
            expected_default_limits_fields,
            list(project_limits.keys()).sort(),
            'Retrieved fields: {} are not as expected: {} '.format(
                list(project_limits.keys()).sort(),
                expected_default_limits_fields))

    @decorators.idempotent_id('828572be-8662-11eb-8ff2-74e5f9e2a801')
    def test_list_designate_impersonate_another_user_as_admin(self):
        primary_project_limits = self.primary_client.list_designate_limits()
        LOG.info(
            'Retrieved designate limits for Primary user are: {} '.format(
                primary_project_limits))
        admin_sudo_project_limits = self.admin_client.list_designate_limits(
            headers={'x-auth-sudo-project-id': self.primary_client.project_id})
        LOG.info(
            'Retrieved designate limits for Admin user impersonates '
            'Primary user are: {} '.format(admin_sudo_project_limits))
        self.assertEqual(
            primary_project_limits, admin_sudo_project_limits,
            'Failed, Admin user should receive the same values for '
            'Designate limits as a Primary tenant did.')

    @decorators.idempotent_id('5975fee0-d430-11eb-aa4d-74e5f9e2a801')
    def test_list_designate_impersonate_another_user_as_alt(self):
        self.assertRaises(
            lib_exc.Forbidden, self.alt_client.list_designate_limits,
            headers={'x-auth-sudo-project-id': self.primary_client.project_id})

    @decorators.idempotent_id('828572be-8662-11eb-8ff2-74e5f9e2a801')
    @decorators.skip_because(bug="1933444")
    def test_list_designate_limits_all_projects(self):
        existing_project_ids = [
            self.primary_client.project_id, self.alt_client.project_id]
        LOG.info('Project IDs we would expect to receive with Admin user '
                 'uses: "x-auth-all-projects" HTTP header '
                 'are {}: '.format(existing_project_ids))
        all_project_limits = self.admin_client.list_designate_limits(
            headers={'x-auth-all-projects': True})
        LOG.info(
            'Retrieved designate limits by Admin user for all projects '
            'are: '.format(all_project_limits))
        received_project_ids = [
            item['project_id'] for item in all_project_limits]
        for project_id in existing_project_ids:
            self.assertIn(
                project_id, received_project_ids,
                'Failed, expected project_id:{} is missing in:{} '.format(
                    project_id, received_project_ids))

    @decorators.idempotent_id('fc57fa6b-5280-4186-9be9-ff4da0961db0')
    def test_list_designate_limits_RBAC(self):
        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.extend(['os_system_admin', 'os_system_reader',
                                     'os_project_member', 'os_project_reader'])

        self.check_list_show_RBAC_enforcement(
            'DesignateLimitClient', 'list_designate_limits',
            expected_allowed, False)
