# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.services.dns.v2.json import base


class ZonesClient(base.DnsClientV2Base):
    """API V2 Tempest REST client for Designate API"""

    @base.handle_errors
    def create_zone(self, name=None, email=None, ttl=None, description=None,
                    wait_until=False, params=None):
        """Create a zone with the specified parameters.

        :param name: The name of the zone.
            Default: Random Value
        :param email: The email for the zone.
            Default: Random Value
        :param ttl: The ttl for the zone.
            Default: Random Value
        :param description: A description of the zone.
            Default: Random Value
        :param wait_until: Block until the zone reaches the desiered status
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the created zone.
        """
        zone = {
            'name': name or dns_data_utils.rand_zone_name(),
            'email': email or dns_data_utils.rand_email(),
            'ttl': ttl or dns_data_utils.rand_ttl(),
            'description': description or data_utils.rand_name('test-zone'),
        }

        resp, body = self._create_request('zones', zone, params=params)

        # Create Zone should Return a HTTP 202
        self.expected_success(202, resp.status)

        if wait_until:
            waiters.wait_for_zone_status(self, body['id'], wait_until)

        return resp, body

    @base.handle_errors
    def show_zone(self, uuid, params=None):
        """Gets a specific zone.
        :param uuid: Unique identifier of the zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized zone as a dictionary.
        """
        return self._show_request('zones', uuid, params=params)

    @base.handle_errors
    def list_zones(self, params=None):
        """Gets a list of zones.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized zones as a list.
        """
        return self._list_request('zones', params=params)

    @base.handle_errors
    def delete_zone(self, uuid, params=None):
        """Deletes a zone having the specified UUID.
        :param uuid: The unique identifier of the zone.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request('zones', uuid, params=params)

        # Delete Zone should Return a HTTP 202
        self.expected_success(202, resp.status)

        return resp, body

    @base.handle_errors
    def update_zone(self, uuid, email=None, ttl=None,
                    description=None, wait_until=False, params=None):
        """Update a zone with the specified parameters.
        :param uuid: The unique identifier of the zone.
        :param email: The email for the zone.
            Default: Random Value
        :param ttl: The ttl for the zone.
            Default: Random Value
        :param description: A description of the zone.
            Default: Random Value
        :param wait_until: Block until the zone reaches the desiered status
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the updated zone.
        """
        zone = {
            'email': email or dns_data_utils.rand_email(),
            'ttl': ttl or dns_data_utils.rand_ttl(),
            'description': description or data_utils.rand_name('test-zone'),
        }

        resp, body = self._update_request('zones', uuid, zone, params=params)

        # Update Zone should Return a HTTP 202
        self.expected_success(202, resp.status)

        if wait_until:
            waiters.wait_for_zone_status(self, body['id'], wait_until)

        return resp, body
