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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class BaseTsigkeyTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'links']


class TsigkeyAdminTest(BaseTsigkeyTest):
    credentials = ['primary', 'admin']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TsigkeyAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TsigkeyAdminTest, cls).setup_clients()
        cls.zone_client = cls.os_primary.zones_client
        cls.admin_client = cls.os_admin.tsigkey_client

    @decorators.idempotent_id('e7b484e3-7ed5-4840-89d7-1e696986f8e4')
    def test_create_tsigkey(self):
        LOG.info('Create a resource')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        tsigkey_data = {
                        "name": "Example tsigkey",
                        "algorithm": "hmac-sha256",
                        "secret": "SomeSecretKey",
                        "scope": "POOL",
                        "resource_id": zone['id']}

        LOG.info('Create a tsigkey')
        _, tsigkey = self.admin_client.create_tsigkey(
                         tsigkey_data['resource_id'],
                         tsigkey_data['name'], tsigkey_data['algorithm'],
                         tsigkey_data['secret'], tsigkey_data['scope'])
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])

        self.assertEqual(tsigkey_data["name"], tsigkey['name'])

    @decorators.idempotent_id('d46e5e86-a18c-4315-aa0c-95a00e816fbf')
    def test_list_tsigkey(self):
        LOG.info('Create a resource')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        LOG.info('Create a tsigkey')
        _, tsigkey = self.admin_client.create_tsigkey(resource_id=zone['id'])
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])
        _, body = self.admin_client.list_tsigkeys()
        self.assertGreater(len(body['tsigkeys']), 0)

    @decorators.idempotent_id('c5d7facf-0f05-47a2-a4fb-87f203860880')
    def test_show_tsigkey(self):
        LOG.info('Create a resource')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a tsigkey')
        _, tsigkey = self.admin_client.create_tsigkey(resource_id=zone['id'])
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])

        LOG.info('Fetch the tsigkey')
        _, body = self.admin_client.show_tsigkey(tsigkey['id'])

        LOG.info('Ensure the fetched response matches the created tsigkey')
        self.assertExpected(tsigkey, body, self.excluded_keys)

    @decorators.idempotent_id('d09dc0dd-dd72-41ee-9085-2afb2bf35459')
    def test_update_tsigkey(self):
        LOG.info('Create a resource')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a tsigkey')
        _, tsigkey = self.admin_client.create_tsigkey(resource_id=zone['id'])
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])

        tsigkey_data = {
                        "name": "Patch tsigkey",
                        "secret": "NewSecretKey",
                        "scope": "POOL"}

        LOG.info('Update the tsigkey')
        _, patch_tsigkey = self.admin_client.update_tsigkey(tsigkey['id'],
                               name=tsigkey_data['name'],
                               secret=tsigkey_data['secret'],
                               scope=tsigkey_data['scope'])

        self.assertEqual(tsigkey_data['name'], patch_tsigkey['name'])
        self.assertEqual(tsigkey_data['secret'], patch_tsigkey['secret'])
        self.assertEqual(tsigkey_data['scope'], patch_tsigkey['scope'])

    @decorators.idempotent_id('9cdffbd2-bc67-4a25-8eb7-4be8635c88a3')
    def test_delete_tsigkey(self):
        LOG.info('Create a resource')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a tsigkey')
        _, tsigkey = self.admin_client.create_tsigkey(resource_id=zone['id'])

        LOG.info('Delete the tsigkey')
        _, body = self.admin_client.delete_tsigkey(tsigkey['id'])

        self.assertRaises(lib_exc.NotFound,
           lambda: self.admin_client.show_tsigkey(tsigkey['id']))

    @decorators.idempotent_id('4bdc20ef-96f9-47f6-a1aa-275159af326b')
    def test_list_tsigkeys_dot_json_fails(self):
        uri = self.admin_client.get_uri('tsigkeys.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.admin_client.get(uri))


class TestTsigkeyNotFoundAdmin(BaseTsigkeyTest):

    credentials = ["admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTsigkeyNotFoundAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTsigkeyNotFoundAdmin, cls).setup_clients()
        cls.admin_client = cls.os_admin.tsigkey_client

    @decorators.idempotent_id('824c9b49-edc5-4282-929e-467a158d23e4')
    def test_show_tsigkey_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.show_tsigkey,
                              data_utils.rand_uuid())
        self.assertTsigkey404(e.resp, e.resp_body)

    @decorators.idempotent_id('4ef3493a-ee66-4c62-b070-c57fa9568b69')
    def test_update_tsigkey_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.update_tsigkey,
                              data_utils.rand_uuid())
        self.assertTsigkey404(e.resp, e.resp_body)

    @decorators.idempotent_id('ba438ede-4823-4922-8f4c-8de278f3d454')
    def test_delete_tsigkey_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.delete_tsigkey,
                              data_utils.rand_uuid())
        self.assertTsigkey404(e.resp, e.resp_body)

    def assertTsigkey404(self, resp, resp_body):
        self.assertEqual(404, resp.status)
        self.assertEqual(404, resp_body['code'])
        self.assertEqual("tsigkey_not_found", resp_body['type'])
        self.assertEqual("Could not find TsigKey", resp_body['message'])


class TestTsigkeyInvalidIdAdmin(BaseTsigkeyTest):

    credentials = ["admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTsigkeyInvalidIdAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTsigkeyInvalidIdAdmin, cls).setup_clients()
        cls.admin_client = cls.os_admin.tsigkey_client

    @decorators.idempotent_id('2a8dfc75-9884-4b1c-8f1f-ed835d96f2fe')
    def test_show_tsigkey_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.show_tsigkey,
                              'foo')
        self.assertTsigkeyInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('2befa10f-fc42-4ae9-9276-672e23f045f2')
    def test_update_tsigkey_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.update_tsigkey,
                              'foo')
        self.assertTsigkeyInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('55c2fea0-ead6-44c7-8bb1-05111412afdd')
    def test_delete_tsigkey_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.delete_tsigkey,
                              'foo')
        self.assertTsigkeyInvalidId(e.resp, e.resp_body)

    def assertTsigkeyInvalidId(self, resp, resp_body):
        self.assertEqual(400, resp.status)
        self.assertEqual(400, resp_body['code'])
        self.assertEqual("invalid_uuid", resp_body['type'])
        self.assertEqual("Invalid UUID tsigkey_id: foo",
                         resp_body['message'])
