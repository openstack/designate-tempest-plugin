# Copyright 2014 Hewlett-Packard Development Company, L.P
# All Rights Reserved.
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

from tempest import config

from designate_tempest_plugin.schemas.v1 import servers_schema as schema
from designate_tempest_plugin.services.dns.v1.json import base

CONF = config.CONF


class ServersClient(base.DnsClientV1Base):
    @base.handle_errors
    def list_servers(self, params=None):
        """List all servers."""
        resp, body = self._list_request('servers', params=params)

        self.validate_response(schema.list_servers, resp, body)

        return resp, body['servers']

    @base.handle_errors
    def get_server(self, uuid, params=None):
        """Get the details of a server."""
        resp, body = self._show_request('servers', uuid, params=params)

        self.validate_response(schema.get_server, resp, body)

        return resp, body

    @base.handle_errors
    def delete_server(self, uuid, params=None):
        """Delete the given server."""
        resp, body = self._delete_request('servers', uuid, params=params)

        self.validate_response(schema.delete_server, resp, body)

        return resp, body

    @base.handle_errors
    def create_server(self, name, params=None, **kwargs):
        """Creates a server."""
        post_body = {
            "name": name,
        }

        for option in ['name']:
            value = kwargs.get(option)
            post_param = option
            if value is not None:
                post_body[post_param] = value

        resp, body = self._create_request('servers', post_body, params=params)

        self.validate_response(schema.create_server, resp, body)

        return resp, body

    @base.handle_errors
    def update_server(self, uuid, params=None, **kwargs):
        """Updates a server."""
        post_body = {}

        for option in ['name']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value

        resp, body = self._put_request('servers', uuid, post_body,
                                       params=params)

        self.validate_response(schema.update_server, resp, body)

        return resp, body
