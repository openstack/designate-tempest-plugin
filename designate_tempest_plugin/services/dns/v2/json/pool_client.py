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

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.services.dns.v2.json import base


class PoolClient(base.DnsClientV2Base):
    """API V2 Tempest REST client for Pool API"""

    @base.handle_errors
    def create_pool(self, pool_name=None, ns_records=None, params=None):
        """Create a pool with the specified parameters.
        :param pool_name: name of the pool.
            Default: Random Value.
        :param ns_records: A dictionary representing the nameservers detail
                           with priority.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the created pool.
        """
        pool = {
                 "name": pool_name or data_utils.rand_name(name="Demo pool"),
                 "ns_records": ns_records or dns_data_utils.rand_ns_records()
        }

        resp, body = self._create_request('pools', data=pool, params=params)

        # Create Pool should Return a HTTP 201
        self.expected_success(201, resp.status)

        return resp, body

    @base.handle_errors
    def show_pool(self, uuid, params=None):
        """Gets a specific pool.
        :param uuid: Unique identifier of the pool in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized pool as a dictionary.
        """
        return self._show_request('pools', uuid, params=params)

    @base.handle_errors
    def list_pools(self, params=None):
        """Gets a list of pools.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized pools as a list.
        """
        return self._list_request('pools', params=params)

    @base.handle_errors
    def delete_pool(self, uuid, params=None):
        """Deletes a pool having the specified UUID.
        :param uuid: The unique identifier of the pool.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request('pools', uuid, params=params)

        # Delete Pool should Return a HTTP 204
        self.expected_success(204, resp.status)

        return resp, body

    @base.handle_errors
    def update_pool(self, uuid, pool_name=None, ns_records=None,
                    params=None):
        """Update a pool with the specified parameters.
        :param uuid: The unique identifier of the pool.
        :param pool_name: name of the pool.
            Default: Random Value.
        :param pool: A dictionary represening the nameservers detail with
                     priority.
            Default: Random Value.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the updated pool.
        """

        pool = {
                 "name": pool_name or data_utils.rand_name(name="Demo pool"),
                 "ns_records": ns_records or dns_data_utils.rand_ns_records()
        }

        resp, body = self._update_request('pools', uuid, pool,
                                          params=params)

        # Update Pool should Return a HTTP 202
        self.expected_success(202, resp.status)

        return resp, body
