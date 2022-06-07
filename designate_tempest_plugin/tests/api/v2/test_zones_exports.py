# Copyright 2016 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.lib.common.utils import data_utils

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseZoneExportsTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                     'status', 'location']

    @classmethod
    def setup_clients(cls):
        super(BaseZoneExportsTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(BaseZoneExportsTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="BaseZoneExportsTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(BaseZoneExportsTest, cls).resource_cleanup()


class ZonesExportTest(BaseZoneExportsTest):
    credentials = ["primary", "admin", "system_admin", "system_reader", "alt",
                   "project_member", "project_reader"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesExportTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesExportTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.ZoneExportsClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.ZoneExportsClient()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.alt_zone_client = cls.os_alt.dns_v2.ZonesClient()
        cls.client = cls.os_primary.dns_v2.ZoneExportsClient()
        cls.alt_client = cls.os_alt.dns_v2.ZoneExportsClient()

    def _create_zone_export(self, test_name):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name=test_name, suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone export')
        zone_export = self.client.create_zone_export(zone['id'])[1]
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])
        waiters.wait_for_zone_export_status(
            self.client, zone_export['id'], const.COMPLETE)
        return zone, zone_export

    @decorators.idempotent_id('2dd8a9a0-98a2-4bf6-bb51-286583b30f40')
    def test_create_zone_export(self):
        zone, zone_export = self._create_zone_export('create_zone_export')

        LOG.info('Ensure we respond with PENDING')
        self.assertEqual(const.PENDING, zone_export['status'])

        # Test RBAC
        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')
            expected_allowed.append('os_project_member')

        self.check_CUD_RBAC_enforcement(
            'ZoneExportsClient', 'create_zone_export', expected_allowed, True,
            zone['id'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('2d29a2a9-1941-4b7e-9d8a-ad6c2140ea68')
    def test_show_zone_export(self):
        zone_export = self._create_zone_export('show_zone_export')[1]

        LOG.info('Re-Fetch the zone export')
        body = self.client.show_zone_export(zone_export['id'])[1]

        LOG.info('Ensure the fetched response matches the zone export')
        self.assertExpected(zone_export, body, self.excluded_keys)

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC
        expected_allowed = ['os_primary']

        self.check_list_show_RBAC_enforcement(
            'ZoneExportsClient', 'show_zone_export', expected_allowed, True,
            zone_export['id'])

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'ZoneExportsClient', 'show_zone_export', expected_allowed, True,
            zone_export['id'], headers=self.all_projects_header)

    @decorators.idempotent_id('fb04507c-9600-11eb-b1cd-74e5f9e2a801')
    def test_show_zone_export_impersonate_another_project(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name='show_zone_export_impersonate', suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone export using primary client')
        resp, zone_export = self.client.create_zone_export(zone['id'])
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])

        LOG.info('Impersonate "primary" client, to show created zone exports')
        body = self.admin_client.show_zone_export(uuid=None, headers={
            'x-auth-sudo-project-id': zone['project_id']})[1]['exports']
        listed_export_ids = [item['id'] for item in body]

        LOG.info('Ensure that the fetched response, contains the ID '
                 'for a zone export created by primary client.')
        self.assertIn(
            zone_export['id'], listed_export_ids,
            'Failed, expected ID:{} was not found in listed export zones '
            'for a primary client: {}'.format(
                zone_export['id'], listed_export_ids))

        # Test RBAC with x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'ZoneExportsClient', 'show_zone_export', expected_allowed, True,
            zone_export['id'],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('97234f00-8bcb-43f8-84dd-874f8bc4a80e')
    def test_delete_zone_export(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name='delete_zone_export', suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Create a zone export')
        _, zone_export = self.client.create_zone_export(zone['id'])

        # Test RBAC
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'ZoneExportsClient', 'delete_zone_export', expected_allowed, True,
            zone_export['id'])

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'ZoneExportsClient', 'delete_zone_export', expected_allowed, False,
            zone_export['id'], headers=self.all_projects_header)

        self.check_CUD_RBAC_enforcement(
            'ZoneExportsClient', 'delete_zone_export', expected_allowed, False,
            zone_export['id'],
            headers={'x-auth-sudo-project-id': self.client.project_id})

        LOG.info('Delete the zone export')
        _, body = self.client.delete_zone_export(zone_export['id'])

        LOG.info('Ensure the zone export has been successfully deleted')
        self.assertRaises(
            lib_exc.NotFound,
            self.client.show_zone_export, zone_export['id'])

    @decorators.idempotent_id('476bfdfe-58c8-46e2-b376-8403c0fff440')
    def test_list_zone_exports(self):
        export = self._create_zone_export('list_zone_exports')[1]

        LOG.info('List zone exports')
        body = self.client.list_zone_exports()[1]

        self.assertGreater(len(body['exports']), 0)

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC - Users that are allowed to call list, but should get
        #             zero zones.
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader',
                                'os_admin', 'os_project_member',
                                'os_project_reader']
        else:
            expected_allowed = ['os_alt']

        self.check_list_RBAC_enforcement_count(
            'ZoneExportsClient', 'list_zone_exports', expected_allowed, 0)

        # Test that users who should see the zone, can see it.
        expected_allowed = ['os_primary']

        self.check_list_IDs_RBAC_enforcement(
            'ZoneExportsClient', 'list_zone_exports',
            expected_allowed, [export['id']])

        # Test RBAC with x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'ZoneExportsClient', 'list_zone_exports',
            expected_allowed, [export['id']],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('f34e7f34-9613-11eb-b1cd-74e5f9e2a801')
    def test_list_zone_exports_all_projects(self):
        LOG.info('Create a primary zone and its export')
        zone_name = dns_data_utils.rand_zone_name(
            name='list_zone_exports_all_projects', suffix=self.tld_name)
        primary_zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(
            self.wait_zone_delete, self.zone_client, primary_zone['id'])
        primary_export = self.client.create_zone_export(primary_zone['id'])[1]
        self.addCleanup(self.client.delete_zone_export, primary_export['id'])

        LOG.info('Create an alt zone and its export')
        alt_zone_name = dns_data_utils.rand_zone_name(
            name='list_zone_exports_all_projects_alt', suffix=self.tld_name)
        alt_zone = self.alt_zone_client.create_zone(name=alt_zone_name)[1]
        self.addCleanup(
            self.wait_zone_delete, self.alt_zone_client, alt_zone['id'])
        alt_export = self.alt_client.create_zone_export(alt_zone['id'])[1]
        self.addCleanup(self.alt_client.delete_zone_export, alt_export['id'])

        LOG.info('As admin user list zone exports for all projects')
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        listed_exports_ids = [
            item['id'] for item in self.admin_client.list_zone_exports(
                headers=self.all_projects_header,
                params={'limit': 1000})[1]['exports']]

        LOG.info('Make sure that all previously created zone '
                 'export IDs are listed')
        for id in [primary_export['id'], alt_export['id']]:
            self.assertIn(
                id, listed_exports_ids,
                'Failed, expected ID:{} was not found in '
                'listed IDs:{}'.format(id, listed_exports_ids))

        # Test RBAC with x-auth-all-projects
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'ZoneExportsClient', 'list_zone_exports', expected_allowed,
            [alt_export['id']], headers=self.all_projects_header)

    @decorators.idempotent_id('e4a11a14-9aaa-11eb-be59-74e5f9e2a801')
    def test_list_zone_exports_filter_results(self):

        LOG.info('Create a primary zone and its export')
        zone_name = dns_data_utils.rand_zone_name(
            name='list_zone_exports_filter', suffix=self.tld_name)
        primary_zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(
            self.wait_zone_delete, self.zone_client, primary_zone['id'])
        primary_export = self.client.create_zone_export(primary_zone['id'])[1]
        self.addCleanup(self.client.delete_zone_export, primary_export['id'])

        LOG.info('Create an alt zone, its export and delete it')
        zone_name = dns_data_utils.rand_zone_name(
            name='list_zone_exports_filter_alt', suffix=self.tld_name)
        alt_zone = self.alt_zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(
            self.wait_zone_delete, self.alt_zone_client, alt_zone['id'])
        alt_export = self.alt_client.create_zone_export(alt_zone['id'])[1]
        self.alt_client.delete_zone_export(alt_export['id'])
        LOG.info('Ensure the zone export has been successfully deleted')
        self.assertRaises(
            lib_exc.NotFound,
            self.alt_client.show_zone_export,
            alt_export['id'])

        LOG.info('Filter out "export zones" in status:ZAHLABUT,'
                 ' expected: empty list')
        self.assertEqual(
            [], self.admin_client.list_zone_exports(
                headers=self.all_projects_header,
                params={'status': 'ZAHLABUT'})[1]['exports'],
            'Failed, filtered result is expected to be empty.')

        LOG.info('Filter out "export zones" with message:ZABABUN,'
                 ' expected: empty list')
        self.assertEqual(
            [], self.admin_client.list_zone_exports(
                headers=self.all_projects_header,
                params={'message': 'ZABABUN'})[1]['exports'],
            'Failed, filtered result is expected to be empty.')

        LOG.info('Filter out "export zones" that have been created for '
                 'a primary zone. Expected: single zone export is listed')
        self.assertEqual(
            1, len(self.admin_client.list_zone_exports(
                headers=self.all_projects_header,
                params={'zone_id': primary_zone['id']})[1]['exports']),
            'Failed, filtered result should contain a single zone '
            '(primary zone export)')

        LOG.info('Filter out "export zones" that have been created for '
                 'an alt zone expected: empty list (it was deleted)')
        self.assertEqual(
            [], self.admin_client.list_zone_exports(
                headers=self.all_projects_header,
                params={'zone_id': alt_zone['id']})[1]['exports'],
            'Failed, filtered result should be empty.')


class ZonesExportTestNegative(BaseZoneExportsTest):
    credentials = ["primary", "alt", "admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesExportTestNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesExportTestNegative, cls).setup_clients()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.client = cls.os_primary.dns_v2.ZoneExportsClient()
        cls.alt_client = cls.os_alt.dns_v2.ZoneExportsClient()

    def _create_zone_export(self, test_name):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(name=test_name,
                                                  suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone export')
        zone_export = self.client.create_zone_export(zone['id'])[1]
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])
        waiters.wait_for_zone_export_status(
            self.client, zone_export['id'], const.COMPLETE)
        return zone, zone_export

    @decorators.idempotent_id('76ab8ec4-95fd-11eb-b1cd-74e5f9e2a801')
    def test_create_zone_export_using_invalid_zone_id(self):
        self.assertRaises(
            lib_exc.NotFound, self.client.create_zone_export,
            'e35bc796-9841-11eb-898b-74e5f9e2a801')

    @decorators.idempotent_id('943dad4a-9617-11eb-b1cd-74e5f9e2a801')
    def test_export_not_your_zone(self):
        LOG.info('Create a primary zone.')
        zone_name = dns_data_utils.rand_zone_name(name='export_not_your_zone',
                                                  suffix=self.tld_name)
        primary_zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(
            self.wait_zone_delete, self.zone_client, primary_zone['id'])

        LOG.info('Make sure that "404 NotFound" status code is raised.')
        self.assertRaises(
            lib_exc.NotFound, self.alt_client.create_zone_export,
            primary_zone['id'])

    @decorators.idempotent_id('518dc308-9604-11eb-b1cd-74e5f9e2a801')
    def test_create_zone_export_using_deleted_zone(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(name='export_deleted_zone',
                                                  suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)
        LOG.info("Delete the zone and wait till it's done.")
        self.zone_client.delete_zone(zone['id'])[1]
        self.wait_zone_delete(self.zone_client, zone['id'])

        LOG.info('Ensure we respond with NotFound exception')
        self.assertRaises(
            lib_exc.NotFound, self.client.create_zone_export, zone['id'])

    @decorators.idempotent_id('9a878646-f66b-4fa4-ae95-f3ac3f8e3d31')
    def test_show_zonefile_using_not_existing_zone_export_id(self):
        LOG.info('Expected: 404 Not Found zone export')
        self.assertRaises(lib_exc.NotFound,
                          self.client.show_exported_zonefile,
                          data_utils.rand_uuid())

    @decorators.idempotent_id('52a1fee0-c338-4ed9-b9f9-41ee7fd73375')
    def test_show_zonefile_not_supported_accept_value(self):
        zone, zone_export = self._create_zone_export(
            'show_zonefile_bad_accept')
        # Tempest-lib _error_checker will raise UnexpectedResponseCode
        e = self.assertRaises(
            lib_exc.UnexpectedResponseCode, self.client.show_exported_zonefile,
            zone_export['id'], headers={'Accept': 'image/jpeg'})
        self.assertEqual(406, e.resp.status,
                         "Failed, actual response code is:{0}"
                         "but expected is: 406".format(e.resp.status))
