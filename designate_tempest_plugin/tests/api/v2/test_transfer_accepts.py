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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseTransferAcceptTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'key', 'links',
                    'zone_name']

    @classmethod
    def setup_clients(cls):
        super(BaseTransferAcceptTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(BaseTransferAcceptTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="BaseTransferAcceptTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(BaseTransferAcceptTest, cls).resource_cleanup()


class TransferAcceptTest(BaseTransferAcceptTest):
    credentials = ["primary", "alt", "admin", "system_admin", "system_reader",
                   "project_member", "project_reader"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TransferAcceptTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TransferAcceptTest, cls).setup_clients()

        # Primary clients
        cls.prm_zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.prm_request_client = cls.os_primary.dns_v2.TransferRequestClient()
        cls.prm_accept_client = cls.os_primary.dns_v2.TransferAcceptClient()

        # Alt clients
        cls.alt_zone_client = cls.os_alt.dns_v2.ZonesClient()
        cls.alt_request_client = cls.os_alt.dns_v2.TransferRequestClient()
        cls.alt_accept_client = cls.os_alt.dns_v2.TransferAcceptClient()

        # Admin clients
        if CONF.enforce_scope.designate:
            cls.admin_zone_client = cls.os_system_admin.dns_v2.ZonesClient()
            cls.admin_request_client = (cls.os_system_admin.dns_v2.
                                        TransferRequestClient())
            cls.admin_accept_client = (cls.os_system_admin.dns_v2.
                                       TransferAcceptClient())
        else:
            cls.admin_zone_client = cls.os_admin.dns_v2.ZonesClient()
            cls.admin_request_client = (cls.os_admin.dns_v2.
                                        TransferRequestClient())
            cls.admin_accept_client = (cls.os_admin.dns_v2.
                                       TransferAcceptClient())

    @decorators.idempotent_id('1c6baf97-a83e-4d2e-a5d8-9d37fb7808f3')
    def test_create_transfer_accept(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_transfer_accept", suffix=self.tld_name)
        zone = self.prm_zone_client.create_zone(name=zone_name,
                                                wait_until='ACTIVE')[1]
        self.addCleanup(
            self.wait_zone_delete, self.admin_zone_client, zone['id'],
            headers=self.all_projects_header,
            ignore_errors=lib_exc.NotFound)

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.prm_request_client.create_transfer_request(
            zone['id'])
        self.addCleanup(
            self.transfer_request_delete,
            self.prm_request_client,
            transfer_request['id']
        )

        data = {
                 "key": transfer_request['key'],
                 "zone_transfer_request_id": transfer_request['id']
        }

        # Test RBAC
        # Note: Everyone can call this API and succeed if they know the
        #       transfer key.
        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')
            expected_allowed.append('os_system_reader')
            expected_allowed.append('os_project_member')
            expected_allowed.append('os_project_reader')

        self.check_CUD_RBAC_enforcement(
            'TransferAcceptClient', 'create_transfer_accept',
            expected_allowed, True, data)

        LOG.info('Create a zone transfer_accept')
        _, transfer_accept = self.prm_accept_client.create_transfer_accept(
            data)

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('COMPLETE', transfer_accept['status'])

    @decorators.idempotent_id('37c6afbb-3ea3-4fd8-94ea-a426244f019a')
    def test_show_transfer_accept(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(name="show_transfer_accept",
                                              suffix=self.tld_name)
        zone = self.prm_zone_client.create_zone(name=zone_name,
                                                wait_until='ACTIVE')[1]
        self.addCleanup(
            self.wait_zone_delete, self.admin_zone_client, zone['id'],
            headers=self.all_projects_header,
            ignore_errors=lib_exc.NotFound)

        LOG.info('Create a zone transfer_request')
        _, transfer_request = self.prm_request_client.create_transfer_request(
                                  zone['id'])
        self.addCleanup(
            self.transfer_request_delete,
            self.prm_request_client,
            transfer_request['id']
        )

        data = {
            "key": transfer_request['key'],
            "zone_transfer_request_id": transfer_request['id']
        }

        LOG.info('Create a zone transfer_accept')
        _, transfer_accept = self.prm_accept_client.create_transfer_accept(
            data)

        LOG.info('Fetch the transfer_accept')
        _, body = self.prm_accept_client.show_transfer_accept(
            transfer_accept['id'])

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_accept')
        self.assertExpected(transfer_accept, body, self.excluded_keys)

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC
        expected_allowed = ['os_primary']

        self.check_list_show_RBAC_enforcement(
            'TransferAcceptClient', 'show_transfer_accept', expected_allowed,
            True, transfer_accept['id'])

        # Test RBAC with x-auth-all-projects
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'TransferAcceptClient', 'show_transfer_accept', expected_allowed,
            True, transfer_accept['id'], headers=self.all_projects_header)

    @decorators.idempotent_id('89b516f0-8c9f-11eb-a322-74e5f9e2a801')
    def test_ownership_transferred_zone(self):

        LOG.info('Create a Primary zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="ownership_transferred_zone", suffix=self.tld_name)
        zone = self.prm_zone_client.create_zone(name=zone_name,
                                                wait_until='ACTIVE')[1]
        self.addCleanup(
            self.wait_zone_delete, self.admin_zone_client, zone['id'],
            headers=self.all_projects_header,
            ignore_errors=lib_exc.NotFound)

        LOG.info('Create a Primary zone transfer_request')
        transfer_request = self.prm_request_client.create_transfer_request(
            zone['id'])[1]
        self.addCleanup(
            self.transfer_request_delete,
            self.prm_request_client,
            transfer_request['id']
        )

        data = {
            "key": transfer_request['key'],
            "zone_transfer_request_id": transfer_request['id']
        }
        LOG.info('Create an Alt zone transfer_accept')
        transfer_accept = self.alt_accept_client.create_transfer_accept(
            data)[1]

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('COMPLETE', transfer_accept['status'])

        # Make sure that the "project_id" of transferred zone has been changed
        alt_transferred_zone = self.alt_zone_client.show_zone(zone['id'])[1]

        self.assertNotEqual(
            zone['project_id'], alt_transferred_zone['project_id'],
            'Failed, shown "project_id" for a transferred zone:{} should be '
            'different than the original "project_id" used in '
            'creation {}:'.format(
                alt_transferred_zone['project_id'], zone['project_id']))

    @decorators.idempotent_id('0fcd314c-8cae-11eb-a322-74e5f9e2a801')
    def test_list_transfer_accepts(self):
        """Test list API including filtering result option"""

        number_of_zones_to_transfer = 3
        transfer_request_ids = []
        for _ in range(number_of_zones_to_transfer):

            LOG.info('Create a Primary zone')
            zone_name = dns_data_utils.rand_zone_name(
                name="list_transfer_accepts", suffix=self.tld_name)
            zone = self.prm_zone_client.create_zone(name=zone_name,
                                                    wait_until='ACTIVE')[1]
            self.addCleanup(
                self.wait_zone_delete, self.admin_zone_client, zone['id'],
                headers=self.all_projects_header,
                ignore_errors=lib_exc.NotFound)

            LOG.info('Create a Primary zone transfer_request')
            transfer_request = self.prm_request_client.create_transfer_request(
                zone['id'])[1]
            self.addCleanup(
                self.transfer_request_delete,
                self.prm_request_client,
                transfer_request['id']
            )

            data = {
                "key": transfer_request['key'],
                "zone_transfer_request_id": transfer_request['id']
            }
            LOG.info('Create an Alt zone transfer_accept')
            transfer_accept = self.alt_accept_client.create_transfer_accept(
                data)[1]

            LOG.info('Ensure we respond with COMPLETE status')
            self.assertEqual('COMPLETE', transfer_accept['status'])
            transfer_request_ids.append(transfer_accept['id'])

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC - Users that are allowed to call list, but should get
        #             zero zones.
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader']
        else:
            expected_allowed = ['os_admin']

        self.check_list_RBAC_enforcement_count(
            'TransferAcceptClient', 'list_transfer_accept',
            expected_allowed, 0)

        # Test that users who should see the zone, can see it.
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'TransferAcceptClient', 'list_transfer_accept',
            expected_allowed, transfer_request_ids,
            headers=self.all_projects_header)

        # As Admin list all accepted zone transfers, expected:
        # each previously transferred zone is listed.
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        LOG.info('Use Admin client to list all "accepted zone transfers"')
        admin_client_accept_ids = [
            item['id'] for item in
            self.admin_accept_client.list_transfer_accept(
                headers=self.all_projects_header,
                params={'limit': 1000})[1]['transfer_accepts']]
        for tr_id in transfer_request_ids:
            self.assertIn(
                tr_id, admin_client_accept_ids,
                'Failed, expected transfer accept ID:{} is not listed in'
                ' transfer accept IDs:{} '.format(tr_id, transfer_request_ids))

        # As Admin list all accepted zone transfers in COMPLETE status only,
        # expected: each previously transferred zone is listed.
        LOG.info('Use Admin client to list all "accepted zone transfers", '
                 'filter COMPLETE status only accepts.')
        admin_client_accept_ids = [
            item['id'] for item in
            self.admin_accept_client.list_transfer_accept(
                headers=self.all_projects_header,
                params={'status': 'COMPLETE'})[1]['transfer_accepts']]
        for tr_id in transfer_request_ids:
            self.assertIn(
                tr_id, admin_client_accept_ids,
                'Failed, expected transfer accept ID:{} is not listed in'
                ' transfer accept IDs:{} '.format(
                    tr_id, transfer_request_ids))

        # As Admin list all accepted zone transfers in "non existing" status,
        # expected: received list is empty.
        not_existing_status = 'zahlabut'
        LOG.info('Use Admin client to list all "accepted zone transfers", '
                 'filter {} status only accepts.'.format(not_existing_status))
        admin_client_accept_ids = [
            item['id'] for item in
            self.admin_accept_client.list_transfer_accept(
                headers=self.all_projects_header,
                params={'status': not_existing_status})[1]['transfer_accepts']]
        self.assertEmpty(
            admin_client_accept_ids,
            "Failed, filtered list should be empty, but actually it's not, "
            "filtered IDs:{} ".format(admin_client_accept_ids))

    @decorators.idempotent_id('b6ac770e-a1d3-11eb-b534-74e5f9e2a801')
    def test_show_transfer_accept_impersonate_another_project(self):
        LOG.info('Create a zone as primary tenant')
        zone_name = dns_data_utils.rand_zone_name(
            name="show_transfer_accept_impersonate", suffix=self.tld_name)
        zone = self.prm_zone_client.create_zone(name=zone_name,
                                                wait_until='ACTIVE')[1]

        # In case when something goes wrong with the test and E2E
        # scenario fails for some reason, we'll use Admin tenant
        # to activate Cleanup for a zone.
        # Note: "ignore_errors=lib_exc.NotFound" is used to prevent a
        # failure in case when E2E scenario was successfully completed.
        # Means that Alt tenant has already been able to run a cleanup
        # for a zone.
        self.addCleanup(
            self.wait_zone_delete, self.admin_zone_client, zone['id'],
            headers=self.all_projects_header,
            ignore_errors=lib_exc.NotFound)

        LOG.info('Create a zone transfer_request as primary tenant')
        transfer_request = self.prm_request_client.create_transfer_request(
                                  zone['id'])[1]
        self.addCleanup(
            self.transfer_request_delete,
            self.prm_request_client,
            transfer_request['id']
        )
        data = {
            "key": transfer_request['key'],
            "zone_transfer_request_id": transfer_request['id']
        }

        LOG.info('Create a zone transfer_accept for Alt tenant, using '
                 'Admin client and "sudo" option')
        transfer_accept = self.admin_accept_client.create_transfer_accept(
            data, headers={
                'x-auth-sudo-project-id': self.os_alt.credentials.project_id,
                'content-type': 'application/json'})[1]

        LOG.info('Fetch the transfer_accept as Alt tenant')
        body = self.alt_accept_client.show_transfer_accept(
            transfer_accept['id'])[1]

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_accept')
        self.assertExpected(transfer_accept, body, self.excluded_keys)

        # E2E accept zone transfer is done, therefore Alt tenant
        # should be able to "cleanup" a transferred zone.
        self.addCleanup(
            self.wait_zone_delete, self.alt_zone_client, zone['id'])

        # Test RBAC with x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'TransferAcceptClient', 'show_transfer_accept', expected_allowed,
            True, transfer_accept['id'],
            headers={'x-auth-sudo-project-id':
                     self.os_alt.credentials.project_id})


class TransferAcceptTestNegative(BaseTransferAcceptTest):

    credentials = ["primary", "alt", "admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TransferAcceptTestNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TransferAcceptTestNegative, cls).setup_clients()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.request_client = cls.os_primary.dns_v2.TransferRequestClient()
        cls.client = cls.os_primary.dns_v2.TransferAcceptClient()

    @decorators.idempotent_id('324a3e80-a1cc-11eb-b534-74e5f9e2a801')
    def test_create_transfer_accept_using_invalid_key(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_transfer_accept_invalid_key", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name,
                                            wait_until='ACTIVE')[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        transfer_request = self.request_client.create_transfer_request(
                                  zone['id'])[1]
        self.addCleanup(
            self.transfer_request_delete,
            self.request_client,
            transfer_request['id']
        )

        data = {"key": data_utils.rand_password(
                len(transfer_request['key'])),
                "zone_transfer_request_id": transfer_request['id']}

        LOG.info('Create a zone transfer_accept using invalid key')
        self.assertRaises(
            lib_exc.Forbidden, self.client.create_transfer_accept,
            transfer_accept_data=data)

    @decorators.idempotent_id('23afb948-a1ce-11eb-b534-74e5f9e2a801')
    def test_create_transfer_accept_using_deleted_transfer_request_id(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_transfer_accept_deleted_id", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name,
                                            wait_until='ACTIVE')[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        transfer_request = self.request_client.create_transfer_request(
                                  zone['id'])[1]
        self.addCleanup(
            self.transfer_request_delete,
            self.request_client,
            transfer_request['id']
        )

        data = {
                 "key": transfer_request['key'],
                 "zone_transfer_request_id": transfer_request['id']
        }

        LOG.info('Delete transfer request')
        self.request_client.delete_transfer_request(transfer_request['id'])

        LOG.info('Ensure 404 when accepting non existing request ID')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.create_transfer_accept(data))
