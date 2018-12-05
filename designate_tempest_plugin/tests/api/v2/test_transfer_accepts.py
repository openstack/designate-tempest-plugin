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
from tempest.lib import decorators

from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class BaseTransferAcceptTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'key', 'links',
                    'zone_name']


class TransferAcceptTest(BaseTransferAcceptTest):
    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TransferAcceptTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TransferAcceptTest, cls).setup_clients()

        cls.zone_client = cls.os_primary.zones_client
        cls.request_client = cls.os_primary.transfer_request_client
        cls.client = cls.os_primary.transfer_accept_client

    @decorators.idempotent_id('1c6baf97-a83e-4d2e-a5d8-9d37fb7808f3')
    def test_create_transfer_accept(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.request_client.create_transfer_request(
                                  zone['id'])
        self.addCleanup(self.request_client.delete_transfer_request,
                        transfer_request['id'])

        data = {
                 "key": transfer_request['key'],
                 "zone_transfer_request_id": transfer_request['id']
        }
        LOG.info('Create a zone transfer_accept')
        _, transfer_accept = self.client.create_transfer_accept(data)

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('COMPLETE', transfer_accept['status'])

    @decorators.idempotent_id('37c6afbb-3ea3-4fd8-94ea-a426244f019a')
    def test_show_transfer_accept(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.request_client.create_transfer_request(
                                  zone['id'])
        self.addCleanup(self.request_client.delete_transfer_request,
                        transfer_request['id'])

        data = {
            "key": transfer_request['key'],
            "zone_transfer_request_id": transfer_request['id']
        }

        LOG.info('Create a zone transfer_accept')
        _, transfer_accept = self.client.create_transfer_accept(data)

        LOG.info('Fetch the transfer_accept')
        _, body = self.client.show_transfer_accept(transfer_accept['id'])

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_accept')
        self.assertExpected(transfer_accept, body, self.excluded_keys)
