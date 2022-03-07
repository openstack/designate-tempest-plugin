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
from tempest.lib import decorators

from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests.api.v2.test_zones_imports import \
    BaseZonesImportTest

LOG = logging.getLogger(__name__)


class ZonesImportTest(BaseZonesImportTest):

    credentials = ["primary", "admin", "system_admin"]

    @classmethod
    def setup_clients(cls):
        super(ZonesImportTest, cls).setup_clients()

        cls.client = cls.os_primary.dns_v2.ZoneImportsClient()
        cls.zones_client = cls.os_primary.dns_v2.ZonesClient()

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
