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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class BaseZonesImportTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                     'status', 'message', 'zone_id']


class ZonesImportTest(BaseZonesImportTest):
    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesImportTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesImportTest, cls).setup_clients()

        cls.client = cls.os_primary.zone_imports_client
        cls.zone_client = cls.os_primary.zones_client

    def clean_up_resources(self, zone_import_id):
        waiters.wait_for_zone_import_status(self.client, zone_import_id,
                                            "COMPLETE")
        _, zone_import = self.client.show_zone_import(zone_import_id)
        self.client.delete_zone_import(zone_import['id'])
        self.wait_zone_delete(self.zone_client, zone_import['zone_id'])

    @decorators.idempotent_id('2e2d907d-0609-405b-9c96-3cb2b87e3dce')
    def test_create_zone_import(self):
        LOG.info('Create a zone import')
        _, zone_import = self.client.create_zone_import()
        self.addCleanup(self.clean_up_resources, zone_import['id'])

        LOG.info('Ensure we respond with PENDING')
        self.assertEqual('PENDING', zone_import['status'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('c8909558-0dc6-478a-9e91-eb97b52e59e0')
    def test_show_zone_import(self):
        LOG.info('Create a zone import')
        _, zone_import = self.client.create_zone_import()
        self.addCleanup(self.clean_up_resources, zone_import['id'])

        LOG.info('Re-Fetch the zone import')
        resp, body = self.client.show_zone_import(zone_import['id'])

        LOG.info('Ensure the fetched response matches the expected one')
        self.assertExpected(zone_import, body, self.excluded_keys)

    @decorators.idempotent_id('56a16e68-b241-4e41-bc5c-c40747fa68e3')
    def test_delete_zone_import(self):
        LOG.info('Create a zone import')
        _, zone_import = self.client.create_zone_import()
        waiters.wait_for_zone_import_status(self.client, zone_import['id'],
                                            "COMPLETE")
        _, zone_import = self.client.show_zone_import(zone_import['id'])
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
        _, zone_import = self.client.create_zone_import()
        self.addCleanup(self.clean_up_resources, zone_import['id'])

        LOG.info('List zones imports')
        _, body = self.client.list_zone_imports()

        self.assertGreater(len(body['imports']), 0)
