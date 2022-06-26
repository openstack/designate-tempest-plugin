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
from tempest.lib.common.utils import data_utils

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseBlacklistsTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'links']


class BlacklistsAdminTest(BaseBlacklistsTest):

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(BlacklistsAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(BlacklistsAdminTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.BlacklistsClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.BlacklistsClient()
        cls.primary_client = cls.os_primary.dns_v2.BlacklistsClient()

    @decorators.idempotent_id('3a7f7564-6bdd-446e-addc-a3475b4c3f71')
    def test_create_blacklist(self):
        LOG.info('Create a blacklist')
        blacklist = {
            'pattern': dns_data_utils.rand_zone_name(),
            'description': data_utils.rand_name(),
        }
        _, body = self.admin_client.create_blacklist(**blacklist)
        self.addCleanup(self.admin_client.delete_blacklist, body['id'])

        self.assertExpected(blacklist, body, self.excluded_keys)

        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']

        self.check_CUD_RBAC_enforcement('BlacklistsClient', 'create_blacklist',
                                        expected_allowed, False)

    @decorators.idempotent_id('ea608152-da3c-11eb-b8b8-74e5f9e2a801')
    def test_create_blacklist_invalid_pattern(self):
        patterns = ['', '#(*&^%$%$#@$', 'a' * 1000]
        for pattern in patterns:
            LOG.info(
                'Try to create a blacklist using pattern:{}'.format(pattern))
            self.assertRaises(
                lib_exc.BadRequest, self.admin_client.create_blacklist,
                pattern=pattern)

    @decorators.idempotent_id('664bdaa0-da47-11eb-b8b8-74e5f9e2a801')
    def test_create_blacklist_huge_size_description(self):
        LOG.info('Try to create a blacklist using huge size description')
        self.assertRaises(
            lib_exc.BadRequest, self.admin_client.create_blacklist,
            description='a' * 1000)

    @decorators.idempotent_id('fe9de464-d8d1-11eb-bcdc-74e5f9e2a801')
    def test_create_blacklist_as_primary_fails(self):
        LOG.info('As Primary user, try to create a blacklist')
        self.assertRaises(
            lib_exc.Forbidden, self.primary_client.create_blacklist)

    @decorators.idempotent_id('5bc02942-6225-4619-8f49-2105581a8dd6')
    def test_show_blacklist(self):
        LOG.info('Create a blacklist')
        _, blacklist = self.admin_client.create_blacklist()
        self.addCleanup(self.admin_client.delete_blacklist, blacklist['id'])

        LOG.info('Fetch the blacklist')
        _, body = self.admin_client.show_blacklist(blacklist['id'])

        LOG.info('Ensure the fetched response matches the created blacklist')
        self.assertExpected(blacklist, body, self.excluded_keys)

        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader']

        self.check_list_show_RBAC_enforcement(
            'BlacklistsClient', 'show_blacklist', expected_allowed, False,
            blacklist['id'])

    @decorators.idempotent_id('dcea40d9-8d36-43cb-8440-4a842faaef0d')
    def test_delete_blacklist(self):
        LOG.info('Create a blacklist')
        _, blacklist = self.admin_client.create_blacklist()
        self.addCleanup(self.admin_client.delete_blacklist, blacklist['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the blacklist')
        _, body = self.admin_client.delete_blacklist(blacklist['id'])

        # A blacklist delete returns an empty body
        self.assertEqual(body.strip(), b"")

        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']

        self.check_CUD_RBAC_enforcement(
            'BlacklistsClient', 'delete_blacklist', expected_allowed, False,
            blacklist['id'])

    @decorators.idempotent_id('3a2a1e6c-8176-428c-b5dd-d85217c0209d')
    def test_list_blacklists(self):
        LOG.info('Create a blacklist')
        _, blacklist = self.admin_client.create_blacklist()
        self.addCleanup(self.admin_client.delete_blacklist, blacklist['id'])

        LOG.info('List blacklists')
        _, body = self.admin_client.list_blacklists()

        # TODO(pglass): Assert that the created blacklist is in the response
        self.assertGreater(len(body['blacklists']), 0)

        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader']

        self.check_list_IDs_RBAC_enforcement(
            'BlacklistsClient', 'list_blacklists',
            expected_allowed, [blacklist['id']])

    @decorators.idempotent_id('0063d6ad-9557-49c7-b521-e64a14d4d0d0')
    def test_update_blacklist(self):
        LOG.info('Create a blacklist')
        _, blacklist = self.admin_client.create_blacklist()
        self.addCleanup(self.admin_client.delete_blacklist, blacklist['id'])

        LOG.info('Update the blacklist')
        pattern = dns_data_utils.rand_zone_name()
        description = data_utils.rand_name()
        _, body = self.admin_client.update_blacklist(
            uuid=blacklist['id'],
            pattern=pattern,
            description=description,
        )

        LOG.info('Ensure we response with updated values')
        self.assertEqual(pattern, body['pattern'])
        self.assertEqual(description, body['description'])

        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin']

        self.check_CUD_RBAC_enforcement(
            'BlacklistsClient', 'update_blacklist', expected_allowed, False,
            uuid=blacklist['id'], pattern=pattern, description=description)


class TestBlacklistNotFoundAdmin(BaseBlacklistsTest):

    credentials = ["admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestBlacklistNotFoundAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestBlacklistNotFoundAdmin, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.BlacklistsClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.BlacklistsClient()

    @decorators.idempotent_id('9d65b638-fe98-47a8-853f-fa9244d144cc')
    def test_show_blacklist_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.show_blacklist,
                              data_utils.rand_uuid())
        self.assertBlacklist404(e.resp, e.resp_body)

    @decorators.idempotent_id('a9e12415-5040-4fba-905c-95d201fcfd3b')
    def test_update_blacklist_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.update_blacklist,
                              data_utils.rand_uuid())
        self.assertBlacklist404(e.resp, e.resp_body)

    @decorators.idempotent_id('b1132586-bf06-47a6-9f6f-3bab6a2c1932')
    def test_delete_blacklist_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.delete_blacklist,
                              data_utils.rand_uuid())
        self.assertBlacklist404(e.resp, e.resp_body)

    def assertBlacklist404(self, resp, resp_body):
        self.assertEqual(404, resp.status)
        self.assertEqual(404, resp_body['code'])
        self.assertEqual("blacklist_not_found", resp_body['type'])
        self.assertEqual("Could not find Blacklist", resp_body['message'])


class TestBlacklistInvalidIdAdmin(BaseBlacklistsTest):

    credentials = ["admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestBlacklistInvalidIdAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestBlacklistInvalidIdAdmin, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.BlacklistsClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.BlacklistsClient()

    @decorators.idempotent_id('c7bae53f-2edc-45d8-b254-8a81482728c1')
    def test_show_blacklist_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.show_blacklist,
                              'foo')
        self.assertBlacklistInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('c57b97da-ca87-44b5-9f40-a099937433bf')
    def test_update_blacklist_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.update_blacklist,
                              'foo')
        self.assertBlacklistInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('5d62a026-13e4-48b9-9773-1780660c5920')
    def test_delete_blacklist_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.delete_blacklist,
                              'foo')
        self.assertBlacklistInvalidId(e.resp, e.resp_body)

    def assertBlacklistInvalidId(self, resp, resp_body):
        self.assertEqual(400, resp.status)
        self.assertEqual(400, resp_body['code'])
        self.assertEqual("invalid_uuid", resp_body['type'])
        self.assertEqual("Invalid UUID blacklist_id: foo",
                         resp_body['message'])
