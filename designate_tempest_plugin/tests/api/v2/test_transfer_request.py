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
from designate_tempest_plugin import data_utils as dns_data_utils

LOG = logging.getLogger(__name__)


class BaseTransferRequestTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'key', 'links']


class TransferRequestTest(BaseTransferRequestTest):
    credentials = ['primary', 'alt']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TransferRequestTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TransferRequestTest, cls).setup_clients()

        cls.zone_client = cls.os_primary.zones_client
        cls.client = cls.os_primary.transfer_request_client
        cls.alt_client = cls.os_alt.transfer_request_client

    @decorators.idempotent_id('2381d489-ad84-403d-b0a2-8b77e4e966bf')
    def test_create_transfer_request(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('ACTIVE', transfer_request['status'])

    @decorators.idempotent_id('5deae1ac-7c14-42dc-b14e-4e4b2725beb7')
    def test_create_transfer_request_scoped(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        transfer_request_data = dns_data_utils.rand_transfer_request_data(
            target_project_id=self.os_alt.credentials.project_id)

        LOG.info('Create a scoped zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(
            zone['id'], transfer_request_data)
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('ACTIVE', transfer_request['status'])

    @decorators.idempotent_id('4505152f-0a9c-4f02-b385-2216c914a0be')
    def test_create_transfer_request_empty_body(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.client.create_transfer_request_empty_body(
            zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('ACTIVE', transfer_request['status'])

    @decorators.idempotent_id('64a7be9f-8371-4ce1-a242-c1190de7c985')
    def test_show_transfer_request(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Fetch the transfer_request')
        _, body = self.client.show_transfer_request(transfer_request['id'])

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_request')
        self.assertExpected(transfer_request, body, self.excluded_keys)

    @decorators.idempotent_id('235ded87-0c47-430b-8cad-4f3194b927a6')
    def test_show_transfer_request_as_target(self):
        # Checks the target of a scoped transfer request can see
        # the request.
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        transfer_request_data = dns_data_utils.rand_transfer_request_data(
            target_project_id=self.os_alt.credentials.project_id)

        LOG.info('Create a scoped zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(
            zone['id'], transfer_request_data)
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Fetch the transfer_request as the target')
        _, body = self.alt_client.show_transfer_request(transfer_request['id'])

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_request')
        excluded_keys = self.excluded_keys + ["target_project_id",
                                              "project_id"]
        self.assertExpected(transfer_request, body, excluded_keys)

    @decorators.idempotent_id('7d81c487-aa15-44c4-b3e5-424ab9e6a3e5')
    def test_delete_transfer_request(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the transfer_request')
        _, body = self.client.delete_transfer_request(transfer_request['id'])
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.show_transfer_request(transfer_request['id']))

    @decorators.idempotent_id('ddd42a19-1768-428c-846e-32f9d6493011')
    def test_list_transfer_requests(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.client.create_transfer_request(zone['id'])
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('List transfer_requests')
        _, body = self.client.list_transfer_requests()

        self.assertGreater(len(body['transfer_requests']), 0)

    @decorators.idempotent_id('de5e9d32-c723-4518-84e5-58da9722cc13')
    def test_update_transfer_request(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

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

    @decorators.idempotent_id('73b754a9-e856-4fd6-80ba-e8d1b80f5dfa')
    def test_list_transfer_requests_dot_json_fails(self):
        uri = self.client.get_uri('transfer_requests.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.get(uri))


class TestTransferRequestNotFound(BaseTransferRequestTest):

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTransferRequestNotFound, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTransferRequestNotFound, cls).setup_clients()
        cls.client = cls.os_primary.transfer_request_client

    @decorators.idempotent_id('d255f72f-ba24-43df-9dba-011ed7f4625d')
    def test_show_transfer_request_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.client.show_transfer_request,
                              data_utils.rand_uuid())
        self.assertTransferRequest404(e.resp, e.resp_body)

    @decorators.idempotent_id('9ff383fb-c31d-4c6f-8085-7b261e401223')
    def test_update_transfer_request_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.client.update_transfer_request,
                              data_utils.rand_uuid())
        self.assertTransferRequest404(e.resp, e.resp_body)

    @decorators.idempotent_id('5a4a0755-c01d-448f-b856-b081b96ae77e')
    def test_delete_transfer_request_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.client.delete_transfer_request,
                              data_utils.rand_uuid())
        self.assertTransferRequest404(e.resp, e.resp_body)

    def assertTransferRequest404(self, resp, resp_body):
        self.assertEqual(404, resp.status)
        self.assertEqual(404, resp_body['code'])
        self.assertEqual("zone_transfer_request_not_found", resp_body['type'])
        self.assertEqual("Could not find ZoneTransferRequest",
                         resp_body['message'])


class TestTransferRequestInvalidId(BaseTransferRequestTest):

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTransferRequestInvalidId, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTransferRequestInvalidId, cls).setup_clients()
        cls.client = cls.os_primary.transfer_request_client

    @decorators.idempotent_id('2205dd19-ecc7-4c68-9e89-63c47d642b07')
    def test_show_transfer_request_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.client.show_transfer_request,
                              'foo')
        self.assertTransferRequestInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('af0ce46f-10be-4cce-a1d5-1b5c2a39fb97')
    def test_update_transfer_request_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.client.update_transfer_request,
                              'foo')
        self.assertTransferRequestInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('1728dca5-01f1-45f4-b59d-7a981d479394')
    def test_delete_transfer_request_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.client.delete_transfer_request,
                              'foo')
        self.assertTransferRequestInvalidId(e.resp, e.resp_body)

    def assertTransferRequestInvalidId(self, resp, resp_body):
        self.assertEqual(400, resp.status)
        self.assertEqual(400, resp_body['code'])
        self.assertEqual("invalid_uuid", resp_body['type'])
