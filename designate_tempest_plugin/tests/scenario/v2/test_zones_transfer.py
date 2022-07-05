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
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from designate_tempest_plugin.common import constants as const

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


class ZonesTransferTest(base.BaseDnsV2Test):
    credentials = ['primary', 'alt', 'admin', 'system_admin']

    @classmethod
    def setup_clients(cls):
        super(ZonesTransferTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_zones_client = cls.os_system_admin.dns_v2.ZonesClient()
            cls.admin_accept_client = (
                cls.os_system_admin.dns_v2.TransferAcceptClient())
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_zones_client = cls.os_admin.dns_v2.ZonesClient()
            cls.admin_accept_client = (
                cls.os_admin.dns_v2.TransferAcceptClient())
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
        cls.zones_client = cls.os_primary.dns_v2.ZonesClient()
        cls.alt_zones_client = cls.os_alt.dns_v2.ZonesClient()
        cls.request_client = cls.os_primary.dns_v2.TransferRequestClient()
        cls.alt_request_client = cls.os_alt.dns_v2.TransferRequestClient()
        cls.accept_client = cls.os_primary.dns_v2.TransferAcceptClient()
        cls.alt_accept_client = cls.os_alt.dns_v2.TransferAcceptClient()

    @classmethod
    def resource_setup(cls):
        super(ZonesTransferTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="ZonesTransferTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(ZonesTransferTest, cls).resource_cleanup()

    @decorators.idempotent_id('60bd80ac-c979-4686-9a03-f2f775f272ab')
    def test_zone_transfer(self):
        LOG.info('Create a zone as primary tenant')
        zone_name = dns_data_utils.rand_zone_name(
            name="zone_transfer", suffix=self.tld_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Create a zone transfer_request for zone as primary tenant')
        transfer_request = (
            self.request_client.create_transfer_request_empty_body(
                zone['id'])[1])
        self.addCleanup(self.request_client.delete_transfer_request,
                        transfer_request['id'],
                        ignore_errors=lib_exc.NotFound)

        accept_data = {
                 "key": transfer_request['key'],
                 "zone_transfer_request_id": transfer_request['id']
        }

        LOG.info('Accept the request as alt tenant')
        transfer_accept = self.alt_accept_client.create_transfer_accept(
            accept_data)[1]

        LOG.info('Ensure we respond with COMPLETE status')
        show_request = self.request_client.show_transfer_request(
            transfer_request['id'])[1]
        self.assertEqual(const.COMPLETE, show_request['status'])

        LOG.info('Fetch the zone as alt tenant')
        alt_zone = self.alt_zones_client.show_zone(zone['id'])[1]
        self.addCleanup(self.wait_zone_delete,
                        self.alt_zones_client,
                        alt_zone['id'])

        LOG.info('Ensure 404 when fetching the zone as primary tenant')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.zones_client.show_zone(zone['id']))

        LOG.info('Accept the request as admin tenant, should fail '
                 'with: "invalid_zone_transfer_request"')
        with self.assertRaisesDns(
                lib_exc.BadRequest, 'invalid_zone_transfer_request', 400):
            self.admin_accept_client.create_transfer_accept(accept_data)

        LOG.info('Delete the transfer_request')
        self.request_client.delete_transfer_request(transfer_request['id'])[1]

        LOG.info('Validation that transfer_accept deleted'
                 ' after the transfer_request delete')
        self.assertRaises(lib_exc.NotFound,
                          self.accept_client.show_transfer_accept,
                          transfer_accept['id'])

    @decorators.idempotent_id('5855b772-a036-11eb-9973-74e5f9e2a801')
    def test_zone_transfer_target_project(self):
        LOG.info('Create a zone as "primary" tenant')
        zone_name = dns_data_utils.rand_zone_name(
            name="zone_transfer_target_project", suffix=self.tld_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]

        LOG.info('Create transfer_request with target project set to '
                 '"Admin" tenant')
        transfer_request_data = dns_data_utils.rand_transfer_request_data(
            target_project_id=self.os_admin.credentials.project_id)
        transfer_request = self.request_client.create_transfer_request(
            zone['id'], transfer_request_data)[1]
        self.addCleanup(self.request_client.delete_transfer_request,
                        transfer_request['id'])
        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual(const.ACTIVE, transfer_request['status'])

        LOG.info('Accept the request as "alt" tenant, Expected: should fail '
                 'as "admin" was set as a target project.')
        accept_data = {
                 "key": transfer_request['key'],
                 "zone_transfer_request_id": transfer_request['id']
        }
        self.assertRaises(
            lib_exc.Forbidden, self.alt_accept_client.create_transfer_accept,
            transfer_accept_data=accept_data)

        LOG.info('Accept the request as "Admin" tenant, Expected: should work')
        self.admin_accept_client.create_transfer_accept(
            accept_data, headers={'x-auth-sudo-project-id':
                                  self.os_admin.credentials.project_id},
            extra_headers=True)
        LOG.info('Fetch the zone as "Admin" tenant')
        admin_zone = self.admin_zones_client.show_zone(
            zone['id'], headers={'x-auth-sudo-project-id':
                                 self.os_admin.credentials.project_id})[1]
        self.addCleanup(self.wait_zone_delete,
                        self.admin_zones_client,
                        admin_zone['id'])
