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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.lib.common.utils import data_utils

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class BaseZonesTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                    'status', 'action']


class ZonesTest(BaseZonesTest):
    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesTest, cls).setup_clients()

        cls.client = cls.os_primary.zones_client

    @decorators.idempotent_id('9d2e20fc-e56f-4a62-9c61-9752a9ec615c')
    def test_create_zone(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', zone['action'])
        self.assertEqual('PENDING', zone['status'])

    @decorators.idempotent_id('02ca5d6a-86ce-4f02-9d94-9e5db55c3055')
    def test_show_zone(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Fetch the zone')
        _, body = self.client.show_zone(zone['id'])

        LOG.info('Ensure the fetched response matches the created zone')
        self.assertExpected(zone, body, self.excluded_keys)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('a4791906-6cd6-4d27-9f15-32273db8bb3d')
    def test_delete_zone(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the zone')
        _, body = self.client.delete_zone(zone['id'])

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual('DELETE', body['action'])
        self.assertEqual('PENDING', body['status'])

    @decorators.idempotent_id('5bfa3cfe-5bc8-443b-bf48-cfba44cbb247')
    def test_list_zones(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('List zones')
        _, body = self.client.list_zones()

        # TODO(kiall): We really want to assert that out newly created zone is
        #              present in the response.
        self.assertGreater(len(body['zones']), 0)

    @decorators.idempotent_id('123f51cb-19d5-48a9-aacc-476742c02141')
    def test_update_zone(self):
        LOG.info('Create a zone')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        # Generate a random description
        description = data_utils.rand_name()

        LOG.info('Update the zone')
        _, zone = self.client.update_zone(
            zone['id'], description=description)

        LOG.info('Ensure we respond with UPDATE+PENDING')
        self.assertEqual('UPDATE', zone['action'])
        self.assertEqual('PENDING', zone['status'])

        LOG.info('Ensure we respond with updated values')
        self.assertEqual(description, zone['description'])

    @decorators.idempotent_id('925192f2-0ed8-4591-8fe7-a9fa028f90a0')
    def test_list_zones_dot_json_fails(self):
        uri = self.client.get_uri('zones.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.get(uri))


class ZonesAdminTest(BaseZonesTest):
    credentials = ['primary', 'admin']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesAdminTest, cls).setup_clients()

        cls.client = cls.os_primary.zones_client
        cls.admin_client = cls.os_admin.zones_client

    @decorators.idempotent_id('6477f92d-70ba-46eb-bd6c-fc50c405e222')
    def test_get_other_tenant_zone(self):
        LOG.info('Create a zone as a user')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Fetch the zone as an admin')
        _, body = self.admin_client.show_zone(
            zone['id'], params={'all_projects': True})

        LOG.info('Ensure the fetched response matches the created zone')
        self.assertExpected(zone, body, self.excluded_keys)


class ZoneOwnershipTest(BaseZonesTest):
    credentials = ['primary', 'alt']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZoneOwnershipTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZoneOwnershipTest, cls).setup_clients()

        cls.client = cls.os_primary.zones_client
        cls.alt_client = cls.os_alt.zones_client

    @decorators.idempotent_id('5d28580a-a012-4b57-b211-e077b1a01340')
    def test_no_create_duplicate_domain(self):
        LOG.info('Create a zone as a default user')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Create a zone as an default with existing domain')
        self.assertRaises(lib_exc.Conflict,
            self.client.create_zone, name=zone['name'])

        LOG.info('Create a zone as an alt user with existing domain')
        self.assertRaises(lib_exc.Conflict,
            self.alt_client.create_zone, name=zone['name'])

    @decorators.idempotent_id('a48776fd-b1aa-4a25-9f09-d1d34cfbb175')
    def test_no_create_subdomain_by_alt_user(self):
        LOG.info('Create a zone as a default user')
        _, zone = self.client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Create a zone as an alt user with existing subdomain')
        self.assertRaises(lib_exc.Forbidden,
            self.alt_client.create_zone, name='sub.' + zone['name'])
        self.assertRaises(lib_exc.Forbidden,
            self.alt_client.create_zone, name='sub.sub.' + zone['name'])

    @decorators.idempotent_id('f1723d48-c082-43cd-94bf-ebeb5b8c9458')
    def test_no_create_superdomain_by_alt_user(self):
        zone_name = dns_data_utils.rand_zone_name()

        LOG.info('Create a zone as a default user')
        _, zone = self.client.create_zone(name='a.b.' + zone_name)
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Create a zone as an alt user with existing superdomain')
        self.assertRaises(lib_exc.Forbidden,
            self.alt_client.create_zone, name=zone_name)
