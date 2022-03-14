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

from operator import itemgetter

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.lib.common.utils import data_utils

from designate_tempest_plugin.tests import base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BasePoolTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'links', 'ns_records']

    def _assertExpectedNSRecords(self, expected, actual, expected_key):
        sort_expected = sorted(expected, key=itemgetter(expected_key))
        sort_actual = sorted(actual, key=itemgetter(expected_key))
        self.assertEqual(sort_expected, sort_actual)


class PoolAdminTest(BasePoolTest):
    credentials = ["admin", "primary", "system_admin", "system_reader",
                   "project_member", "project_reader", "alt"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(PoolAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(PoolAdminTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.PoolClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.PoolClient()

    @decorators.idempotent_id('69257f7c-b3d5-4e1b-998e-0677ad12f125')
    def test_create_pool(self):
        pool_data = {
                      "name": "Example Pool",
                      "project_id": "1",
                      "ns_records": [{
                          "hostname": "ns1.example.org.",
                          "priority": 1}
                      ]
                    }
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool(pool_name=pool_data["name"],
            ns_records=pool_data["ns_records"],
            project_id=pool_data["project_id"])
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        headers=self.all_projects_header)

        self.assertEqual(pool_data["name"], pool['name'])
        self.assertExpected(pool_data, pool, self.excluded_keys)

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'PoolClient', 'create_pool', expected_allowed, False,
            pool_name=pool_data["name"], ns_records=pool_data["ns_records"],
            project_id=pool_data["project_id"])

    @decorators.idempotent_id('e80eb70a-8ee5-40eb-b06e-599597a8ab7e')
    def test_show_pool(self):
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool(project_id="1")
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        headers=self.all_projects_header)

        LOG.info('Fetch the pool')
        _, body = self.admin_client.show_pool(
            pool['id'], headers=self.all_projects_header)

        LOG.info('Ensure the fetched response matches the created pool')
        self.assertExpected(pool, body, self.excluded_keys)
        self._assertExpectedNSRecords(pool["ns_records"], body["ns_records"],
                                expected_key="priority")

        # TODO(johnsom) Test reader roles once this bug is fixed.
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        # TODO(johnsom) The pools API seems inconsistent with the requirement
        #               of the all-projects header.
        self.check_list_show_RBAC_enforcement(
            'PoolClient', 'show_pool', expected_allowed, True, pool['id'],
            headers=self.all_projects_header)

    @decorators.idempotent_id('d8c4c377-5d88-452d-a4d2-c004d72e1abe')
    def test_delete_pool(self):
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool(project_id="1")
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        ignore_errors=lib_exc.NotFound,
                        headers=self.all_projects_header)

        LOG.info('Delete the pool')
        _, body = self.admin_client.delete_pool(
            pool['id'], headers=self.all_projects_header)

        self.assertRaises(lib_exc.NotFound,
           lambda: self.admin_client.show_pool(
               pool['id'], headers=self.all_projects_header))

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'PoolClient', 'delete_pool', expected_allowed, False, pool['id'])

    @decorators.idempotent_id('77c85b40-83b2-4c17-9fbf-e6d516cfce90')
    def test_list_pools(self):
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool(project_id="1")
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        headers=self.all_projects_header)

        LOG.info('List pools')
        _, body = self.admin_client.list_pools(
            headers=self.all_projects_header)

        self.assertGreater(len(body['pools']), 0)

        # TODO(johnsom) Test reader roles once this bug is fixed.
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'PoolClient', 'list_pools', expected_allowed, [pool['id']],
            headers=self.all_projects_header)

    @decorators.idempotent_id('fdcc84ce-af65-4af6-a5fc-6c50acbea0f0')
    def test_update_pool(self):
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool(project_id="1")
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        headers=self.all_projects_header)

        LOG.info('Update the pool')
        _, patch_pool = self.admin_client.update_pool(
            pool['id'], pool_name="foo", headers=self.all_projects_header,
            extra_headers=True)

        self.assertEqual("foo", patch_pool["name"])

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'PoolClient', 'update_pool', expected_allowed, True,
            pool['id'], pool_name="test-name")

    @decorators.idempotent_id('41ad6a84-00ce-4a04-9fd5-b7c15c31e2db')
    def test_list_pools_dot_json_fails(self):
        uri = self.admin_client.get_uri('pools.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.admin_client.get(uri))


class TestPoolNotFoundAdmin(BasePoolTest):

    credentials = ["admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestPoolNotFoundAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestPoolNotFoundAdmin, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.PoolClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.PoolClient()

    @decorators.idempotent_id('56281b2f-dd5a-4376-8c32-aba771062fa5')
    def test_show_pool_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.show_pool,
                              data_utils.rand_uuid())
        self.assertPool404(e.resp, e.resp_body)

    @decorators.idempotent_id('10fba3c2-9972-479c-ace1-8f7eac7c159f')
    def test_update_pool_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.update_pool,
                              data_utils.rand_uuid())
        self.assertPool404(e.resp, e.resp_body)

    @decorators.idempotent_id('96132295-896b-4de3-8f86-cc2ee513fdad')
    def test_delete_pool_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.delete_pool,
                              data_utils.rand_uuid())
        self.assertPool404(e.resp, e.resp_body)

    def assertPool404(self, resp, resp_body):
        self.assertEqual(404, resp.status)
        self.assertEqual(404, resp_body['code'])
        self.assertEqual("pool_not_found", resp_body['type'])
        self.assertEqual("Could not find Pool", resp_body['message'])


class TestPoolInvalidIdAdmin(BasePoolTest):

    credentials = ["admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestPoolInvalidIdAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestPoolInvalidIdAdmin, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.PoolClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.PoolClient()

    @decorators.idempotent_id('081d0188-42a7-4953-af0e-b022960715e2')
    def test_show_pool_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.show_pool,
                              'foo')
        self.assertPoolInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('f4ab4f5a-d7f0-4758-b232-8338f02d7c5c')
    def test_update_pool_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.update_pool,
                              'foo')
        self.assertPoolInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('bf5ad3be-2e79-439d-b247-902fe198143b')
    def test_delete_pool_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.delete_pool,
                              'foo')
        self.assertPoolInvalidId(e.resp, e.resp_body)

    def assertPoolInvalidId(self, resp, resp_body):
        self.assertEqual(400, resp.status)
        self.assertEqual(400, resp_body['code'])
        self.assertEqual("invalid_uuid", resp_body['type'])
        self.assertEqual("Invalid UUID pool_id: foo",
                         resp_body['message'])


class TestPoolAdminNegative(BasePoolTest):

    credentials = ["admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestPoolAdminNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestPoolAdminNegative, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.PoolClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.PoolClient()

    @decorators.idempotent_id('0a8cdc1e-ac02-11eb-ae06-74e5f9e2a801')
    def test_create_pool_invalid_name(self):
        LOG.info('Create a pool using a huge size string for name)')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self.admin_client.create_pool(
                pool_name=data_utils.rand_name(name="Huge_size_name") * 10000)

    @decorators.idempotent_id('9a787d0e-ac04-11eb-ae06-74e5f9e2a801')
    def test_create_pool_invalid_hostname_in_ns_records(self):
        LOG.info('Create a pool using invalid hostname in ns_records')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self.admin_client.create_pool(
                ns_records=[{"hostname": "ns1_example_org_", "priority": 1}])

    @decorators.idempotent_id('9a787d0e-ac04-11eb-ae06-74e5f9e2a801')
    def test_create_pool_invalid_priority_in_ns_records(self):
        LOG.info('Create a pool using invalid priority in ns_records')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self.admin_client.create_pool(
                ns_records=[{"hostname": "ns1.example.org.", "priority": -1}])

    @decorators.idempotent_id('cc378e4c-ac05-11eb-ae06-74e5f9e2a801')
    # Note: Update pool API is deprecated for removal.
    def test_update_pool_with_invalid_name(self):
        LOG.info('Create a pool')
        pool = self.admin_client.create_pool(project_id="1")[1]
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        headers=self.all_projects_header)

        LOG.info('Update the pool using a name that is too long')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self.admin_client.update_pool(
                pool['id'],
                pool_name=data_utils.rand_name(name="Huge_size_name") * 10000,
                headers=self.all_projects_header, extra_headers=True)

    @decorators.idempotent_id('2e496596-ac07-11eb-ae06-74e5f9e2a801')
    def test_update_pool_with_invalid_hostname_in_ns_records(self):
        # Note: Update pool API is deprecated for removal.
        LOG.info('Create a pool')
        pool = self.admin_client.create_pool(project_id="1")[1]
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        headers=self.all_projects_header)

        LOG.info('Update the pool using invalid hostname in ns_records')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self.admin_client.update_pool(
                pool['id'],
                ns_records=[{"hostname": "ns1_example_org_", "priority": 1}],
                headers=self.all_projects_header, extra_headers=True)

    @decorators.idempotent_id('3e934624-ac07-11eb-ae06-74e5f9e2a801')
    def test_update_pool_with_invalid_priority_in_ns_records(self):
        # Note: Update pool API is deprecated for removal.
        LOG.info('Create a pool')
        pool = self.admin_client.create_pool(project_id="1")[1]
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        headers=self.all_projects_header)

        LOG.info('Update the pool using invalid priority in ns_records')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self.admin_client.update_pool(
                pool['id'],
                ns_records=[{"hostname": "ns1.example.org.", "priority": -1}],
                headers=self.all_projects_header, extra_headers=True)
