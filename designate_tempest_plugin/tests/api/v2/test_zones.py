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
from tempest import config
from tempest.lib import decorators
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc


from designate_tempest_plugin.common import constants as const

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseZonesTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                    'status', 'action']

    @classmethod
    def setup_clients(cls):
        super(BaseZonesTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(BaseZonesTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="BaseZonesTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(BaseZonesTest, cls).resource_cleanup()


class ZonesTest(BaseZonesTest):

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.pool_client = cls.os_system_admin.dns_v2.PoolClient()
        else:
            cls.pool_client = cls.os_admin.dns_v2.PoolClient()
        cls.client = cls.os_primary.dns_v2.ZonesClient()
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()

    @decorators.idempotent_id('9d2e20fc-e56f-4a62-9c61-9752a9ec615c')
    def test_create_zones(self):
        # Create a PRIMARY zone
        LOG.info('Create a PRIMARY zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_zones_primary", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual(const.CREATE, zone['action'])
        self.assertEqual(const.PENDING, zone['status'])

        # Get the Name Servers (hosts) created in PRIMARY zone
        nameservers = self.client.show_zone_nameservers(zone['id'])[1]
        nameservers = [dic['hostname'] for dic in nameservers['nameservers']]

        # Create a SECONDARY zone
        LOG.info('Create a SECONDARY zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_zones_secondary", suffix=self.tld_name)
        zone = self.client.create_zone(
            name=zone_name, zone_type=const.SECONDARY_ZONE_TYPE,
            primaries=nameservers)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual(const.CREATE, zone['action'])
        self.assertEqual(const.PENDING, zone['status'])

        # Test with no extra header overrides (sudo-project-id)
        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')
            expected_allowed.append('os_project_member')

        self.check_CUD_RBAC_enforcement('ZonesClient', 'create_zone',
                                        expected_allowed, False)

        # Test with x-auth-sudo-project-id header
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'ZonesClient', 'create_zone', expected_allowed, False,
            project_id=self.client.project_id)

    @decorators.idempotent_id('ec150c22-f52e-11eb-b09b-74e5f9e2a801')
    def test_create_zone_validate_recordsets_created(self):
        # Create a PRIMARY zone and wait till it's Active
        LOG.info('Create a PRIMARY zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_zone_validate_recordsets", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name,
                                       wait_until=const.ACTIVE)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual(const.CREATE, zone['action'])
        self.assertEqual(const.PENDING, zone['status'])

        LOG.info('Ensure that SOA and NS recordsets types has been created.')
        recordsets = self.recordset_client.list_recordset(
            zone['id'])[1]['recordsets']
        types = [rec['type'] for rec in recordsets]
        expected_types = ['SOA', 'NS']
        for exp_type in expected_types:
            self.assertIn(
                exp_type, types,
                'Failed, expected recordset type:{} was'
                ' not created'.format(exp_type))

    @decorators.idempotent_id('02ca5d6a-86ce-4f02-9d94-9e5db55c3055')
    def test_show_zone(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="show_zones", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Fetch the zone')
        body = self.client.show_zone(zone['id'])[1]

        LOG.info('Ensure the fetched response matches the created zone')
        self.assertExpected(zone, body, self.excluded_keys)

        # TODO(johnsom) Test reader roles once this bug is fixed.
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test with no extra header overrides (all_projects, sudo-project-id)
        expected_allowed = ['os_primary']

        self.check_list_show_RBAC_enforcement(
            'ZonesClient', 'show_zone', expected_allowed, True, zone['id'])

        # Test with x-auth-all-projects and x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'ZonesClient', 'show_zone', expected_allowed, False, zone['id'],
            headers=self.all_projects_header)
        self.check_list_show_RBAC_enforcement(
            'ZonesClient', 'show_zone', expected_allowed, False, zone['id'],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('a4791906-6cd6-4d27-9f15-32273db8bb3d')
    def test_delete_zone(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="delete_zones", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        # Test RBAC
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement('ZonesClient', 'delete_zone',
                                        expected_allowed, True, zone['id'])

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement('ZonesClient', 'delete_zone',
                                        expected_allowed, False, zone['id'],
                                        headers=self.all_projects_header)
        self.check_CUD_RBAC_enforcement(
            'ZonesClient', 'delete_zone', expected_allowed, False, zone['id'],
            headers={'x-auth-sudo-project-id': self.client.project_id})

        LOG.info('Delete the zone')
        body = self.client.delete_zone(zone['id'])[1]

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual(const.DELETE, body['action'])
        self.assertEqual(const.PENDING, body['status'])

    @decorators.idempotent_id('5bfa3cfe-5bc8-443b-bf48-cfba44cbb247')
    def test_list_zones(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_zones", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('List zones')
        body = self.client.list_zones()[1]

        # TODO(kiall): We really want to assert that out newly created zone is
        #              present in the response.
        self.assertGreater(len(body['zones']), 0)

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC - Users that are allowed to call list, but should get
        #             zero zones.
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader',
                                'os_admin', 'os_project_member',
                                'os_project_reader']
        else:
            expected_allowed = ['os_alt']

        self.check_list_RBAC_enforcement_count(
            'ZonesClient', 'list_zones', expected_allowed, 0)

        # Test that users who should see the zone, can see it.
        expected_allowed = ['os_primary']

        self.check_list_IDs_RBAC_enforcement(
            'ZonesClient', 'list_zones', expected_allowed, [zone['id']])

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'ZonesClient', 'list_zones', expected_allowed, [zone['id']],
            headers=self.all_projects_header)
        self.check_list_IDs_RBAC_enforcement(
            'ZonesClient', 'list_zones', expected_allowed, [zone['id']],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('123f51cb-19d5-48a9-aacc-476742c02141')
    def test_update_zone(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="update_zone", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        # Generate a random description
        description = data_utils.rand_name()

        LOG.info('Update the zone')
        zone = self.client.update_zone(
            zone['id'], description=description)[1]

        LOG.info('Ensure we respond with UPDATE+PENDING')
        self.assertEqual(const.UPDATE, zone['action'])
        self.assertEqual(const.PENDING, zone['status'])

        LOG.info('Ensure we respond with updated values')
        self.assertEqual(description, zone['description'])

        # Test RBAC
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'ZonesClient', 'update_zone', expected_allowed, True,
            zone['id'], description=description)

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'ZonesClient', 'update_zone', expected_allowed, False,
            zone['id'], description=description,
            headers=self.all_projects_header)
        self.check_CUD_RBAC_enforcement(
            'ZonesClient', 'update_zone', expected_allowed, False,
            zone['id'], description=description,
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('3acddc86-62cc-4bfa-8589-b99e5d239bf2')
    @decorators.skip_because(bug="1960487")
    def test_serial_changes_on_update(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="serial_changes_on_update", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name,
                                       wait_until=const.ACTIVE)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info("Update Zone's email")
        update_email = self.client.update_zone(
            zone['id'], email=dns_data_utils.rand_email())[1]
        self.assertNotEqual(
            zone['serial'], update_email['serial'],
            "Failed, expected: 'Serial' is supposed to be changed "
            "on Email update.")

        LOG.info("Update Zone's TTL")
        update_ttl = self.client.update_zone(
            zone['id'], ttl=dns_data_utils.rand_ttl())[1]
        self.assertNotEqual(
            update_email['serial'], update_ttl['serial'],
            "Failed, expected: 'Serial' is supposed to be changed "
            "on TTL update.")

        LOG.info("Update Zone's email and description")
        update_email_description = self.client.update_zone(
            zone['id'],
            email=dns_data_utils.rand_email(),
            description=data_utils.rand_name())[1]
        self.assertNotEqual(
            update_ttl['serial'], update_email_description['serial'],
            "Failed, expect the Serial to change "
            "when the Email and Description are updated")

        LOG.info("Update Zone's description")
        update_description = self.client.update_zone(
            zone['id'], description=data_utils.rand_name())[1]
        self.assertEqual(
            update_email_description['serial'], update_description['serial'],
            "Failed, expect the Serial to not change "
            "when the Description is updated")

    @decorators.idempotent_id('d4ce813e-64a5-11eb-9f43-74e5f9e2a801')
    def test_get_primary_zone_nameservers(self):
        # Create a zone and get the associated "pool_id"
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="get_primary_nameservers", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
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

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC
        expected_allowed = ['os_primary']

        self.check_list_show_RBAC_enforcement(
            'ZonesClient', 'show_zone_nameservers', expected_allowed,
            True, zone['id'])

        # Test with x-auth-all-projects and x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'ZonesClient', 'show_zone_nameservers', expected_allowed,
            False, zone['id'], headers=self.all_projects_header)
        self.check_list_show_RBAC_enforcement(
            'ZonesClient', 'show_zone_nameservers', expected_allowed,
            False, zone['id'],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('9970b632-f2db-11ec-a757-201e8823901f')
    def test_create_zone_ttl_zero(self):
        LOG.info('Create a PRIMARY zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="test_create_zone_ttl_zero", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name, ttl=0)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual(const.CREATE, zone['action'])
        self.assertEqual(const.PENDING, zone['status'])

        LOG.info('Fetch the zone, ensure TTL is Zero')
        body = self.client.show_zone(zone['id'])[1]
        self.assertEqual(
            0, body['ttl'],
            "Failed, actual Zone's TTL:{} "
            "is not Zero".format(body['ttl']))


class ZonesAdminTest(BaseZonesTest):
    credentials = ["primary", "admin", "system_admin", "alt"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesAdminTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.ZonesClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.ZonesClient()
        cls.client = cls.os_primary.dns_v2.ZonesClient()
        cls.alt_client = cls.os_alt.dns_v2.ZonesClient()

    @decorators.idempotent_id('f6fe8cce-8b04-11eb-a861-74e5f9e2a801')
    def test_show_zone_impersonate_another_project(self):
        LOG.info('Create zone "A" using primary client')
        zone_name = dns_data_utils.rand_zone_name(
            name="show_zone_impersonate", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
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
        zone_name = dns_data_utils.rand_zone_name(
            name="list_zone_all_projects_A", suffix=self.tld_name)
        primary_zone = self.client.create_zone(name=zone_name,
                                               wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete, self.client, primary_zone['id'])

        LOG.info('Create zone "B" using Alt client')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_zone_all_projects_B", suffix=self.tld_name)
        alt_zone = self.alt_client.create_zone(name=zone_name,
                                               wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete, self.alt_client, alt_zone['id'])

        LOG.info('Create zone "C" using Admin client')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_zone_all_projects_C", suffix=self.tld_name)
        admin_zone = self.admin_client.create_zone(
            name=zone_name, project_id="FakeProjectID",
            wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete, self.admin_client, admin_zone['id'],
            headers=self.all_projects_header)

        LOG.info('As admin user list all projects zones')
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        body = self.admin_client.list_zones(
            headers=self.all_projects_header,
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
    credentials = ["primary", "alt", "admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZoneOwnershipTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZoneOwnershipTest, cls).setup_clients()
        cls.client = cls.os_primary.dns_v2.ZonesClient()
        cls.alt_client = cls.os_alt.dns_v2.ZonesClient()

    @decorators.idempotent_id('5d28580a-a012-4b57-b211-e077b1a01340')
    def test_no_create_duplicate_domain(self):
        LOG.info('Create a zone as a default user')
        zone_name = dns_data_utils.rand_zone_name(
            name="no_create_duplicate", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
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
        zone_name = dns_data_utils.rand_zone_name(
            name="no_create_subdomain_by_alt", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Create a zone as an alt user with existing subdomain')
        self.assertRaises(lib_exc.Forbidden,
            self.alt_client.create_zone, name='sub.' + zone['name'])
        self.assertRaises(lib_exc.Forbidden,
            self.alt_client.create_zone, name='sub.sub.' + zone['name'])

    @decorators.idempotent_id('f1723d48-c082-43cd-94bf-ebeb5b8c9458')
    def test_no_create_superdomain_by_alt_user(self):
        zone_name = dns_data_utils.rand_zone_name(
            name="no_create_superdomain_by_alt", suffix=self.tld_name)

        LOG.info('Create a zone as a default user')
        zone = self.client.create_zone(name='a.b.' + zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        LOG.info('Create a zone as an alt user with existing superdomain')
        self.assertRaises(lib_exc.Forbidden,
            self.alt_client.create_zone, name=zone_name)


class ZonesNegativeTest(BaseZonesTest):
    credentials = ["admin", "primary", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesNegativeTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesNegativeTest, cls).setup_clients()
        cls.client = cls.os_primary.dns_v2.ZonesClient()

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

    @decorators.idempotent_id('79921370-92e1-11eb-9d02-74e5f9e2a801')
    def test_delete_non_existing_zone(self):
        LOG.info('Delete non existing zone')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.delete_zone(uuid.uuid1()))

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
