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
from designate_tempest_plugin import clients

LOG = logging.getLogger(__name__)


class TestDnsUnauthed(base.BaseDnsV2Test):

    client_manager = clients.ManagerV2Unauthed
    credentials = ["primary"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestDnsUnauthed, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestDnsUnauthed, cls).setup_clients()
        cls.zones_client = cls.os_primary.zones_client
        cls.recordset_client = cls.os_primary.recordset_client
        cls.tld_client = cls.os_primary.tld_client
        cls.pool_client = cls.os_primary.pool_client
        cls.blacklists_client = cls.os_primary.blacklists_client

    def _test_unauthed(self, client, method, args=None):
        client = getattr(self, client)
        method = getattr(client, method)
        args = args or []
        self.assertRaises(lib_exc.Unauthorized, method, *args)

    @decorators.idempotent_id('b18827ac-de92-11ed-8334-201e8823901f')
    def test_list_zones(self):
        self._test_unauthed('zones_client', 'list_zones')

    @decorators.idempotent_id('f60c32ce-de92-11ed-8334-201e8823901f')
    def test_show_zone(self):
        self._test_unauthed(
            'zones_client', 'show_zone',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('56e899c0-de93-11ed-8334-201e8823901f')
    def test_create_zone(self):
        self._test_unauthed(
            'zones_client', 'create_zone',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('5765af6e-de93-11ed-8334-201e8823901f')
    def test_update_zone(self):
        self._test_unauthed(
            'zones_client', 'update_zone',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('57b5cef4-de93-11ed-8334-201e8823901f')
    def test_delete_zone(self):
        self._test_unauthed(
            'zones_client', 'delete_zone',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('05099b62-de94-11ed-8334-201e8823901f')
    def test_list_recordsets(self):
        self._test_unauthed(
            'recordset_client', 'list_recordset',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('0573ca32-de94-11ed-8334-201e8823901f')
    def test_show_recordset(self):
        self._test_unauthed(
            'recordset_client', 'show_recordset',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90",
             "6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('05c0236e-de94-11ed-8334-201e8823901f')
    def test_create_recordset(self):
        self._test_unauthed(
            'recordset_client', 'create_recordset',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90",
             "6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('0600f628-de94-11ed-8334-201e8823901f')
    def test_update_recordset(self):
        self._test_unauthed(
            'recordset_client', 'update_recordset',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90",
             "6ef3b7f2-df39-43ef-9f37-ce2bc424ab90", {}])

    @decorators.idempotent_id('063c95b6-de94-11ed-8334-201e8823901f')
    def test_delete_recordset(self):
        self._test_unauthed(
            'recordset_client', 'delete_recordset',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90",
             "6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('ee9dae6c-de94-11ed-8334-201e8823901f')
    def test_list_tlds(self):
        self._test_unauthed('tld_client', 'list_tlds')

    @decorators.idempotent_id('eef1e5f4-de94-11ed-8334-201e8823901f')
    def test_show_tld(self):
        self._test_unauthed(
            'tld_client', 'show_tld',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('ef3ae024-de94-11ed-8334-201e8823901f')
    def test_create_tld(self):
        self._test_unauthed(
            'tld_client', 'create_tld',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('ef7cfda6-de94-11ed-8334-201e8823901f')
    def test_update_tld(self):
        self._test_unauthed(
            'tld_client', 'update_tld',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('efb982e4-de94-11ed-8334-201e8823901f')
    def test_delete_tld(self):
        self._test_unauthed(
            'tld_client', 'delete_tld',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('654e7596-de95-11ed-8334-201e8823901f')
    def test_list_blacklists(self):
        self._test_unauthed('blacklists_client', 'list_blacklists')

    @decorators.idempotent_id('658ea9cc-de95-11ed-8334-201e8823901f')
    def test_show_blacklist(self):
        self._test_unauthed(
            'blacklists_client', 'show_blacklist',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('65cbc2ee-de95-11ed-8334-201e8823901f')
    def test_create_blacklist(self):
        self._test_unauthed(
            'blacklists_client', 'create_blacklist',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('66032676-de95-11ed-8334-201e8823901f')
    def test_update_blacklist(self):
        self._test_unauthed(
            'blacklists_client', 'update_blacklist',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('66321184-de95-11ed-8334-201e8823901f')
    def test_delete_blacklist(self):
        self._test_unauthed(
            'blacklists_client', 'delete_blacklist',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('c7048d66-de95-11ed-8334-201e8823901f')
    def test_list_pools(self):
        self._test_unauthed('pool_client', 'list_pools')

    @decorators.idempotent_id('c74581cc-de95-11ed-8334-201e8823901f')
    def test_show_pool(self):
        self._test_unauthed(
            'pool_client', 'show_pool',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('c77d62f4-de95-11ed-8334-201e8823901f')
    def test_create_pool(self):
        self._test_unauthed(
            'pool_client', 'create_pool',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('c7ada040-de95-11ed-8334-201e8823901f')
    def test_update_pool(self):
        self._test_unauthed(
            'pool_client', 'update_pool',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])

    @decorators.idempotent_id('c7e07682-de95-11ed-8334-201e8823901f')
    def test_delete_pool(self):
        self._test_unauthed(
            'pool_client', 'delete_pool',
            ["6ef3b7f2-df39-43ef-9f37-ce2bc424ab90"])
