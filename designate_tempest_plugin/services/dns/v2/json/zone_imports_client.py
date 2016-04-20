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
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.services.dns.v2.json import base


class ZoneImportsClient(base.DnsClientV2Base):

    @base.handle_errors
    def create_zone_import(self, zonefile_data=None,
                           params=None, wait_until=None):
        """Create a zone import.
        :param zonefile_data: A tuple that represents zone data.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized imported zone as a dictionary.
        """

        headers = {'Content-Type': 'text/dns'}
        zone_data = zonefile_data or dns_data_utils.rand_zonefile_data()
        resp, body = self._create_request(
            'zones/tasks/imports', zone_data, headers=headers)

        # Create Zone should Return a HTTP 202
        self.expected_success(202, resp.status)

        if wait_until:
            waiters.wait_for_zone_import_status(self, body['id'], wait_until)

        return resp, body

    @base.handle_errors
    def show_zone_import(self, uuid, params=None):
        """Gets a specific zone import.
        :param uuid: Unique identifier of the imported zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized imported zone as a dictionary.
        """
        return self._show_request(
            'zones/tasks/imports', uuid, params=params)

    @base.handle_errors
    def list_zone_imports(self, params=None):
        """Gets all the imported zones.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized imported zones as a list.
        """
        return self._list_request(
            'zones/tasks/imports', params=params)

    @base.handle_errors
    def delete_zone_import(self, uuid, params=None):
        """Deletes a imported zone having the specified UUID.
        :param uuid: The unique identifier of the imported zone.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request(
            'zones/tasks/imports', uuid, params=params)

        # Delete Zone should Return a HTTP 204
        self.expected_success(204, resp.status)

        return resp, body
