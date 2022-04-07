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

from designate_tempest_plugin.services.dns.v2.json import base


class TransferAcceptClient(base.DnsClientV2Base):

    @base.handle_errors
    def create_transfer_accept(self, transfer_accept_data,
                               params=None, headers=None, extra_headers=None):
        """Create a zone transfer_accept.
        :param transfer_accept_data: A python dictionary representing
                                data for the zone transfer accept.
        :param params: A Python dict that represents the query paramaters to
                       include in the accept URI.
        :param headers (dict): The headers to use for the request.
        :param extra_headers (bool): Boolean value than indicates if the
                                     headers returned by the get_headers()
                                     method are to be used but additional
                                     headers are needed in the request
                                     pass them in as a dict.
        :return: Serialized accepted zone transfer as a dictionary.
        """

        transfer_accept_uri = 'zones/tasks/transfer_accepts'
        resp, body = self._create_request(
            transfer_accept_uri, transfer_accept_data,
            params=params, headers=headers, extra_headers=extra_headers)

        # Create Transfer accept should Return a HTTP 201
        self.expected_success(201, resp.status)

        return resp, body

    @base.handle_errors
    def show_transfer_accept(self, uuid, params=None, headers=None):
        """Gets a specific accepted zone transfer..
        :param uuid: Unique identifier of the transfer_accept.
        :param params: A Python dict that represents the query paramaters to
                       include in the accept URI.
        :param headers (dict): The headers to use for the request.
        :return: Serialized accepted zone transfer as a dictionary.
        """
        return self._show_request(
            'zones/tasks/transfer_accepts', uuid,
            params=params, headers=headers)

    @base.handle_errors
    def list_transfer_accept(self, params=None, headers=None):
        """Lists all accepted zone transfers.
        :param params: A Python dict that represents the query paramaters to
                       include in the accept URI.
        :param headers (dict): The headers to use for the request.
        :return: List of accepted zone transfers
        """
        return self._list_request(
            'zones/tasks/transfer_accepts', params=params, headers=headers)
