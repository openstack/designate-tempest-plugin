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
from tempest import test
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class BasePoolTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'links', 'ns_records']

    def _assertExpectedNSRecords(self, expected, actual, expected_key):
        sort_expected = sorted(expected, key=itemgetter(expected_key))
        sort_actual = sorted(actual, key=itemgetter(expected_key))
        self.assertEqual(sort_expected, sort_actual)


class PoolAdminTest(BasePoolTest):
    credentials = ['admin']

    @classmethod
    def setup_clients(cls):
        super(PoolAdminTest, cls).setup_clients()

        cls.admin_client = cls.os_adm.pool_client

    @test.attr(type='smoke')
    @test.idempotent_id('69257f7c-b3d5-4e1b-998e-0677ad12f125')
    def test_create_pool(self):
        pool_data = {
                      "name": "Example Pool",
                      "ns_records": [{
                          "hostname": "ns1.example.org.",
                          "priority": 1}
                      ]
                    }
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool(pool_name=pool_data["name"],
                      ns_records=pool_data["ns_records"])
        self.addCleanup(self.admin_client.delete_pool, pool['id'])

        self.assertEqual(pool_data["name"], pool['name'])
        self.assertExpected(pool_data, pool, self.excluded_keys)

    @test.attr(type='smoke')
    @test.idempotent_id('e80eb70a-8ee5-40eb-b06e-599597a8ab7e')
    def test_show_pool(self):
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool()
        self.addCleanup(self.admin_client.delete_pool, pool['id'])

        LOG.info('Fetch the pool')
        _, body = self.admin_client.show_pool(pool['id'])

        LOG.info('Ensure the fetched response matches the created pool')
        self.assertExpected(pool, body, self.excluded_keys)
        self._assertExpectedNSRecords(pool["ns_records"], body["ns_records"],
                                expected_key="priority")

    @test.attr(type='smoke')
    @test.idempotent_id('d8c4c377-5d88-452d-a4d2-c004d72e1abe')
    def test_delete_pool(self):
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool()
        self.addCleanup(self.admin_client.delete_pool, pool['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the pool')
        _, body = self.admin_client.delete_pool(pool['id'])

        self.assertRaises(lib_exc.NotFound,
           lambda: self.admin_client.show_pool(pool['id']))

    @test.attr(type='smoke')
    @test.idempotent_id('77c85b40-83b2-4c17-9fbf-e6d516cfce90')
    def test_list_pools(self):
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool()
        self.addCleanup(self.admin_client.delete_pool, pool['id'])

        LOG.info('List pools')
        _, body = self.admin_client.list_pools()

        self.assertGreater(len(body['pools']), 0)

    @test.attr(type='smoke')
    @test.idempotent_id('fdcc84ce-af65-4af6-a5fc-6c50acbea0f0')
    def test_update_pool(self):
        LOG.info('Create a pool')
        _, pool = self.admin_client.create_pool()
        self.addCleanup(self.admin_client.delete_pool, pool['id'])

        LOG.info('Update the pool')
        _, patch_pool = self.admin_client.update_pool(
            pool['id'], pool_name="foo")

        self.assertEqual("foo", patch_pool["name"])

    @test.attr(type='smoke')
    @test.idempotent_id('41ad6a84-00ce-4a04-9fd5-b7c15c31e2db')
    def test_list_pools_dot_json_fails(self):
        uri = self.admin_client.get_uri('pools.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.admin_client.get(uri))
