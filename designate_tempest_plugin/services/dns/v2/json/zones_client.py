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

from designate_tempest_plugin.common import constants as const

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.services.dns.v2.json import base


class ZonesClient(base.DnsClientV2Base):
    """API V2 Tempest REST client for Designate API"""

    @base.handle_errors
    def create_zone(self, name=None, email=None, ttl=None, description=None,
                    attributes=None, wait_until=False,
                    zone_type=const.PRIMARY_ZONE_TYPE,
                    primaries=None, params=None, project_id=None):

        """Create a zone with the specified parameters.

        :param name: The name of the zone.
            Default: Random Value
        :param email: The email for the zone.
            Default: Random Value
        :param ttl: The ttl for the zone.
            Default: Random Value
        :param description: A description of the zone.
            Default: Random Value
        :param attributes: Key:Value pairs of information about this zone,
               and the pool the user would like to place the zone in.
               This information can be used by the scheduler to place
               zones on the correct pool.
        :param wait_until: Block until the zone reaches the desiered status
        :param zone_type: PRIMARY or SECONDARY
            Default: PRIMARY
        :param primaries: List of Primary nameservers. Required for SECONDARY
            Default: None
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param project_id: When specified, overrides the project ID the zone
                           will be associated with.
        :return: A tuple with the server response and the created zone.
        """

        zone = {
            'name': name or dns_data_utils.rand_zone_name()
            if name != '' else '',
            'email': email or dns_data_utils.rand_email()
            if email != '' else '',
            'ttl': ttl or dns_data_utils.rand_ttl()
            if ttl != 0 else 0,
            'description': description or data_utils.rand_name('test-zone')
            if description != '' else '',
            'attributes': attributes or {
                'attribute_key': data_utils.rand_name('attribute_value')}
        }
        # If SECONDARY, "email" and "ttl" cannot be supplied
        if zone_type == const.SECONDARY_ZONE_TYPE:
            zone['type'] = zone_type
            del zone['email']
            del zone['ttl']
            if primaries is None:
                raise AttributeError(
                    'Error - "primaries" is mandatory parameter'
                    ' for a SECONDARY zone type')

            zone['masters'] = primaries

        headers = None
        extra_headers = False
        if project_id:
            headers = {'x-auth-sudo-project-id': project_id}
            extra_headers = True

        resp, body = self._create_request('zones', zone, params=params,
                                          headers=headers,
                                          extra_headers=extra_headers)

        # Create Zone should Return a HTTP 202
        self.expected_success(202, resp.status)

        if wait_until:
            waiters.wait_for_zone_status(self, body['id'], wait_until,
                                         headers=headers)

        return resp, body

    @base.handle_errors
    def show_zone(self, uuid, params=None, headers=None):
        """Gets a specific zone.
        :param uuid: Unique identifier of the zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param headers (dict): The headers to use for the request.
        :return: Serialized zone as a dictionary.
        """
        return self._show_request(
            'zones', uuid, params=params, headers=headers)

    @base.handle_errors
    def show_zone_nameservers(self, zone_uuid, params=None, headers=None):
        """Gets list of Zone Name Servers
        :param zone_uuid: Unique identifier of the zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param headers (dict): The headers to use for the request.
        :return: Serialized nameservers as a list.
        """
        return self._show_request(
            'zones/{0}/nameservers'.format(zone_uuid), uuid=None,
            params=params, headers=headers)

    @base.handle_errors
    def list_zones(self, params=None, headers=None):
        """Gets a list of zones.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param headers (dict): The headers to use for the request.
        :return: Serialized zones as a list.
        """
        return self._list_request('zones', params=params, headers=headers)

    @base.handle_errors
    def delete_zone(self, uuid, params=None, headers=None):
        """Deletes a zone having the specified UUID.
        :param uuid: The unique identifier of the zone.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param headers (dict): The headers to use for the request.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request(
            'zones', uuid, params=params, headers=headers)

        # Delete Zone should Return a HTTP 202
        self.expected_success(202, resp.status)

        return resp, body

    @base.handle_errors
    def update_zone(self, uuid, email=None, ttl=None,
                    description=None, wait_until=False, params=None,
                    headers=None):
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
        :param headers (dict): The headers to use for the request.
        :return: A tuple with the server response and the updated zone.
        """
        zone = {
            'email': email or dns_data_utils.rand_email(),
            'ttl': ttl or dns_data_utils.rand_ttl(),
            'description': description or data_utils.rand_name('test-zone'),
        }

        resp, body = self._update_request('zones', uuid, zone, params=params,
                                          headers=headers)

        # Update Zone should Return a HTTP 202
        self.expected_success(202, resp.status)

        if wait_until:
            waiters.wait_for_zone_status(self, body['id'], wait_until)

        return resp, body

    @base.handle_errors
    def trigger_manual_update(self, zone_id, headers=None):
        """Trigger manually update for secondary zone.

        :param zone_id: Secondary zone ID.
        :param headers (dict): The headers to use for the request.
        :return: A tuple with the server response and body.
        """
        resp, body = self._create_request(
            'zones/{}/tasks/xfr'.format(zone_id), headers=headers)
        # Trigger Zone Update should Return a HTTP 202
        self.expected_success(202, resp.status)
        return resp, body

    @base.handle_errors
    def abandon_zone(self, zone_id, headers=None):
        """This removes a zone from the designate database without removing
         it from the backends.

        :param zone_id: Zone ID.
        :param headers (dict): The headers to use for the request.
        :return: A tuple with the server response and body.
        """
        resp, body = self._create_request(
            'zones/{}/tasks/abandon'.format(zone_id),
            headers=headers,
            expected_statuses=self.DELETE_STATUS_CODES)

        self.expected_success(self.DELETE_STATUS_CODES, resp.status)
        return resp, body
