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

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.services.dns.v2.json import base


class TransferRequestClient(base.DnsClientV2Base):

    @base.handle_errors
    def create_transfer_request(self, uuid, transfer_request_data=None,
                                params=None):
        """Create a zone transfer_requests.
        :param uuid: Unique identifier of the zone in UUID format.
        :transfer_request_data: A python dictionary representing
                                data for zone transfer request
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized imported zone as a dictionary.
        """

        transfer_request_uri = 'zones/{0}/tasks/transfer_requests'.format(uuid)
        transfer_request_data = (transfer_request_data or
                                 dns_data_utils.rand_transfer_request_data())
        resp, body = self._create_request(
            transfer_request_uri, transfer_request_data, params=params)

        # Create Transfer request should Return a HTTP 201
        self.expected_success(201, resp.status)

        return resp, body

    @base.handle_errors
    def create_transfer_request_empty_body(self, uuid, params=None):
        """Create a zone transfer_requests.
        :param uuid: Unique identifier of the zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized zone trasfer request as a dictionary.
        """

        transfer_request_uri = 'zones/{0}/tasks/transfer_requests'.format(uuid)
        resp, body = self._create_request(
            transfer_request_uri, None, params=params)

        # Create Transfer request should Return a HTTP 201
        self.expected_success(201, resp.status)

        return resp, body

    @base.handle_errors
    def show_transfer_request(self, uuid, params=None):
        """Gets a specific transfer_requestsed zone.
        :param uuid: Unique identifier of the transfer_requestsed zone in
                     UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized transfer_requestsed zone as a dictionary.
        """
        return self._show_request(
            'zones/tasks/transfer_requests', uuid, params=params)

    @base.handle_errors
    def list_transfer_requests(self, params=None):
        """Gets all the transfer_requestsed zones
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized transfer_requestsed zone as a list.
        """
        return self._list_request(
            'zones/tasks/transfer_requests', params=params)

    @base.handle_errors
    def delete_transfer_request(self, uuid, params=None):
        """Deletes an transfer_requestsed zone having the specified UUID.
        :param uuid: The unique identifier of the transfer_requestsed zone.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request(
            'zones/tasks/transfer_requests', uuid, params=params)

        # Delete Zone transfer_requests should Return a HTTP 204
        self.expected_success(204, resp.status)

        return resp, body

    @base.handle_errors
    def update_transfer_request(self, uuid, transfer_request_data=None,
                                params=None):
        """Update a zone transfer_requests.
        :param uuid: Unique identifier of the zone transfer request in UUID
                     format.
        :transfer_request_data: A python dictionary representing
                                data for zone transfer request
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized imported zone as a dictionary.
        """
        transfer_request_uri = 'zones/tasks/transfer_requests'
        transfer_request_data = (transfer_request_data or
                                 dns_data_utils.rand_transfer_request_data())
        resp, body = self._update_request(
            transfer_request_uri, uuid, transfer_request_data, params=params)

        # Create Transfer request should Return a HTTP 200
        self.expected_success(200, resp.status)

        return resp, body
