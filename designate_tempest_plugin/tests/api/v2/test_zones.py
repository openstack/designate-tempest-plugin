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
import six
from oslo_log import log as logging
from tempest import test
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests.api.v2 import base
from designate_tempest_plugin.common import waiters

LOG = logging.getLogger(__name__)


class BaseZonesTest(base.BaseDnsTest):
    def _assertExpected(self, expected, actual):
        for key, value in six.iteritems(expected):
            if key not in ('created_at', 'updated_at', 'version', 'links',
                           'status', 'action'):
                self.assertIn(key, actual)
                self.assertEqual(value, actual[key], key)


class ZonesTest(BaseZonesTest):
    @classmethod
    def setup_clients(cls):
        super(ZonesTest, cls).setup_clients()

        cls.client = cls.os.zones_client

    @test.attr(type='smoke')
    @test.idempotent_id('9d2e20fc-e56f-4a62-9c61-9752a9ec615c')
    def test_create_zone(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.client.delete_zone, zone['id'])

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', zone['action'])
        self.assertEqual('PENDING', zone['status'])

        waiters.wait_for_zone_status(
            self.client, zone['id'], 'ACTIVE')

        LOG.info('Re-Fetch the zone')
        _, body = self.client.show_zone(zone['id'])

        LOG.info('Ensure the fetched response matches the created zone')
        self._assertExpected(zone, body)

    @test.attr(type='smoke')
    @test.idempotent_id('a4791906-6cd6-4d27-9f15-32273db8bb3d')
    def test_delete_zone(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone(wait_until='ACTIVE')
        self.addCleanup(self.client.delete_zone, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the zone')
        _, body = self.client.delete_zone(zone['id'])

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual('DELETE', body['action'])
        self.assertEqual('PENDING', body['status'])

        waiters.wait_for_zone_404(self.client, zone['id'])


class ZonesAdminTest(BaseZonesTest):
    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(ZonesAdminTest, cls).setup_clients()

        cls.client = cls.os.zones_client
        cls.admin_client = cls.os_adm.zones_client

    @test.idempotent_id('6477f92d-70ba-46eb-bd6c-fc50c405e222')
    def test_get_other_tenant_zone(self):
        LOG.info('Create a zone as a user')
        _, zone = self.client.create_zone()
        self.addCleanup(self.client.delete_zone, zone['id'])

        LOG.info('Fetch the zone as an admin')
        _, body = self.admin_client.show_zone(
            zone['id'], params={'all_projects': True})

        LOG.info('Ensure the fetched response matches the created zone')
        self._assertExpected(zone, body)
