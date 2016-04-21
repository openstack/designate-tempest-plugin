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

from designate_tempest_plugin.schemas.v1 import records_schema as schema
from designate_tempest_plugin.services.dns.v1.json import base

CONF = config.CONF


class RecordsClient(base.DnsClientV1Base):
    @base.handle_errors
    def list_records(self, domain_uuid, params=None):
        """List all records."""
        base_uri = 'domains/%s/records' % (domain_uuid)

        resp, body = self._list_request(base_uri, params=params)

        self.validate_response(schema.list_records, resp, body)

        return resp, body['records']

    @base.handle_errors
    def get_record(self, domain_uuid, uuid, params=None):
        """Get the details of a record."""
        base_uri = 'domains/%s/records' % (domain_uuid)

        resp, body = self._show_request(base_uri, uuid, params=params)

        self.validate_response(schema.get_record, resp, body)

        return resp, body

    @base.handle_errors
    def delete_record(self, domain_uuid, uuid, params=None):
        """Delete the given record."""
        base_uri = 'domains/%s/records' % (domain_uuid)

        resp, body = self._delete_request(base_uri, uuid, params=params)

        self.validate_response(schema.delete_record, resp, body)

        return resp, body

    @base.handle_errors
    def create_record(self, domain_uuid, name, type, data, params=None,
                      **kwargs):
        """Creates a record."""
        base_uri = 'domains/%s/records' % (domain_uuid)

        post_body = {
            "name": name,
            "type": type,
            "data": data
        }

        for option in ['ttl', 'priority', 'description']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value

        resp, body = self._create_request(base_uri, post_body, params=params)

        self.validate_response(schema.create_record, resp, body)

        return resp, body

    @base.handle_errors
    def update_record(self, domain_uuid, uuid, params=None, **kwargs):
        """Updates a record."""
        base_uri = 'domains/%s/records' % (domain_uuid)

        post_body = {}

        for option in ['name', 'type', 'data', 'ttl', 'priority',
                       'description']:
            post_param = option
            value = kwargs.get(option)
            if value is not None:
                post_body[post_param] = value

        resp, body = self._put_request(base_uri, uuid, post_body,
                                       params=params)

        self.validate_response(schema.update_record, resp, body)

        return resp, body
