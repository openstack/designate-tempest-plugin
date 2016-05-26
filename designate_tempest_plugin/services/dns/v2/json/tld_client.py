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

from tempest.lib.common.utils import data_utils

from designate_tempest_plugin.services.dns.v2.json import base


class TldClient(base.DnsClientV2Base):
    """API V2 Tempest REST client for Designate Tld API"""

    @base.handle_errors
    def create_tld(self, tld_name=None, description=None, params=None):
        """Create a tld with the specified parameters.
        :param tld_name: Name of the tld. e.g .com .
        :param description: represents details of tld.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the created tld.
        """
        tld = {
                "name": tld_name or data_utils.rand_name(name="tld"),
                "description": description or data_utils.rand_name(
                               name="description")
        }

        resp, body = self._create_request('tlds', data=tld, params=params)

        # Create Tld should Return a HTTP 201
        self.expected_success(201, resp.status)

        return resp, body

    @base.handle_errors
    def show_tld(self, uuid, params=None):
        """Gets a specific tld.
        :param uuid: Unique identifier of the tld in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized tld as a dictionary.
        """
        return self._show_request('tlds', uuid, params=params)

    @base.handle_errors
    def list_tlds(self, params=None):
        """Gets a list of tlds.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized tlds as a list.
        """
        return self._list_request('tlds', params=params)

    @base.handle_errors
    def delete_tld(self, uuid, params=None):
        """Deletes a tld having the specified UUID.
        :param uuid: The unique identifier of the tld.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request('tlds', uuid, params=params)

        # Delete Tld should Return a HTTP 204
        self.expected_success(204, resp.status)

        return resp, body

    @base.handle_errors
    def update_tld(self, uuid, tld_name=None, description=None, params=None):
        """Update a tld with the specified parameters.
        :param uuid: The unique identifier of the tld.
        :param tld_name: Name of the tld. e.g .com .
        :param description: represents info about tld.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the updated tld.
        """

        tld = {
                 "name": tld_name or data_utils.rand_name(name="tld"),
                 "description": description or data_utils.rand_name(
                                name="description")
        }

        resp, body = self._update_request('tlds', uuid, tld,
                                          params=params)

        # Update Tld should Return a HTTP 200
        self.expected_success(200, resp.status)

        return resp, body
