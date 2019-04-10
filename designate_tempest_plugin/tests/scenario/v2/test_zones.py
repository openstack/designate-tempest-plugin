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
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
import testtools

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import waiters


LOG = logging.getLogger(__name__)


class ZonesTest(base.BaseDnsV2Test):
    @classmethod
    def setup_clients(cls):
        super(ZonesTest, cls).setup_clients()

        cls.client = cls.os_primary.zones_client
        cls.query_client = cls.os_primary.query_client

    @decorators.attr(type='smoke')
    @decorators.attr(type='slow')
    @decorators.idempotent_id('d0648f53-4114-45bd-8792-462a82f69d32')
    def test_create_and_delete_zone(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
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

    @decorators.attr(type='slow')
    @decorators.idempotent_id('c9838adf-14dc-4097-9130-e5cea3727abb')
    def test_delete_zone_pending_create(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        # NOTE(kiall): This is certainly a little racey, it's entirely
        #              possible the zone will become active before we delete
        #              it. Worst case, that means we get an unexpected pass.
        #              Theres not a huge amount we can do, given this is
        #              black-box testing.
        LOG.info('Delete the zone while it is still pending')
        _, zone = self.client.delete_zone(zone['id'])

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual('DELETE', zone['action'])
        self.assertEqual('PENDING', zone['status'])

        waiters.wait_for_zone_404(self.client, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('ad8d1f5b-da66-46a0-bbee-14dc84a5d791')
    @testtools.skipUnless(
        config.CONF.dns.nameservers,
        "Config option dns.nameservers is missing or empty")
    def test_zone_create_propagates_to_nameservers(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        waiters.wait_for_zone_status(self.client, zone['id'], "ACTIVE")
        waiters.wait_for_query(self.query_client, zone['name'], "SOA")

    @decorators.attr(type='slow')
    @decorators.idempotent_id('d13d3095-c78f-4aae-8fe3-a74ccc335c84')
    @testtools.skipUnless(
        config.CONF.dns.nameservers,
        "Config option dns.nameservers is missing or empty")
    def test_zone_delete_propagates_to_nameservers(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        waiters.wait_for_zone_status(self.client, zone['id'], "ACTIVE")
        waiters.wait_for_query(self.query_client, zone['name'], "SOA")

        LOG.info('Delete the zone')
        self.client.delete_zone(zone['id'])

        waiters.wait_for_zone_404(self.client, zone['id'])
        waiters.wait_for_query(self.query_client, zone['name'], "SOA",
                               found=False)
