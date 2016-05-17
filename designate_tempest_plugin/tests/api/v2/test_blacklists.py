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
from tempest import test
from tempest.lib import exceptions as lib_exc
from tempest.lib.common.utils import data_utils

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class BaseBlacklistsTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'links']


class BlacklistsAdminTest(BaseBlacklistsTest):

    credentials = ["admin"]

    @classmethod
    def setup_clients(cls):
        super(BlacklistsAdminTest, cls).setup_clients()
        cls.admin_client = cls.os_adm.blacklists_client

    @test.attr(type='smoke')
    @test.idempotent_id('3a7f7564-6bdd-446e-addc-a3475b4c3f71')
    def test_create_blacklist(self):
        LOG.info('Create a blacklist')
        blacklist = {
            'pattern': dns_data_utils.rand_zone_name(),
            'description': data_utils.rand_name(),
        }
        _, body = self.admin_client.create_blacklist(**blacklist)
        self.addCleanup(self.admin_client.delete_blacklist, body['id'])

        self.assertExpected(blacklist, body, self.excluded_keys)

    @test.attr(type='smoke')
    @test.idempotent_id('5bc02942-6225-4619-8f49-2105581a8dd6')
    def test_show_blacklist(self):
        LOG.info('Create a blacklist')
        _, blacklist = self.admin_client.create_blacklist()
        self.addCleanup(self.admin_client.delete_blacklist, blacklist['id'])

        LOG.info('Fetch the blacklist')
        _, body = self.admin_client.show_blacklist(blacklist['id'])

        LOG.info('Ensure the fetched response matches the created blacklist')
        self.assertExpected(blacklist, body, self.excluded_keys)

    @test.attr(type='smoke')
    @test.idempotent_id('dcea40d9-8d36-43cb-8440-4a842faaef0d')
    def test_delete_blacklist(self):
        LOG.info('Create a blacklist')
        _, blacklist = self.admin_client.create_blacklist()
        self.addCleanup(self.admin_client.delete_blacklist, blacklist['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Delete the blacklist')
        _, body = self.admin_client.delete_blacklist(blacklist['id'])

        # A blacklist delete returns an empty body
        self.assertEqual(body.strip(), "")

    @test.attr(type='smoke')
    @test.idempotent_id('3a2a1e6c-8176-428c-b5dd-d85217c0209d')
    def test_list_blacklists(self):
        LOG.info('Create a blacklist')
        _, blacklist = self.admin_client.create_blacklist()
        self.addCleanup(self.admin_client.delete_blacklist, blacklist['id'])

        LOG.info('List blacklists')
        _, body = self.admin_client.list_blacklists()

        # TODO(pglass): Assert that the created blacklist is in the response
        self.assertGreater(len(body['blacklists']), 0)

    @test.attr(type='smoke')
    @test.idempotent_id('0063d6ad-9557-49c7-b521-e64a14d4d0d0')
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