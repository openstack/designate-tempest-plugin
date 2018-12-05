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
from designate_tempest_plugin.tests.api.v2.test_zones_exports import \
    BaseZoneExportsTest

LOG = logging.getLogger(__name__)


class ZonesExportTest(BaseZoneExportsTest):

    @classmethod
    def setup_clients(cls):
        super(ZonesExportTest, cls).setup_clients()

        cls.zones_client = cls.os_primary.zones_client
        cls.client = cls.os_primary.zone_exports_client

    @decorators.attr(type='slow')
    @decorators.idempotent_id('0484c3c4-df57-458e-a6e5-6eb63e0475e0')
    def test_create_zone_export_and_show_exported_zonefile(self):
        LOG.info('Create a zone to be exported')
        _, zone = self.zones_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'])

        LOG.info('Create a zone export')
        _, zone_export = self.client.create_zone_export(zone['id'])
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])

        self.assertEqual('PENDING', zone_export['status'])
        self.assertEqual(zone['id'], zone_export['zone_id'])
        self.assertIsNone(zone_export['links'].get('export'))
        self.assertIsNone(zone_export['location'])

        LOG.info('Wait for the zone export to COMPLETE')
        waiters.wait_for_zone_export_status(
            self.client, zone_export['id'], 'COMPLETE')

        LOG.info('Check the zone export looks good')
        _, zone_export = self.client.show_zone_export(zone_export['id'])

        self.assertEqual('COMPLETE', zone_export['status'])
        self.assertEqual(zone['id'], zone_export['zone_id'])
        self.assertIsNotNone(zone_export['links'].get('export'))
        self.assertIsNotNone(zone_export['location'])

        LOG.info('Fetch the exported zonefile')
        _, zonefile = self.client.show_exported_zonefile(zone_export['id'])
        self.assertEqual(zone['name'], zonefile.origin)
        self.assertEqual(zone['ttl'], zonefile.ttl)
