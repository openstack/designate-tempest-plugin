# Copyright 2014 Hewlett-Packard Development Company, L.P.
# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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

import six
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest import config
from tempest.lib import decorators

from designate_tempest_plugin.tests import base


CONF = config.CONF


class ServersAdminTest(base.BaseDnsV1Test):
    """
    Tests Servers API Create, Get, List and Delete
    that require admin privileges
    """
    credentials = ['admin']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ServersAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServersAdminTest, cls).setup_clients()

        cls.client = cls.os_admin.servers_client

    @classmethod
    def skip_checks(cls):
        super(ServersAdminTest, cls).skip_checks()

        if not CONF.dns_feature_enabled.api_v1_servers:
            skip_msg = ("%s skipped as designate V1 servers API is not "
                        "available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def resource_setup(cls):
        super(ServersAdminTest, cls).resource_setup()

        cls.setup_servers = list()
        for i in range(2):
            name = data_utils.rand_name('dns-server') + '.com.'
            _, server = cls.client.create_server(name)
            cls.setup_servers.append(server)

    @classmethod
    def resource_cleanup(cls):
        for server in cls.setup_servers:
            cls.client.delete_server(server['id'])
        super(ServersAdminTest, cls).resource_cleanup()

    def _delete_server(self, server_id):
        self.client.delete_server(server_id)
        self.assertRaises(lib_exc.NotFound,
                          self.client.get_server, server_id)

    @decorators.idempotent_id('0296fb0c-f400-4b52-9be4-a24f37646e3f')
    def test_list_servers(self):
        # Get a list of servers
        _, servers = self.client.list_servers()
        # Verify servers created in setup class are in the list
        for server in self.setup_servers:
            self.assertIn(server['id'],
                          six.moves.map(lambda x: x['id'], servers))

    @decorators.idempotent_id('7d18fdfc-3959-4c3f-9855-0bf2f8c9ade2')
    def test_create_update_get_delete_server(self):
        # Create Dns Server
        s_name1 = data_utils.rand_name('dns-server') + '.com.'
        _, server = self.client.create_server(s_name1)
        self.addCleanup(self._delete_server, server['id'])
        self.assertEqual(s_name1, server['name'])
        self.assertIsNotNone(server['id'])
        # Update Dns Server
        s_name2 = data_utils.rand_name('update-dns-server') + '.com.'
        _, update_server = self.client.update_server(server['id'],
                                                     name=s_name2)
        self.assertEqual(s_name2, update_server['name'])
        # Get the details of Server
        _, get_server = self.client.get_server(server['id'])
        self.assertEqual(update_server['name'], get_server['name'])
