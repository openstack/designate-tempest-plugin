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

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.services.dns.v2.json import base


class QuotasClient(base.DnsClientV2Base):

    @base.handle_errors
    def update_quotas(self, zones=None, zone_records=None,
                      zone_recordsets=None, recordset_records=None,
                      api_export_size=None, project_id=None, params=None,
                      headers=None):
        """Update the quotas for the project id

        :param zones: The limit on zones per tenant
            Default: Random Value
        :param zone_records: The limit on records per zone
            Default: Random Value
        :param zone_recordsets: The limit recordsets per zone
            Default: Random Value
        :param recordset_records: The limit on records per recordset
            Default: Random Value
        :param api_export_size: The limit on size of on exported zone
            Default: Random Value
        :param project_id: Apply the quotas to this project id
            Default: The project id of this client
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param headers (dict): The headers to use for the request.
        :return: A tuple with the server response and the created quota.
        """
        project_id = project_id or self.tenant_id

        quotas = dns_data_utils.rand_quotas(
            zones=zones,
            zone_records=zone_records,
            zone_recordsets=zone_recordsets,
            recordset_records=recordset_records,
            api_export_size=api_export_size,
        )

        resp, body = self._update_request('quotas', project_id, quotas,
                                          params=params, headers=headers,
                                          extra_headers=True)

        self.expected_success(200, resp.status)

        return resp, body

    @base.handle_errors
    def show_quotas(self, project_id=None, params=None, headers=None):
        """Gets a specific quota.

        :param project_id: Show the quotas of this project id
            Default: The project id of this client
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param headers (dict): The headers to use for the request.
        :return: Serialized quota as a dictionary.
        """
        project_id = project_id or self.tenant_id
        return self._show_request('quotas', project_id, params=params,
                                  headers=headers, extra_headers=True)

    @base.handle_errors
    def delete_quotas(self, project_id=None, params=None, headers=None):
        """Resets the quotas for the specified project id

        :param project_id: Reset the quotas of this project id
            Default: The project id of this client
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param headers (dict): The headers to use for the request.
        :return: A tuple with the server response and the response body.
        """
        project_id = project_id or self.tenant_id

        resp, body = self._delete_request(
            'quotas', project_id,
            params=params, headers=headers,
            extra_headers=True)

        self.expected_success(204, resp.status)

        return resp, body
