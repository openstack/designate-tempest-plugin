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


class BaseTransferRequestTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'key', 'links']

    @classmethod
    def setup_clients(cls):
        super(BaseTransferRequestTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(BaseTransferRequestTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(
            name="BaseTransferRequestTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(BaseTransferRequestTest, cls).resource_cleanup()


class TransferRequestTest(BaseTransferRequestTest):
    credentials = ["primary", "alt", "admin", "system_admin", "system_reader",
                   "project_member", "project_reader"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TransferRequestTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TransferRequestTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_client = (cls.os_system_admin.dns_v2.
                                TransferRequestClient())
        else:
            cls.admin_client = cls.os_admin.dns_v2.TransferRequestClient()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.alt_zone_client = cls.os_alt.dns_v2.ZonesClient()
        cls.client = cls.os_primary.dns_v2.TransferRequestClient()
        cls.alt_client = cls.os_alt.dns_v2.TransferRequestClient()

    @decorators.idempotent_id('2381d489-ad84-403d-b0a2-8b77e4e966bf')
    def test_create_transfer_request(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_transfer_request", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        # Test RBAC
        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')
            expected_allowed.append('os_project_member')

        self.check_CUD_RBAC_enforcement(
            'TransferRequestClient', 'create_transfer_request',
            expected_allowed, True, zone['id'])

        LOG.info('Create a zone transfer_request')
        transfer_request = self.client.create_transfer_request(zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('ACTIVE', transfer_request['status'])

    @decorators.idempotent_id('5deae1ac-7c14-42dc-b14e-4e4b2725beb7')
    def test_create_transfer_request_scoped(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_transfer_request_scoped", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        transfer_request_data = dns_data_utils.rand_transfer_request_data(
            target_project_id=self.os_alt.credentials.project_id)

        LOG.info('Create a scoped zone transfer_request')
        transfer_request = self.client.create_transfer_request(
            zone['id'], transfer_request_data)[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('ACTIVE', transfer_request['status'])

    @decorators.idempotent_id('4505152f-0a9c-4f02-b385-2216c914a0be')
    def test_create_transfer_request_empty_body(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_transfer_request_empty", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        LOG.info('Create a zone transfer_request')
        transfer_request = self.client.create_transfer_request_empty_body(
            zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Ensure we respond with ACTIVE status')
        self.assertEqual('ACTIVE', transfer_request['status'])

    @decorators.idempotent_id('64a7be9f-8371-4ce1-a242-c1190de7c985')
    def test_show_transfer_request(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="show_transfer_request", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        transfer_request = self.client.create_transfer_request(zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Fetch the transfer_request')
        body = self.client.show_transfer_request(transfer_request['id'])[1]

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_request')
        self.assertExpected(transfer_request, body, self.excluded_keys)

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC
        # Note: The create service client does not define a target project
        #       ID, so everyone should be able to see it.
        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.extend(['os_system_admin', 'os_system_reader',
                                     'os_project_member', 'os_project_reader'])

        self.check_list_show_RBAC_enforcement(
            'TransferRequestClient', 'show_transfer_request', expected_allowed,
            True, transfer_request['id'])

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_show_RBAC_enforcement(
            'TransferRequestClient', 'show_transfer_request', expected_allowed,
            True, transfer_request['id'], headers=self.all_projects_header)
        # TODO(johnsom) Move this down to the impersonate test below when the
        #               bug is resolved and the test is not skipped.
        self.check_list_show_RBAC_enforcement(
            'TransferRequestClient', 'show_transfer_request', expected_allowed,
            True, transfer_request['id'],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('5bed4582-9cfb-11eb-a160-74e5f9e2a801')
    @decorators.skip_because(bug="1926572")
    def test_show_transfer_request_impersonate_another_project(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="show_transfer_request_impersonate", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        transfer_request = self.client.create_transfer_request(zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('As Admin tenant fetch the transfer_request without using '
                 '"x-auth-sudo-project-id" HTTP header. Expected: 404')
        self.assertRaises(lib_exc.NotFound,
                          lambda: self.admin_client.show_transfer_request(
                              transfer_request['id']))

        LOG.info('As Admin tenant fetch the transfer_request using '
                 '"x-auth-sudo-project-id" HTTP header.')
        body = self.admin_client.show_transfer_request(
            transfer_request['id'],
            headers={'x-auth-sudo-project-id': zone['project_id']})[1]

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_request')
        self.assertExpected(transfer_request, body, self.excluded_keys)

    @decorators.idempotent_id('235ded87-0c47-430b-8cad-4f3194b927a6')
    def test_show_transfer_request_as_target(self):
        # Checks the target of a scoped transfer request can see
        # the request.
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_transfer_request_as_target", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        transfer_request_data = dns_data_utils.rand_transfer_request_data(
            target_project_id=self.os_alt.credentials.project_id)

        LOG.info('Create a scoped zone transfer_request')
        transfer_request = self.client.create_transfer_request(
            zone['id'], transfer_request_data)[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Fetch the transfer_request as the target')
        body = self.alt_client.show_transfer_request(transfer_request['id'])[1]

        LOG.info('Ensure the fetched response matches the '
                 'created transfer_request')
        excluded_keys = self.excluded_keys + ["target_project_id",
                                              "project_id"]
        self.assertExpected(transfer_request, body, excluded_keys)

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC when a transfer target project is specified.
        expected_allowed = ['os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')
        else:
            expected_allowed.append('os_admin')

        self.check_list_show_RBAC_enforcement(
            'TransferRequestClient', 'show_transfer_request', expected_allowed,
            True, transfer_request['id'])

    @decorators.idempotent_id('7d81c487-aa15-44c4-b3e5-424ab9e6a3e5')
    def test_delete_transfer_request(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="delete_transfer_request", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a transfer_request')
        transfer_request = self.client.create_transfer_request(zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'],
                        ignore_errors=lib_exc.NotFound)

        # Test RBAC
        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')
            expected_allowed.append('os_project_member')

        self.check_CUD_RBAC_enforcement(
            'TransferRequestClient', 'delete_transfer_request',
            expected_allowed, True, transfer_request['id'])

        LOG.info('Delete the transfer_request')
        self.client.delete_transfer_request(transfer_request['id'])
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.show_transfer_request(transfer_request['id']))

    @decorators.idempotent_id('ddd42a19-1768-428c-846e-32f9d6493011')
    def test_list_transfer_requests(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_transfer_request", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        transfer_request = self.client.create_transfer_request(zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('List transfer_requests')
        body = self.client.list_transfer_requests()[1]

        self.assertGreater(len(body['transfer_requests']), 0)

        # TODO(johnsom) Test reader role once this bug is fixed:
        #               https://bugs.launchpad.net/tempest/+bug/1964509
        # Test RBAC - Users that are allowed to call list, but should get
        #             zero zones.
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader',
                                'os_admin', 'os_project_member',
                                'os_project_reader']
        else:
            expected_allowed = ['os_alt']

        self.check_list_RBAC_enforcement_count(
            'TransferRequestClient', 'list_transfer_requests',
            expected_allowed, 0)

        # Test that users who should see the zone, can see it.
        expected_allowed = ['os_primary']

        self.check_list_IDs_RBAC_enforcement(
            'TransferRequestClient', 'list_transfer_requests',
            expected_allowed, [transfer_request['id']])

    @decorators.idempotent_id('db985892-9d02-11eb-a160-74e5f9e2a801')
    def test_list_transfer_requests_all_projects(self):
        LOG.info('Create a Primary zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_transfer_request_all_projects", suffix=self.tld_name)
        primary_zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete,
                        self.zone_client, primary_zone['id'])

        LOG.info('Create an Alt zone')
        alt_zone_name = dns_data_utils.rand_zone_name(
            name="list_transfer_request_all_projects_alt",
            suffix=self.tld_name)
        alt_zone = self.alt_zone_client.create_zone(name=alt_zone_name)[1]
        self.addCleanup(self.wait_zone_delete,
                        self.alt_zone_client, alt_zone['id'])

        LOG.info('Create a zone transfer_request using Primary client')
        primary_transfer_request = self.client.create_transfer_request(
            primary_zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        primary_transfer_request['id'])

        LOG.info('Create a zone transfer_request using Alt client')
        alt_transfer_request = self.alt_client.create_transfer_request(
            alt_zone['id'])[1]
        self.addCleanup(self.alt_client.delete_transfer_request,
                        alt_transfer_request['id'])

        LOG.info('List transfer_requests for all projects using Admin tenant '
                 'without "x-auth-all-projects" HTTP header. '
                 'Expected: empty list')
        self.assertEqual([], self.admin_client.list_transfer_requests()[1][
            'transfer_requests'], 'Failed, requests list is not empty')

        LOG.info('List transfer_requests for all projects using Admin tenant '
                 'and "x-auth-all-projects" HTTP header.')
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        request_ids = [
            item['id'] for item in self.admin_client.list_transfer_requests(
                headers=self.all_projects_header,
                params={'limit': 1000})[1]['transfer_requests']]

        for request_id in [primary_transfer_request['id'],
                           alt_transfer_request['id']]:
            self.assertIn(request_id, request_ids,
                          "Failed, transfer request ID:{} wasn't found in "
                          "listed IDs{}".format(request_id, request_ids))

        # Test RBAC with x-auth-all-projects
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'TransferRequestClient', 'list_transfer_requests',
            expected_allowed, [primary_transfer_request['id']],
            headers=self.all_projects_header)

    @decorators.idempotent_id('bee42f38-e666-4b85-a710-01f40ea1e56a')
    def test_list_transfer_requests_impersonate_another_project(self):
        LOG.info('Create a Primary zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_transfer_request_impersonate", suffix=self.tld_name)
        primary_zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete,
                        self.zone_client, primary_zone['id'])

        LOG.info('Create an Alt zone')
        alt_zone_name = dns_data_utils.rand_zone_name(
            name="list_transfer_request_impersonate_alt", suffix=self.tld_name)
        alt_zone = self.alt_zone_client.create_zone(name=alt_zone_name)[1]
        self.addCleanup(self.wait_zone_delete,
                        self.alt_zone_client, alt_zone['id'])

        LOG.info('Create a zone transfer_request using Primary client')
        primary_transfer_request = self.client.create_transfer_request(
            primary_zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        primary_transfer_request['id'])

        LOG.info('Create a zone transfer_request using Alt client')
        alt_transfer_request = self.alt_client.create_transfer_request(
            alt_zone['id'])[1]
        self.addCleanup(self.alt_client.delete_transfer_request,
                        alt_transfer_request['id'])

        request_ids = [
            item['id'] for item in self.admin_client.list_transfer_requests(
                headers={'x-auth-sudo-project-id': self.alt_client.project_id},
                params={'limit': 1000})[1]['transfer_requests']]

        self.assertEqual([alt_transfer_request['id']], request_ids)

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']
        else:
            expected_allowed = ['os_admin']

        self.check_list_IDs_RBAC_enforcement(
            'TransferRequestClient', 'list_transfer_requests',
            expected_allowed, [primary_transfer_request['id']],
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('de5e9d32-c723-4518-84e5-58da9722cc13')
    def test_update_transfer_request(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="update_transfer_request", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone transfer_request')
        transfer_request = self.client.create_transfer_request(zone['id'])[1]
        self.addCleanup(self.client.delete_transfer_request,
                        transfer_request['id'])

        LOG.info('Update the transfer_request')
        data = {
                 "description": "demo description"
               }
        transfer_request_patch = self.client.update_transfer_request(
            transfer_request['id'], transfer_request_data=data)[1]

        self.assertEqual(data['description'],
                         transfer_request_patch['description'])

        # Test RBAC
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'TransferRequestClient', 'update_transfer_request',
            expected_allowed, True,
            transfer_request['id'], transfer_request_data=data)

        # Test RBAC with x-auth-all-projects and x-auth-sudo-project-id header
        expected_allowed = ['os_admin', 'os_primary']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'TransferRequestClient', 'update_transfer_request',
            expected_allowed, False,
            transfer_request['id'], transfer_request_data=data,
            headers=self.all_projects_header)
        self.check_CUD_RBAC_enforcement(
            'TransferRequestClient', 'update_transfer_request',
            expected_allowed, False,
            transfer_request['id'], transfer_request_data=data,
            headers={'x-auth-sudo-project-id': self.client.project_id})

    @decorators.idempotent_id('73b754a9-e856-4fd6-80ba-e8d1b80f5dfa')
    def test_list_transfer_requests_dot_json_fails(self):
        uri = self.client.get_uri('transfer_requests.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.get(uri))


class TestTransferRequestNotFound(BaseTransferRequestTest):
    credentials = ["admin", "primary", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTransferRequestNotFound, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTransferRequestNotFound, cls).setup_clients()
        cls.client = cls.os_primary.dns_v2.TransferRequestClient()

    @decorators.idempotent_id('39131f7c-e9bb-4f92-a325-444a675e1b3d')
    def test_create_transfer_request_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.client.create_transfer_request,
                              data_utils.rand_uuid())
        self.assertEqual(404, e.resp.status)
        self.assertEqual(404, e.resp_body['code'])
        self.assertEqual("zone_not_found", e.resp_body['type'])

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


class TestTransferRequestInvalidId(BaseTransferRequestTest):
    credentials = ["admin", "primary", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTransferRequestInvalidId, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTransferRequestInvalidId, cls).setup_clients()
        cls.client = cls.os_primary.dns_v2.TransferRequestClient()

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
