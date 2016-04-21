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
from tempest.lib.common.utils import data_utils

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.services.dns.v2.json import base


class BlacklistsClient(base.DnsClientV2Base):

    @base.handle_errors
    def create_blacklist(self, pattern=None, description=None, params=None):
        """Create a blacklist

        :param pattern: The blacklist pattern.
            Default: Random Value
        :param description: A description of the blacklist.
            Default: Random Value
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the created blacklist.
        """
        blacklist = {
            'pattern': pattern or dns_data_utils.rand_zone_name(),
            'description': description or data_utils.rand_name(),
        }

        resp, body = self._create_request('blacklists', blacklist,
                                          params=params)

        self.expected_success(201, resp.status)

        return resp, body

    @base.handle_errors
    def show_blacklist(self, uuid, params=None):
        """Gets a specified blacklist.

        :param uuid: Unique identifier of the blacklist in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized blacklist as a dictionary.
        """
        return self._show_request('blacklists', uuid, params=params)

    @base.handle_errors
    def list_blacklists(self, params=None):
        """Gets a list of blacklists.

        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized blacklists as a list.
        """
        return self._list_request('blacklists', params=params)

    @base.handle_errors
    def delete_blacklist(self, uuid, params=None):
        """Deletes a blacklist having the specified UUID.

        :param uuid: The unique identifier of the blacklist.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request('blacklists', uuid, params=params)

        self.expected_success(204, resp.status)

        return resp, body

    @base.handle_errors
    def update_blacklist(self, uuid, pattern=None, description=None,
                         params=None):
        """Update a blacklist with the specified parameters.

        :param uuid: The unique identifier of the blacklist.
        :param pattern: The blacklist pattern.
            Default: Random Value
        :param description: A description of the blacklist.
            Default: Random Value
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the updated blacklist.
        """
        blacklist = {
            'pattern': pattern or dns_data_utils.rand_zone_name(),
            'description': description or data_utils.rand_name(),
        }

        resp, body = self._update_request('blacklists', uuid, blacklist,
                                          params=params)

        self.expected_success(200, resp.status)

        return resp, body
