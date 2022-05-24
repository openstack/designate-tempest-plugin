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

from designate_tempest_plugin.common import constants as const
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

        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
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
    credentials = ["primary", "admin", "system_admin", "alt"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesImportTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesImportTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.ZoneImportsClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.ZoneImportsClient()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.client = cls.os_primary.dns_v2.ZoneImportsClient()
        cls.alt_client = cls.os_alt.dns_v2.ZoneImportsClient()

    def clean_up_resources(self, zone_import_id):
        zone_import = self.client.show_zone_import(zone_import_id)[1]
        if zone_import['zone_id']:  # A zone was actually created.
            waiters.wait_for_zone_import_status(
                self.client, zone_import_id, const.COMPLETE)
            self.client.delete_zone_import(zone_import['id'])
            self.wait_zone_delete(self.zone_client, zone_import['zone_id'])
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
                        self.zone_client,
                        zone_import['zone_id'])

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
            "listed import IDs".format(
                zone_import['id'], listed_zone_import_ids))
