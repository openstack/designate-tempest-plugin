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
import ddt

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import clients

LOG = logging.getLogger(__name__)


@ddt.ddt
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

    @decorators.idempotent_id('0f7a6d20-f6f3-4937-8fe6-7a9851227d98')
    @ddt.file_data('unauthed_data.json')
    def test_unauthed(self, client, method, args=None):
        client = getattr(self, client)
        method = getattr(client, method)
        args = args or []
        self.assertRaises(lib_exc.Unauthorized, method, *args)
