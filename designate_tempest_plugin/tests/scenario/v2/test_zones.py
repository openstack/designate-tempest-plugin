# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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
from tempest import test
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import waiters

LOG = logging.getLogger(__name__)


class ZonesTest(base.BaseDnsTest):
    @classmethod
    def setup_clients(cls):
        super(ZonesTest, cls).setup_clients()

        cls.client = cls.os.zones_client

    @test.attr(type='slow')
    @test.idempotent_id('d0648f53-4114-45bd-8792-462a82f69d32')
    def test_create_and_delete_zone(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.client.delete_zone, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', zone['action'])
        self.assertEqual('PENDING', zone['status'])

        waiters.wait_for_zone_status(
            self.client, zone['id'], 'ACTIVE')

        LOG.info('Re-Fetch the zone')
        _, zone = self.client.show_zone(zone['id'])

        LOG.info('Ensure we respond with NONE+PENDING')
        self.assertEqual('NONE', zone['action'])
        self.assertEqual('ACTIVE', zone['status'])

        LOG.info('Delete the zone')
        _, zone = self.client.delete_zone(zone['id'])

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual('DELETE', zone['action'])
        self.assertEqual('PENDING', zone['status'])

        waiters.wait_for_zone_404(self.client, zone['id'])
