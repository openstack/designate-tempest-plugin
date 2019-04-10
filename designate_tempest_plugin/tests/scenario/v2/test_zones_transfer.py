# Copyright 2016 Rackspace
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
from oslo_log import log as logging
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class ZonesTransferTest(base.BaseDnsV2Test):
    credentials = ['primary', 'alt']

    @classmethod
    def setup_clients(cls):
        super(ZonesTransferTest, cls).setup_clients()
        cls.zones_client = cls.os_primary.zones_client
        cls.alt_zones_client = cls.os_alt.zones_client
        cls.request_client = cls.os_primary.transfer_request_client
        cls.alt_request_client = cls.os_alt.transfer_request_client
        cls.accept_client = cls.os_primary.transfer_accept_client
        cls.alt_accept_client = cls.os_alt.transfer_accept_client

    @decorators.idempotent_id('60bd80ac-c979-4686-9a03-f2f775f272ab')
    def test_zone_transfer(self):
        LOG.info('Create a zone as primary tenant')
        _, zone = self.zones_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Create a zone transfer_request for zone as primary tenant')
        _, transfer_request = \
            self.request_client.create_transfer_request_empty_body(zone['id'])
        self.addCleanup(self.request_client.delete_transfer_request,
                        transfer_request['id'])

        accept_data = {
                 "key": transfer_request['key'],
                 "zone_transfer_request_id": transfer_request['id']
        }

        LOG.info('Accept the request as alt tenant')
        self.alt_accept_client.create_transfer_accept(accept_data)

        LOG.info('Fetch the zone as alt tenant')
        _, alt_zone = self.alt_zones_client.show_zone(zone['id'])
        self.addCleanup(self.wait_zone_delete,
                        self.alt_zones_client,
                        alt_zone['id'])

        LOG.info('Ensure 404 when fetching the zone as primary tenant')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.zones_client.show_zone(zone['id']))
