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
import uuid
from oslo_log import log as logging
from tempest.lib import decorators
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc


from designate_tempest_plugin.common import constants as const

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

from designate_tempest_plugin.common import waiters
LOG = logging.getLogger(__name__)


class BaseZonesTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                    'status', 'action']


class ZonesTest(BaseZonesTest):
    credentials = ['admin', 'primary']
    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesTest, cls).setup_clients()

        cls.client = cls.os_primary.zones_client
        cls.pool_client = cls.os_admin.pool_client

    @decorators.idempotent_id('9d2e20fc-e56f-4a62-9c61-9752a9ec615c')
    def test_create_zones(self):
        # Create a PRIMARY zone
        LOG.info('Create a PRIMARY zone')
        zone = self.client.create_zone()[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', zone['action'])
        self.assertEqual('PENDING', zone['status'])

        # Get the Name Servers (hosts) created in PRIMARY zone
        nameservers = self.client.show_zone_nameservers(zone['id'])[1]
        nameservers = [dic['hostname'] for dic in nameservers['nameservers']]

        # Create a SECONDARY zone
        LOG.info('Create a SECONDARY zone')
        zone = self.client.create_zone(
            zone_type=const.SECONDARY_ZONE_TYPE, primaries=nameservers)[1]
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

    @decorators.idempotent_id('49268b24-92de-11eb-9d02-74e5f9e2a801')
    def test_show_not_existing_zone(self):
        LOG.info('Fetch non existing zone')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.show_zone(uuid.uuid1()))

    @decorators.idempotent_id('736e3b50-92e0-11eb-9d02-74e5f9e2a801')
    def test_use_invalid_id_to_show_zone(self):
        LOG.info('Fetch the zone using invalid zone ID')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_uuid', 400):
            self.client.show_zone(uuid='zahlabut')

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

    @decorators.idempotent_id('79921370-92e1-11eb-9d02-74e5f9e2a801')
    def test_delete_non_existing_zone(self):
        LOG.info('Delete non existing zone')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.delete_zone(uuid.uuid1()))

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

    @decorators.idempotent_id('e391e30a-92e0-11eb-9d02-74e5f9e2a801')
    def test_update_non_existing_zone(self):
        LOG.info('Update non existing zone')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.update_zone(
                uuid.uuid1(), description=data_utils.rand_name()))

    @decorators.idempotent_id('925192f2-0ed8-4591-8fe7-a9fa028f90a0')
    def test_list_zones_dot_json_fails(self):
        uri = self.client.get_uri('zones.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.get(uri))

    @decorators.idempotent_id('d4ce813e-64a5-11eb-9f43-74e5f9e2a801')
    def test_get_primary_zone_nameservers(self):
        # Create a zone and get the associated "pool_id"
        LOG.info('Create a zone')
        zone = self.client.create_zone()[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])
        zone_pool_id = zone['pool_id']

        # Get zone's Name Servers using dedicated API request
        zone_nameservers = self.client.show_zone_nameservers(zone['id'])[1]
        zone_nameservers = zone_nameservers['nameservers']
        LOG.info('Zone Name Servers are: {}'.format(zone_nameservers))
        self.assertIsNot(
            0, len(zone_nameservers),
            "Failed - received list of nameservers shouldn't be empty")

        # Use "pool_id" to get the Name Servers used
        pool = self.pool_client.show_pool(zone_pool_id)[1]
        pool_nameservers = pool['ns_records']
        LOG.info('Pool nameservers: {}'.format(pool_nameservers))

        # Make sure that pool's and zone's Name Servers are same
        self.assertCountEqual(
            pool_nameservers, zone_nameservers,
            'Failed - Pool and Zone nameservers should be the same')


class ZonesAdminTest(BaseZonesTest):
    credentials = ['primary', 'admin', 'alt']

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
        cls.alt_client = cls.os_alt.zones_client

    @decorators.idempotent_id('f6fe8cce-8b04-11eb-a861-74e5f9e2a801')
    def test_show_zone_impersonate_another_project(self):
        LOG.info('Create zone "A" using primary client')
        zone = self.client.create_zone()[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('As Alt tenant show zone created by Primary tenant. '
                 'Expected: 404 NotFound')
        self.assertRaises(
            lib_exc.NotFound, self.alt_client.show_zone, uuid=zone['id'])

        LOG.info('As Admin tenant show zone created by Primary tenant. '
                 'Expected: 404 NotFound')
        self.assertRaises(
            lib_exc.NotFound, self.admin_client.show_zone, uuid=zone['id'])

        LOG.info('As Alt tenant show zone created by Primary tenant using '
                 '"x-auth-sudo-project-id" HTTP header. '
                 'Expected: 403 Forbidden')
        self.assertRaises(
            lib_exc.Forbidden, self.alt_client.show_zone, uuid=None,
            headers={'x-auth-sudo-project-id': zone['project_id']})

        LOG.info('As Admin user impersonate another project '
                 '(using "x-auth-sudo-project-id" HTTP header) to show '
                 'a Primary tenant zone.')
        body = self.admin_client.show_zone(
            uuid=None, headers={
                'x-auth-sudo-project-id': zone['project_id']})[1]

        LOG.info('Ensure the fetched response matches the impersonated'
                 ' project, it means the ID of a zone "A"')
        self.assertExpected(zone, body['zones'][0], self.excluded_keys)

    @decorators.idempotent_id('e1cf7104-8b06-11eb-a861-74e5f9e2a801')
    def test_list_all_projects_zones(self):

        LOG.info('Create zone "A" using Primary client')
        primary_zone = self.client.create_zone()[1]
        self.addCleanup(
            self.wait_zone_delete, self.client, primary_zone['id'])
        LOG.info('Wait till the zone is ACTIVE')
        waiters.wait_for_zone_status(
            self.client, primary_zone['id'], 'ACTIVE')

        LOG.info('Create zone "B" using Alt client')
        alt_zone = self.alt_client.create_zone()[1]
        self.addCleanup(
            self.wait_zone_delete, self.alt_client, alt_zone['id'])
        LOG.info('Wait till the zone is ACTIVE')
        waiters.wait_for_zone_status(
            self.alt_client, alt_zone['id'], 'ACTIVE')

        LOG.info('Create zone "C" using Admin client')
        admin_zone = self.admin_client.create_zone()[1]
        self.addCleanup(
            self.wait_zone_delete, self.admin_client, admin_zone['id'])
        LOG.info('Wait till the zone is ACTIVE')
        waiters.wait_for_zone_status(
            self.admin_client, admin_zone['id'], 'ACTIVE')

        LOG.info('As admin user list all projects zones')
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        body = self.admin_client.list_zones(
            headers={'x-auth-all-projects': True},
            params={'limit': 1000})[1]['zones']
        listed_zone_ids = [item['id'] for item in body]

        LOG.info('Ensure the fetched response includes all zone '
                 'IDs created within the test')

        for id in [primary_zone['id'], alt_zone['id'], admin_zone['id']]:
            self.assertIn(
                id, listed_zone_ids,
                'Failed, id:{} was not found in listed zones:{} '.format(
                    id, listed_zone_ids))


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


class ZonesNegativeTest(BaseZonesTest):
    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesNegativeTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesNegativeTest, cls).setup_clients()
        cls.client = cls.os_primary.zones_client

    @decorators.idempotent_id('551853c0-8593-11eb-8c8a-74e5f9e2a801')
    def test_no_valid_zone_name(self):
        no_valid_names = ['a' * 1000, '___', '!^%&^#%^!@#', 'ggg', '.a', '']
        for name in no_valid_names:
            LOG.info('Trying to create a zone named: {} '.format(name))
            self.assertRaisesDns(
                lib_exc.BadRequest, 'invalid_object', 400,
                self.client.create_zone, name=name)

    @decorators.idempotent_id('551853c0-8593-11eb-8c8a-74e5f9e2a801')
    def test_no_valid_email(self):
        no_valid_emails = [
            'zahlabut#gmail.com', '123456', '___', '', '*&^*^%$']
        for email in no_valid_emails:
            LOG.info(
                'Trying to create a zone using: {} as email'
                ' value: '.format(email))
            self.assertRaisesDns(
                lib_exc.BadRequest, 'invalid_object', 400,
                self.client.create_zone, email=email)

    @decorators.idempotent_id('551853c0-8593-11eb-8c8a-74e5f9e2a801')
    def test_no_valid_ttl(self):
        no_valid_tls = ['zahlabut', -60000,
                        2147483647 + 10]  # Max valid TTL is 2147483647

        for ttl in no_valid_tls:
            LOG.info(
                'Trying to create a zone using: {} as TTL'
                ' value: '.format(ttl))
            self.assertRaisesDns(
                lib_exc.BadRequest, 'invalid_object', 400,
                self.client.create_zone, ttl=ttl)

    @decorators.idempotent_id('a3b0a928-a682-11eb-9899-74e5f9e2a801')
    def test_huge_size_description(self):
        LOG.info('Trying to create a zone using huge size description')
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.client.create_zone,
            description=dns_data_utils.rand_zone_name() * 10000)
