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

from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests.api.v2.test_zones_imports import \
    BaseZonesImportTest

LOG = logging.getLogger(__name__)


class ZonesImportTest(BaseZonesImportTest):

    @classmethod
    def setup_clients(cls):
        super(ZonesImportTest, cls).setup_clients()

        cls.client = cls.os_primary.zone_imports_client
        cls.zones_client = cls.os_primary.zones_client

    @decorators.attr(type='slow')
    @decorators.idempotent_id('679f38d0-2f2f-49c5-934e-8fe0c452f56e')
    def test_create_zone_import_and_wait_for_zone(self):
        name = dns_data_utils.rand_zone_name('testimport')
        zonefile = dns_data_utils.rand_zonefile_data(name=name)

        LOG.info('Import zone %r', name)
        _, zone_import = self.client.create_zone_import(zonefile)
        self.addCleanup(self.client.delete_zone_import, zone_import['id'])

        LOG.info('Wait for the zone import to COMPLETE')
        waiters.wait_for_zone_import_status(self.client, zone_import['id'],
                                            "COMPLETE")

        LOG.info('Check the zone import looks good')
        _, zone_import = self.client.show_zone_import(zone_import['id'])
        self.addCleanup(self.wait_zone_delete,
                        self.zones_client,
                        zone_import['zone_id'])

        self.assertEqual('COMPLETE', zone_import['status'])
        self.assertIsNotNone(zone_import['zone_id'])
        self.assertIsNotNone(zone_import['links'].get('zone'))

        LOG.info('Wait for the imported zone to go to ACTIVE')
        waiters.wait_for_zone_status(self.zones_client, zone_import['zone_id'],
                                     "ACTIVE")

        LOG.info('Check the imported zone looks good')
        _, zone = self.zones_client.show_zone(zone_import['zone_id'])
        self.assertEqual('NONE', zone['action'])
        self.assertEqual('ACTIVE', zone['status'])
        self.assertEqual(name, zone['name'])
