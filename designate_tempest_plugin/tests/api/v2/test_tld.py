# Copyright 2016 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.lib.common.utils import data_utils

from designate_tempest_plugin.tests import base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseTldTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'links']


class TldAdminTest(BaseTldTest):
    credentials = ["admin", "system_admin", "system_reader",
                   "primary", "alt", "project_reader", "project_member"]

    # Use a TLD suffix unique to this test class.
    local_tld_suffix = '.'.join(["tldadmintest", CONF.dns.tld_suffix])

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TldAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TldAdminTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.TldClient()
        cls.primary_client = cls.os_primary.dns_v2.TldClient()
        cls.primary_zone_client = cls.os_primary.dns_v2.ZonesClient()

    @classmethod
    def _generate_tld_name(cls, test_name):
        return '.'.join([data_utils.rand_name(name=test_name),
                         cls.local_tld_suffix])

    @decorators.idempotent_id('52a4bb4b-4eff-4591-9dd3-ad98316806c3')
    def test_create_tld(self):
        tld_name = self._generate_tld_name("test_create_tld")
        tld_data = {"name": tld_name, "description": "sample tld"}

        LOG.info('Create a tld')
        tld = self.admin_client.create_tld(tld_data['name'],
                                           tld_data['description'])[1]
        self.addCleanup(self.admin_client.delete_tld, tld['id'])

        self.assertEqual(tld_name, tld['name'])

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement('TldClient', 'create_tld',
                                        expected_allowed, False)

    @decorators.idempotent_id('961bd2e8-d4d0-11eb-b8ee-74e5f9e2a801')
    def test_create_duplicated_tlds(self):
        tld_name = self._generate_tld_name("test_create_duplicated_tlds")
        tld_data = {"name": tld_name,
                    "description": "test_create_duplicated_tlds"}

        LOG.info('Create a first "org" TLD')
        tld = self.admin_client.create_tld(
            tld_data['name'], tld_data['description'])[1]
        self.addCleanup(self.admin_client.delete_tld, tld['id'])
        self.assertEqual(tld_name, tld['name'])

        LOG.info('Try to create a second "org" TLD')
        self.assertRaises(
            lib_exc.Conflict, self.admin_client.create_tld,
            tld_name=tld_data['name'],
            description=tld_data['description'])

    @decorators.idempotent_id('0c0ab92e-d4db-11eb-b8ee-74e5f9e2a801')
    def test_create_multiply_tlds(self):
        for _dummy in range(0, 2):
            tld_name = self._generate_tld_name("test_create_multiply_tlds")
            tld_data = {"name": tld_name,
                        "description": "test_create_multiply_tlds"}
            LOG.info('Create a "{}" TLD'.format(tld_name))
            tld = self.admin_client.create_tld(
                tld_data['name'], tld_data['description'])[1]
            self.addCleanup(self.admin_client.delete_tld, tld['id'])
            self.assertEqual(tld_name, tld['name'])

    @decorators.idempotent_id('52a4bb4b-4eff-4591-9dd3-ad98316806c3')
    def test_create_invalid_tld(self):
        invalid_tlds = ['   ', 'fff.', '^&$', 't' * 1000, '@p%']
        for tld_name in invalid_tlds:
            tld_data = {
                "name": tld_name, "description": "test_create_invalid_tld"}
            LOG.info('Create a "{}" TLD'.format(tld_name))
            self.assertRaises(
                lib_exc.BadRequest, self.admin_client.create_tld,
                tld_name=tld_data['name'], description=tld_data['description'])
        LOG.info('Create a "{}" TLD with huge size description.')
        self.assertRaises(
            lib_exc.BadRequest, self.admin_client.create_tld,
            tld_name='org', description='test_create_invalid_tld' * 1000)

    @decorators.idempotent_id('757019c0-d4e2-11eb-b8ee-74e5f9e2a801')
    def test_create_tld_as_primary_user(self):
        tld_data = {
            "name": "org", "description": "test_create_tld_as_primary_user"}
        LOG.info('Try to create a TLD as primary user.')
        self.assertRaises(
            lib_exc.Forbidden, self.primary_client.create_tld,
            tld_name=tld_data['name'], description=tld_data['description'])

    @decorators.idempotent_id('271af08c-2603-4f61-8eb1-05887b74e25a')
    def test_show_tld(self):
        tld_name = self._generate_tld_name("test_show_tld")
        tld_data = {
                     "name": tld_name,
                     "description": "sample tld"}

        LOG.info('Create a tld')
        tld = self.admin_client.create_tld(tld_data['name'],
                                           tld_data['description'])[1]
        self.addCleanup(self.admin_client.delete_tld, tld['id'])

        LOG.info('Fetch the tld')
        body = self.admin_client.show_tld(tld['id'])[1]

        LOG.info('Ensure the fetched response matches the created tld')
        self.assertExpected(tld, body, self.excluded_keys)

        # Test RBAC
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader']
        else:
            expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'TldClient', 'show_tld', expected_allowed, False, tld['id'])

    @decorators.idempotent_id('26708cb8-7126-48a7-9424-1c225e56e609')
    def test_delete_tld(self):
        LOG.info('Create a tld')
        tld_name = self._generate_tld_name("test_delete_tld")
        tld = self.admin_client.create_tld(tld_name)[1]
        self.addCleanup(self.admin_client.delete_tld, tld['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the tld')
        self.admin_client.delete_tld(tld['id'])

        self.assertRaises(lib_exc.NotFound, self.admin_client.show_tld,
                          tld['id'])

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement('TldClient', 'delete_tld',
                                        expected_allowed, False, tld['id'])

    @decorators.idempotent_id('95b13759-c85c-4791-829b-9591ca15779d')
    def test_list_tlds(self):
        LOG.info('List tlds')
        tld_name = self._generate_tld_name("test_list_tlds")
        tld = self.admin_client.create_tld(tld_name)[1]
        self.addCleanup(self.admin_client.delete_tld, tld['id'],
                        ignore_errors=lib_exc.NotFound)

        body = self.admin_client.list_tlds()[1]

        self.assertGreater(len(body['tlds']), 0)

        # Test RBAC
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader']
        else:
            expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'TldClient', 'list_tlds', expected_allowed, [tld['id']],
            params={'limit': 1000})

    @decorators.idempotent_id('1a233812-48d9-4d15-af5e-9961744286ff')
    def test_update_tld(self):
        tld_name = self._generate_tld_name("test_update_tld")
        tld = self.admin_client.create_tld(tld_name)[1]
        self.addCleanup(self.admin_client.delete_tld, tld['id'])

        tld_name_2 = self._generate_tld_name("test_update_tld")

        tld_data = {
                     "name": tld_name_2,
                     "description": "Updated description"
        }

        LOG.info('Update the tld')
        patch_tld = self.admin_client.update_tld(tld['id'],
                       tld_data['name'], tld_data['description'])[1]

        self.assertEqual(tld_name_2, patch_tld["name"])
        self.assertEqual(tld_data["description"], patch_tld["description"])

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'TldClient', 'update_tld', expected_allowed, False, tld['id'],
            tld_data['name'], tld_data['description'])

    @decorators.idempotent_id('8116dcf5-a329-47d1-90be-5ff32f299c53')
    def test_list_tlds_dot_json_fails(self):
        uri = self.admin_client.get_uri('tlds.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.admin_client.get(uri))


class TestTldNotFoundAdmin(BaseTldTest):

    credentials = ["admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTldNotFoundAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTldNotFoundAdmin, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.TldClient()

    @decorators.idempotent_id('b237d5ee-0d76-4294-a3b6-c2f8bf4b0e30')
    def test_show_tld_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.show_tld,
                              data_utils.rand_uuid())
        self.assertTld404(e.resp, e.resp_body)

    @decorators.idempotent_id('3d128772-7f52-4473-b569-51ae8294667b')
    def test_update_tld_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.update_tld,
                              data_utils.rand_uuid())
        self.assertTld404(e.resp, e.resp_body)

    @decorators.idempotent_id('18e465e7-5c7d-4775-acef-bd12a8db1095')
    def test_delete_tld_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.delete_tld,
                              data_utils.rand_uuid())
        self.assertTld404(e.resp, e.resp_body)

    def assertTld404(self, resp, resp_body):
        self.assertEqual(404, resp.status)
        self.assertEqual(404, resp_body['code'])
        self.assertEqual("tld_not_found", resp_body['type'])
        self.assertEqual("Could not find Tld", resp_body['message'])


class TestTldInvalidIdAdmin(BaseTldTest):

    credentials = ["admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTldInvalidIdAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTldInvalidIdAdmin, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.TldClient()

    @decorators.idempotent_id('f9ec0730-57ff-4720-8d06-e11d377c7cfc')
    def test_show_tld_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.show_tld,
                              'foo')
        self.assertTldInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('13dc6518-b479-4502-90f5-f5a5ecc8b1fb')
    def test_update_tld_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.update_tld,
                              'foo')
        self.assertTldInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('6a6fc9db-9a73-4ffc-831a-172e1cbc7394')
    def test_delete_tld_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.delete_tld,
                              'foo')
        self.assertTldInvalidId(e.resp, e.resp_body)

    def assertTldInvalidId(self, resp, resp_body):
        self.assertEqual(400, resp.status)
        self.assertEqual(400, resp_body['code'])
        self.assertEqual("invalid_uuid", resp_body['type'])
        self.assertEqual("Invalid UUID tld_id: foo",
                         resp_body['message'])
