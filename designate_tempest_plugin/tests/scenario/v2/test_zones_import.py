# Copyright 2016 Rackspace
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
from oslo_utils import versionutils
from tempest.lib import decorators

from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import pool_config
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests.api.v2.test_zones_imports import (
    BaseZonesImportTest)

LOG = logging.getLogger(__name__)


class ZonesImportTest(BaseZonesImportTest):

    credentials = ["primary", "admin"]

    @classmethod
    def setup_clients(cls):
        super(ZonesImportTest, cls).setup_clients()

        cls.client = cls.os_primary.dns_v2.ZoneImportsClient()

    @decorators.attr(type='slow')
    @decorators.idempotent_id('679f38d0-2f2f-49c5-934e-8fe0c452f56e')
    def test_create_zone_import_and_wait_for_zone(self):
        zone_name = dns_data_utils.rand_zone_name(
            name="create_zone_import_and_wait_for_zone", suffix=self.tld_name)
        zonefile = dns_data_utils.rand_zonefile_data(name=zone_name)

        LOG.info('Import zone %r', zone_name)
        zone_import = self.client.create_zone_import(
            zonefile, wait_until=const.COMPLETE)[1]
        self.addCleanup(self.client.delete_zone_import, zone_import['id'])

        LOG.info('Check the zone import looks good')
        zone_import = self.client.show_zone_import(zone_import['id'])[1]
        self.addCleanup(self.wait_zone_delete,
                        self.zones_client,
                        zone_import['zone_id'])

        self.assertEqual(const.COMPLETE, zone_import['status'])
        self.assertIsNotNone(zone_import['zone_id'])
        self.assertIsNotNone(zone_import['links'].get('zone'))

        LOG.info('Wait for the imported zone to go to ACTIVE')
        waiters.wait_for_zone_status(
            self.zones_client, zone_import['zone_id'], const.ACTIVE)

        LOG.info('Check the imported zone looks good')
        zone = self.zones_client.show_zone(zone_import['zone_id'])[1]
        self.assertEqual(const.NONE, zone['action'])
        self.assertEqual(const.ACTIVE, zone['status'])
        self.assertEqual(zone_name, zone['name'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('e5f6a7b8-5678-9abc-def0-123456789012')
    def test_create_zone_import_with_pool_attribute_and_wait_for_zone(self):
        if not versionutils.is_compatible('2.3', self.api_version,
                                          same_major=False):
            raise self.skipException(
                'JSON zone import tests require Designate API version '
                '2.3 or newer.')
        target_pool_id = pool_config.get_non_default_pool_id()
        if not target_pool_id:
            raise self.skipException(
                'A non-default pool is required to test zone import '
                'with pool_id attribute')

        zone_name = dns_data_utils.rand_zone_name(
            name="import_pool_attr_wait_for_zone", suffix=self.tld_name)
        zonefile = dns_data_utils.rand_zonefile_data(name=zone_name)

        # zone_create_forced_pool policy requires admin privileges
        admin_client = self.os_admin.dns_v2.ZoneImportsClient()
        admin_zones_client = self.os_admin.dns_v2.ZonesClient()

        LOG.info('Import zone %r with pool_id attribute targeting '
                 'pool %s', zone_name, target_pool_id)
        zone_import = admin_client.create_zone_import(
            zonefile, attributes={'pool_id': target_pool_id},
            wait_until=const.COMPLETE)[1]
        self.addCleanup(admin_client.delete_zone_import, zone_import['id'])

        LOG.info('Check the zone import looks good')
        zone_import = admin_client.show_zone_import(zone_import['id'])[1]
        self.addCleanup(self.wait_zone_delete,
                        admin_zones_client,
                        zone_import['zone_id'])

        self.assertEqual(const.COMPLETE, zone_import['status'])
        self.assertIsNotNone(zone_import['zone_id'])
        self.assertIsNotNone(zone_import['links'].get('zone'))

        LOG.info('Wait for the imported zone to go to ACTIVE')
        waiters.wait_for_zone_status(
            admin_zones_client, zone_import['zone_id'], const.ACTIVE)

        LOG.info('Check the imported zone looks good')
        zone = admin_zones_client.show_zone(zone_import['zone_id'])[1]
        self.assertEqual(const.NONE, zone['action'])
        self.assertEqual(const.ACTIVE, zone['status'])
        self.assertEqual(zone_name, zone['name'])
        self.assertEqual(target_pool_id, zone['pool_id'])
