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


class BaseTransferRequestTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'key', 'links',
                    'zone_name']


class TransferRequestTest(BaseTransferRequestTest):
    @classmethod
    def setup_clients(cls):
        super(TransferRequestTest, cls).setup_clients()

        cls.zone_client = cls.os.zones_client
        cls.client = cls.os.transfer_request_client

    @test.attr(type='smoke')
    @test.idempotent_id('2381d489-ad84-403d-b0a2-8b77e4e966bf')
    def test_create_transfer_request(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('ACTIVE', transfer_request['status'])

    @test.attr(type='smoke')
    @test.idempotent_id('64a7be9f-8371-4ce1-a242-c1190de7c985')
    def test_show_transfer_request(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Fetch the transfer_request')
        _, body = self.client.show_transfer_request(transfer_request['id'])

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_request')
        self.assertExpected(transfer_request, body, self.excluded_keys)

    @test.attr(type='smoke')
    @test.idempotent_id('7d81c487-aa15-44c4-b3e5-424ab9e6a3e5')
    def test_delete_transfer_request(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        LOG.info('Create a transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the transfer_request')
        _, body = self.client.delete_transfer_request(transfer_request['id'])
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.show_transfer_request(transfer_request['id']))

    @test.attr(type='smoke')
    @test.idempotent_id('ddd42a19-1768-428c-846e-32f9d6493011')
    def test_list_transfer_requests(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('List transfer_requests')
        _, body = self.client.list_transfer_requests()

        self.assertGreater(len(body['transfer_requests']), 0)

    @test.attr(type='smoke')
    @test.idempotent_id('de5e9d32-c723-4518-84e5-58da9722cc13')
    def test_update_transfer_request(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Update the transfer_request')
        data = {
                 "description": "demo descripion"
               }
        _, transfer_request_patch = self.client.update_transfer_request(
            transfer_request['id'], transfer_request_data=data)

        self.assertEqual(data['description'],
                         transfer_request_patch['description'])

    @test.attr(type='smoke')
    @test.idempotent_id('73b754a9-e856-4fd6-80ba-e8d1b80f5dfa')
    def test_list_transfer_requests_dot_json_fails(self):
        uri = self.client.get_uri('transfer_requests.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.get(uri))
