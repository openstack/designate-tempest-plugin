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
from tempest import test
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class BaseTldTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'links']


class TldAdminTest(BaseTldTest):
    credentials = ['admin']

    @classmethod
    def setup_clients(cls):
        super(TldAdminTest, cls).setup_clients()
        cls.admin_client = cls.os_adm.tld_client

    @classmethod
    def resource_setup(cls):
        super(TldAdminTest, cls).resource_setup()
        cls.tld = cls.admin_client.create_tld(tld_name='com',
                      ignore_errors=lib_exc.Conflict)

    @test.attr(type='smoke')
    @test.idempotent_id('52a4bb4b-4eff-4591-9dd3-ad98316806c3')
    def test_create_tld(self):
        tld_data = {
                     "name": "org",
                     "description": "sample tld"}

        LOG.info('Create a tld')
        _, tld = self.admin_client.create_tld(tld_data['name'],
                                        tld_data['description'])
        self.addCleanup(self.admin_client.delete_tld, tld['id'])

        self.assertEqual(tld_data["name"], tld['name'])

    @test.attr(type='smoke')
    @test.idempotent_id('271af08c-2603-4f61-8eb1-05887b74e25a')
    def test_show_tld(self):
        tld_data = {
                     "name": "org",
                     "description": "sample tld"}

        LOG.info('Create a tld')
        _, tld = self.admin_client.create_tld(tld_data['name'],
                                        tld_data['description'])
        self.addCleanup(self.admin_client.delete_tld, tld['id'])

        LOG.info('Fetch the tld')
        _, body = self.admin_client.show_tld(tld['id'])

        LOG.info('Ensure the fetched response matches the created tld')
        self.assertExpected(tld, body, self.excluded_keys)

    @test.attr(type='smoke')
    @test.idempotent_id('26708cb8-7126-48a7-9424-1c225e56e609')
    def test_delete_tld(self):
        LOG.info('Create a tld')
        _, tld = self.admin_client.create_tld()
        self.addCleanup(self.admin_client.delete_tld, tld['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the tld')
        _, body = self.admin_client.delete_tld(tld['id'])

        self.assertRaises(lib_exc.NotFound,
           lambda: self.admin_client.show_tld(tld['id']))

    @test.attr(type='smoke')
    @test.idempotent_id('95b13759-c85c-4791-829b-9591ca15779d')
    def test_list_tlds(self):
        LOG.info('List tlds')
        _, body = self.admin_client.list_tlds()

        self.assertGreater(len(body['tlds']), 0)

    @test.attr(type='smoke')
    @test.idempotent_id('1a233812-48d9-4d15-af5e-9961744286ff')
    def test_update_tld(self):
        _, tld = self.admin_client.create_tld()
        self.addCleanup(self.admin_client.delete_tld, tld['id'])

        tld_data = {
                     "name": "org",
                     "description": "Updated description"
        }

        LOG.info('Update the tld')
        _, patch_tld = self.admin_client.update_tld(tld['id'],
                       tld_data['name'], tld_data['description'])

        self.assertEqual(tld_data["name"], patch_tld["name"])
        self.assertEqual(tld_data["description"], patch_tld["description"])

    @test.attr(type='smoke')
    @test.idempotent_id('8116dcf5-a329-47d1-90be-5ff32f299c53')
    def test_list_tlds_dot_json_fails(self):
        uri = self.admin_client.get_uri('tlds.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.admin_client.get(uri))
