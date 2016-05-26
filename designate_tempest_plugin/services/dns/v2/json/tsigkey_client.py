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

from designate_tempest_plugin import data_utils as utils
from designate_tempest_plugin.services.dns.v2.json import base


class TsigkeyClient(base.DnsClientV2Base):
    """API V2 Tempest REST client for Designate Tsigkey API"""

    @base.handle_errors
    def create_tsigkey(self, resource_id, name=None, algorithm=None,
                       secret=None, scope=None, params=None):
        """Create a tsigkey with the specified parameters.
        :param resource_id: Pool id or Zone id.
        :param name: name of the tsigkey.
        :param algorithm: TSIG algorithm e.g hmac-md5, hmac-sha256 etc.
        :param secret: represents TSIG secret.
        :param scope: represents TSIG scope.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the created tsigkey.
        """
        tsig = {
                 "name": name or data_utils.rand_name('test-tsig'),
                 "algorithm": algorithm or utils.rand_tsig_algorithm(),
                 "secret": secret or data_utils.rand_name("secret"),
                 "scope": scope or utils.rand_tsig_scope(),
                 "resource_id": resource_id}

        resp, body = self._create_request('tsigkeys', data=tsig,
                                          params=params)

        self.expected_success(201, resp.status)

        return resp, body

    @base.handle_errors
    def list_tsigkeys(self, params=None):
        """Gets a list of tsigkeys.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized tsigkeys as a list.
        """
        return self._list_request('tsigkeys', params=params)

    @base.handle_errors
    def show_tsigkey(self, uuid, params=None):
        """Gets a specific tsigkey.
        :param uuid: Unique identifier of the tsigkey in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized tsigkey as a dictionary.
        """
        return self._show_request('tsigkeys', uuid, params=params)

    @base.handle_errors
    def update_tsigkey(self, uuid, name=None, algorithm=None,
                       secret=None, scope=None, params=None):
        """Update the tsigkey with the specified parameters.
        :param uuid: The unique identifier of the tsigkey..
        :param name: name of the tsigkey.
        :param algorithm: TSIG algorithm e.g hmac-md5, hmac-sha256 etc.
        :param secret: represents TSIG secret.
        :param scope: represents TSIG scope.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the updated tsigkey.
        """
        tsig = {
                 "name": name or data_utils.rand_name('test-tsig'),
                 "algorithm": algorithm or utils.rand_tsig_algorithm(),
                 "secret": secret or data_utils.rand_name("secret"),
                 "scope": scope or utils.rand_tsig_scope()}

        resp, body = self._update_request('tsigkeys', uuid, tsig,
                                          params=params)

        self.expected_success(200, resp.status)

        return resp, body

    @base.handle_errors
    def delete_tsigkey(self, uuid, params=None):
        """Deletes a tsigkey having the specified UUID.
        :param uuid: The unique identifier of the tsigkey.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request('tsigkeys', uuid, params=params)

        self.expected_success(204, resp.status)

        return resp, body
