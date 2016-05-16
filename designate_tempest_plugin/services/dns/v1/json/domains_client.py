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

from designate_tempest_plugin.schemas.v1 import domains_schema as schema
from designate_tempest_plugin.services.dns.v1.json import base

CONF = config.CONF


class DomainsClient(base.DnsClientV1Base):
    @base.handle_errors
    def list_domains(self, params=None):
        """List all domains."""
        resp, body = self._list_request('domains', params=params)

        self.validate_response(schema.list_domains, resp, body)

        return resp, body['domains']

    @base.handle_errors
    def get_domain(self, uuid, params=None):
        """Gets a specific zone.
        :param uuid: Unique identifier of the domain in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized domain as a dictionary.
        :return: A tuple with the server response and the deserialized domain.
        """
        resp, body = self._show_request('domains', uuid, params=params)

        self.validate_response(schema.get_domain, resp, body)

        return resp, body

    @base.handle_errors
    def delete_domain(self, uuid, params=None):
        """Delete the given domain."""
        resp, body = self._delete_request('domains', uuid, params=params)

        self.validate_response(schema.delete_domain, resp, body)

        return resp, body

    @base.handle_errors
    def create_domain(self, name, email, params=None, **kwargs):
        """Creates a domain."""
        post_body = {
            "name": name,
            "email": email
        }

        for option in ['ttl', 'description']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value

        resp, body = self._create_request('domains', post_body, params=params)

        self.validate_response(schema.create_domain, resp, body)

        return resp, body

    @base.handle_errors
    def update_domain(self, uuid, params=None, **kwargs):
        """Updates a domain."""
        post_body = {}

        for option in ['email', 'name', 'ttl', 'description']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value

        resp, body = self._put_request('domains', uuid, post_body,
                                       params=params)

        self.validate_response(schema.update_domain, resp, body)

        return resp, body
