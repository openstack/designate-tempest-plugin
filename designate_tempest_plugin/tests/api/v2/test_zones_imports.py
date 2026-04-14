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

import testtools

from oslo_log import log as logging
from oslo_utils import versionutils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import pool_config
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseZonesImportTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                     'status', 'message', 'zone_id']

    @classmethod
    def setup_clients(cls):
        super(BaseZonesImportTest, cls).setup_clients()
        cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(BaseZonesImportTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="BaseZonesImportTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(BaseZonesImportTest, cls).resource_cleanup()


class ZonesImportTest(BaseZonesImportTest):
    credentials = ["primary", "admin", "alt",
                   "project_member", "project_reader"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesImportTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesImportTest, cls).setup_clients()
        cls.admin_client = cls.os_admin.dns_v2.ZoneImportsClient()
        cls.client = cls.os_primary.dns_v2.ZoneImportsClient()
        cls.alt_client = cls.os_alt.dns_v2.ZoneImportsClient()

    def clean_up_resources(self, zone_import_id):
        zone_import = self.client.show_zone_import(zone_import_id)[1]
        if zone_import['zone_id']:  # A zone was actually created.
            waiters.wait_for_zone_import_status(
                self.client, zone_import_id, const.COMPLETE)
            self.client.delete_zone_import(zone_import['id'])
            self.wait_zone_delete(self.zones_client, zone_import['zone_id'])
        else:  # Import has failed and zone wasn't created.
            self.client.delete_zone_import(zone_import['id'])

    @decorators.idempotent_id('2e2d907d-0609-405b-9c96-3cb2b87e3dce')
    def test_create_zone_import(self):
        LOG.info('Create a zone import')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_zone_import", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name)
        zone_import = self.client.create_zone_import(
            zonefile_data=zone_data)[1]
        self.addCleanup(self.clean_up_resources, zone_import['id'])
        # Make sure we complete the import and have the zone_id for cleanup
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], const.COMPLETE)

        # Test with no extra header overrides (sudo-project-id)
        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_project_member')

        self.check_CUD_RBAC_enforcement(
            'ZoneImportsClient', 'create_zone_import', expected_allowed, False)

    @decorators.idempotent_id('31eaf25a-9532-11eb-a55d-74e5f9e2a801')
    def test_create_zone_import_invalid_ttl(self):
        LOG.info('Try to create a zone import using invalid TTL value')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_zone_import_invalid_ttl", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name,
                                                      ttl='zahlabut')
        zone_import = self.client.create_zone_import(
            zonefile_data=zone_data)[1]
        self.addCleanup(self.clean_up_resources, zone_import['id'])
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], "ERROR")

    @decorators.idempotent_id('31eaf25a-9532-11eb-a55d-74e5f9e2a801')
    def test_create_zone_import_invalid_name(self):
        LOG.info('Try to create a zone import using invalid name')
        zone_import = self.client.create_zone_import(
            zonefile_data=dns_data_utils.rand_zonefile_data(name='@@@'))[1]
        self.addCleanup(self.clean_up_resources, zone_import['id'])
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], "ERROR")

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('c8909558-0dc6-478a-9e91-eb97b52e59e0')
    def test_show_zone_import(self):
        LOG.info('Create a zone import')
        zone_name = dns_data_utils.rand_zone_name(
            name="show_zone_import", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name)
        zone_import = self.client.create_zone_import(
            zonefile_data=zone_data)[1]
        self.addCleanup(self.clean_up_resources, zone_import['id'])
        # Make sure we complete the import and have the zone_id for cleanup
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], const.COMPLETE)

        LOG.info('Re-Fetch the zone import')
        resp, body = self.client.show_zone_import(zone_import['id'])

        LOG.info('Ensure the fetched response matches the expected one')
        self.assertExpected(zone_import, body, self.excluded_keys)

        # Test with no extra header overrides (all_projects, sudo-project-id)
        expected_allowed = ['os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.extend(['os_project_member',
                                     'os_project_reader'])

        self.check_list_show_RBAC_enforcement(
            'ZoneImportsClient', 'show_zone_import', expected_allowed, True,
            zone_import['id'])

        # Test with x-auth-all-projects
        expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'ZoneImportsClient', 'show_zone_import', expected_allowed, False,
            zone_import['id'], headers=self.all_projects_header)

    @decorators.idempotent_id('56a16e68-b241-4e41-bc5c-c40747fa68e3')
    def test_delete_zone_import(self):
        LOG.info('Create a zone import')
        zone_name = dns_data_utils.rand_zone_name(
            name="delete_zone_import", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name)
        zone_import = self.client.create_zone_import(
            zonefile_data=zone_data)[1]
        waiters.wait_for_zone_import_status(self.client, zone_import['id'],
                                            const.COMPLETE)
        zone_import = self.client.show_zone_import(zone_import['id'])[1]
        self.addCleanup(self.wait_zone_delete,
                        self.zones_client,
                        zone_import['zone_id'])

        # Test RBAC
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.extend(['os_project_member'])

        self.check_CUD_RBAC_enforcement(
            'ZoneImportsClient', 'delete_zone_import', expected_allowed, True,
            zone_import['id'])

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.extend(['os_project_member'])

        self.check_CUD_RBAC_enforcement(
            'ZoneImportsClient', 'delete_zone_import', expected_allowed, False,
            zone_import['id'], headers=self.all_projects_header)
        self.check_CUD_RBAC_enforcement(
            'ZoneImportsClient', 'delete_zone_import', expected_allowed, False,
            zone_import['id'],
            headers={'x-auth-sudo-project-id': self.client.project_id})

        LOG.info('Delete the zone')
        resp, body = self.client.delete_zone_import(zone_import['id'])

        LOG.info('Ensure successful deletion of imported zones')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.show_zone_import(zone_import['id']))

    @decorators.idempotent_id('9eab76af-1995-485f-a2ef-8290c1863aba')
    def test_list_zones_imports(self):
        LOG.info('Create a zone import')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_zone_imports", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name)
        zone_import = self.client.create_zone_import(
            zonefile_data=zone_data)[1]
        self.addCleanup(self.clean_up_resources, zone_import['id'])
        # Make sure we complete the import and have the zone_id for cleanup
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], const.COMPLETE)

        LOG.info('List zones imports')
        body = self.client.list_zone_imports()[1]

        self.assertGreater(len(body['imports']), 0)

        # Test RBAC - Users that are allowed to call list, but should get
        #             zero zones.
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_admin']
        else:
            expected_allowed = ['os_alt']

        self.check_list_RBAC_enforcement_count(
            'ZoneImportsClient', 'list_zone_imports', expected_allowed, 0)

        # Test that users who should see the zone, can see it.
        expected_allowed = ['os_primary']

        self.check_list_IDs_RBAC_enforcement(
            'ZoneImportsClient', 'list_zone_imports', expected_allowed,
            [zone_import['id']])

        # Test RBAC with x-auth-sudo-project-id header
        expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'ZoneImportsClient', 'list_zone_imports', expected_allowed,
            [zone_import['id']],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('2c1fa20e-9554-11eb-a55d-74e5f9e2a801')
    def test_show_import_impersonate_another_project(self):

        LOG.info('Import zone "A" using primary client')
        zone_name = dns_data_utils.rand_zone_name(
            name="show_zone_import_impersonate", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name)
        zone_import = self.client.create_zone_import(
            zonefile_data=zone_data)[1]
        self.addCleanup(self.clean_up_resources, zone_import['id'])

        # Make sure we complete the import and have the zone_id for cleanup
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], const.COMPLETE)

        LOG.info('Show a zone import for a Primary tenant, using Alt tenant. '
                 'Expected:404 NotFound')
        self.assertRaises(lib_exc.NotFound,
                          lambda: self.alt_client.show_zone_import(
                              zone_import['id']))

        LOG.info('Show a zone import for a Primary tenant using Alt tenant '
                 'and "x-auth-sudo-project-id" HTTP header. '
                 'Expected:403 Forbidden')
        self.assertRaises(
            lib_exc.Forbidden,
            lambda: self.alt_client.show_zone_import(
                zone_import['id'],
                headers={'x-auth-sudo-project-id': zone_import[
                    'project_id']}))

        LOG.info('Show a zone import for a Primary tenant, using Admin '
                 'tenant and "x-auth-sudo-project-id" HTTP header.')
        resp_body = self.admin_client.show_zone_import(uuid=None, headers={
                'x-auth-sudo-project-id': zone_import['project_id']})[1]

        LOG.info('Show a zone import for a Primary tenant, using Admin '
                 'tenant without "x-auth-sudo-project-id" HTTP header. '
                 'Expected:404 NotFound')
        self.assertRaises(
            lib_exc.NotFound, lambda: self.admin_client.show_zone_import(
                zone_import['id']))

        LOG.info('Ensure that the shown response matches the expected one')
        self.assertExpected(
            zone_import, resp_body['imports'][0], self.excluded_keys)

        # Test with x-auth-sudo-project-id header
        expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'ZoneImportsClient', 'show_zone_import', expected_allowed, False,
            zone_import['id'],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('7bd06ec6-9556-11eb-a55d-74e5f9e2a801')
    def test_list_import_zones_all_projects(self):
        LOG.info('Create import zone "A" using primary client')
        zone_name = dns_data_utils.rand_zone_name(
            name="_zone_imports_all_projects", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name)
        zone_import = self.client.create_zone_import(
            zonefile_data=zone_data)[1]
        self.addCleanup(self.clean_up_resources, zone_import['id'])
        # Make sure we complete the import and have the zone_id for cleanup
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], const.COMPLETE)

        LOG.info('As Alt user list import zones for a Primary tenant, '
                 'using "x-auth-sudo-project-id" HTTP header. '
                 'Expected: 403 Forbidden')
        self.assertRaises(
            lib_exc.Forbidden, lambda: self.alt_client.list_zone_imports(
                headers={
                    'x-auth-sudo-project-id': zone_import['project_id']}))

        LOG.info('As Alt tenant list zone imports for all projects, using '
                 '"x-auth-all-projects" HTTP header, Expected: 403 Forbidden')
        self.assertRaises(
            lib_exc.Forbidden, lambda: self.alt_client.list_zone_imports(
                headers=self.all_projects_header))

        LOG.info('As Admin tenant list import zones for all projects')
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        body = self.admin_client.list_zone_imports(
            headers=self.all_projects_header,
            params={'limit': 1000})[1]['imports']

        LOG.info('Ensure the fetched response includes previously '
                 'created import ID')
        listed_zone_import_ids = [item['id'] for item in body]
        self.assertIn(
            zone_import['id'], listed_zone_import_ids,
            "Failed, expected import ID:{} wasn't found in "
            "listed import IDs".format(zone_import['id']))

        # Test RBAC with x-auth-all-projects
        expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'ZoneImportsClient', 'list_zone_imports', expected_allowed,
            [zone_import['id']], headers=self.all_projects_header)

    @decorators.idempotent_id('a1b2c3d4-1234-5678-9abc-def012345678')
    def test_create_zone_import_json(self):
        if not versionutils.is_compatible('2.3', self.api_version,
                                          same_major=False):
            raise self.skipException(
                'JSON zone import tests require Designate API version '
                '2.3 or newer.')
        LOG.info('Create a zone import using application/json content type')
        zone_name = dns_data_utils.rand_zone_name(
            name="import_json", suffix=self.tld_name)
        zonefile = dns_data_utils.rand_zonefile_data(name=zone_name)

        # attributes={} triggers JSON mode without adding any attributes
        zone_import = self.client.create_zone_import(
            zonefile_data=zonefile, attributes={})[1]
        self.addCleanup(self.clean_up_resources, zone_import['id'])
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], const.COMPLETE)

        zone_import = self.client.show_zone_import(zone_import['id'])[1]
        self.assertEqual(const.COMPLETE, zone_import['status'])

    @decorators.idempotent_id('b2c3d4e5-2345-6789-abcd-ef0123456789')
    @testtools.skipIf(
        CONF.dns_feature_enabled.test_multipool_with_delete_opt,
        'Multipools feature is being tested with --delete option.')
    def test_create_zone_import_with_pool_attribute(self):
        if not versionutils.is_compatible('2.3', self.api_version,
                                          same_major=False):
            raise self.skipException(
                'JSON zone import tests require Designate API version '
                '2.3 or newer.')
        LOG.info('Test zone import with pool_id attribute targets'
                 ' correct pool')
        target_pool_id = pool_config.get_non_default_pool_id()
        if not target_pool_id:
            raise self.skipException(
                'A non-default pool is required to test pool routing '
                'via attributes')

        zone_name = dns_data_utils.rand_zone_name(
            name="import_pool_attribute", suffix=self.tld_name)
        zonefile = dns_data_utils.rand_zonefile_data(name=zone_name)

        # zone_create_forced_pool policy requires admin privileges
        zone_import = self.admin_client.create_zone_import(
            zonefile_data=zonefile,
            attributes={'pool_id': target_pool_id})[1]
        waiters.wait_for_zone_import_status(
            self.admin_client, zone_import['id'], const.COMPLETE)

        zone_import = self.admin_client.show_zone_import(
            zone_import['id'])[1]

        admin_zones_client = self.os_admin.dns_v2.ZonesClient()
        self.addCleanup(self.wait_zone_delete,
                        admin_zones_client, zone_import['zone_id'])
        self.addCleanup(self.admin_client.delete_zone_import,
                        zone_import['id'])

        LOG.info('Verify the zone was assigned to the correct pool')
        self.assertEqual(const.COMPLETE, zone_import['status'])
        zone = admin_zones_client.show_zone(zone_import['zone_id'])[1]
        self.assertEqual(target_pool_id, zone['pool_id'])


class ZonesImportTestNegative(BaseZonesImportTest):
    credentials = ["primary", "admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesImportTestNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesImportTestNegative, cls).setup_clients()
        cls.client = cls.os_primary.dns_v2.ZoneImportsClient()

    def _clean_up_resources(self, zone_import_id):
        zone_import = self.client.show_zone_import(zone_import_id)[1]
        if zone_import['zone_id']:  # A zone was actually created.
            waiters.wait_for_zone_import_status(
                self.client, zone_import_id, const.COMPLETE)
            self.client.delete_zone_import(zone_import['id'])
            self.wait_zone_delete(self.zones_client, zone_import['zone_id'])
        else:  # Import has failed and zone wasn't created.
            self.client.delete_zone_import(zone_import['id'])

    @decorators.idempotent_id('31eaf25a-9532-11eb-a55d-74e5f9e2a801')
    def test_create_zone_import_invalid_ttl(self):
        LOG.info('Try to create a zone import using invalid TTL value')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_zone_import_invalid_ttl", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name,
                                                      ttl='zahlabut')
        zone_import = self.client.create_zone_import(
            zonefile_data=zone_data, wait_until=const.ERROR)[1]
        self.addCleanup(self._clean_up_resources, zone_import['id'])

    @decorators.idempotent_id('31eaf25a-9532-11eb-a55d-74e5f9e2a801')
    def test_create_zone_import_invalid_name(self):
        LOG.info('Try to create a zone import using invalid name')
        zone_import = self.client.create_zone_import(
            zonefile_data=dns_data_utils.rand_zonefile_data(
                name='@@@'), wait_until=const.ERROR)[1]
        self.addCleanup(self._clean_up_resources, zone_import['id'])

    @decorators.idempotent_id('8fd744d2-9dff-11ec-9fb6-201e8823901f')
    def test_create_zone_import_invalid_file_data(self):
        LOG.info('Try to create a zone import using random generated'
                 ' import file data')
        zone_file_data = dns_data_utils.rand_string(size=100)
        zone_import = self.client.create_zone_import(zone_file_data)[1]
        self.addCleanup(self.client.delete_zone_import, zone_import['id'])
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], const.ERROR)

    @decorators.idempotent_id('4fb9494e-9e23-11ec-8378-201e8823901f')
    def test_zone_cannot_be_update_by_import(self):
        LOG.info('Create a Zone named: "...zone_to_update..."')
        zone_name = dns_data_utils.rand_zone_name(
            name='zone_to_update', suffix=self.tld_name)
        zone = self.zones_client.create_zone(
            name=zone_name, wait_until=const.ACTIVE)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'])
        LOG.info('Use zone import to update an existing zone, expected: zone'
                 ' import gets into the ERROR status ')
        zone_import_data = dns_data_utils.rand_zonefile_data(name=zone_name)
        zone_import = self.client.create_zone_import(zone_import_data)[1]
        waiters.wait_for_zone_import_status(
            self.client, zone_import['id'], const.ERROR)
        self.addCleanup(self._clean_up_resources, zone_import['id'])

    @decorators.idempotent_id('5fa8016e-6ed1-11ec-9bd7-201e8823901f')
    def test_create_zone_import_invalid_content_type(self):
        LOG.info('Try to create a zone import using: "Content-Type:Zahlabut"'
                 ' HTTP header in POST request')
        with self.assertRaisesDns(
                lib_exc.InvalidContentType, 'unsupported_content_type', 415):
            self.client.create_zone_import(
                headers={'Content-Type': 'Zahlabut'})

    @decorators.idempotent_id('d4e5f6a7-4567-89ab-cdef-012345678901')
    def test_create_zone_import_invalid_json_body(self):
        if not versionutils.is_compatible('2.3', self.api_version,
                                          same_major=False):
            raise self.skipException(
                'JSON zone import tests require Designate API version '
                '2.3 or newer.')
        LOG.info('Try to create a zone import with invalid JSON body')
        self.assertRaises(
            (lib_exc.BadRequest, lib_exc.InvalidContentType),
            self.client.create_zone_import,
            zonefile_data='not valid json{{{',
            headers={'Content-Type': 'application/json'})

    @decorators.idempotent_id('e5f6a7b8-5678-9abc-def0-123456789abc')
    def test_create_zone_import_json_missing_zonefile(self):
        if not versionutils.is_compatible('2.3', self.api_version,
                                          same_major=False):
            raise self.skipException(
                'JSON zone import tests require Designate API version '
                '2.3 or newer.')
        LOG.info('Try to create a zone import with JSON body missing '
                 'the required zonefile field')
        self.assertRaises(
            lib_exc.BadRequest,
            self.client.create_zone_import,
            zonefile_data='{"attributes": {"pool_id": "fake-id"}}',
            headers={'Content-Type': 'application/json'})

    @decorators.idempotent_id('f6a7b8c9-6789-abcd-ef01-23456789abcd')
    def test_create_zone_import_json_invalid_pool_id(self):
        if not versionutils.is_compatible('2.3', self.api_version,
                                          same_major=False):
            raise self.skipException(
                'JSON zone import tests require Designate API version '
                '2.3 or newer.')
        LOG.info('Try to create a zone import with a non-existent pool_id')
        zone_name = dns_data_utils.rand_zone_name(
            name="import_invalid_pool", suffix=self.tld_name)
        zonefile = dns_data_utils.rand_zonefile_data(name=zone_name)
        self.assertRaises(
            lib_exc.NotFound,
            self.client.create_zone_import,
            zonefile_data=zonefile,
            attributes={
                'pool_id': '00000000-0000-0000-0000-000000000000'
            })
