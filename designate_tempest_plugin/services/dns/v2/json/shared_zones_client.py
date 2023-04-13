# Copyright 2020 Cloudification GmbH. All rights reserved.
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


class SharedZonesClient(base.DnsClientV2Base):

    @base.handle_errors
    def create_zone_share(self, zone_id, target_project_id, headers=None):
        """Create a new zone share for a project ID.

        :param zone_id: Zone UUID to share
        :param target_project_id: Project ID that will gain access to specified
                                  zone
        :param headers: (dict): The headers to use for the request.
        :return: Zone share dict
        """
        resp, body = self._create_request(
            'zones/{}/shares'.format(zone_id),
            data={'target_project_id': target_project_id}, headers=headers,
            extra_headers=True)

        # Endpoint should Return a HTTP 201
        self.expected_success(201, resp.status)

        return resp, body

    @base.handle_errors
    def show_zone_share(self, zone_id, zone_share_id, headers=None):
        """Get the zone share object

        :param zone_id: Zone UUID for the share
        :param zone_share_id: The zone share ID
        :param headers: (dict): The headers to use for the request.
        :return: Zone share dict
        """
        return self._show_request('zones/{}/shares'.format(zone_id),
                                  zone_share_id, headers=headers)

    @base.handle_errors
    def list_zone_shares(self, zone_id, params=None, headers=None):
        """List zone shares

        :param zone_id: Zone UUID to query for the shares
        :param params: A Python dict that represents the query parameters to
                       include in the request URI.
        :param headers: (dict): The headers to use for the request.
        :return: Zone shares list.
        """
        return self._list_request('zones/{}/shares'.format(zone_id),
                                  params=params, headers=headers)

    @base.handle_errors
    def delete_zone_share(self, zone_id, zone_share_id, headers=None):
        """Deletes the zone share

        :param zone_id: Zone UUID for the share
        :param zone_share_id: The zone share ID
        :param headers: (dict): The headers to use for the request.
        :return: None
        """
        resp, body = self._delete_request('zones/{}/shares'.format(zone_id),
                                          zone_share_id, headers=headers)

        # Endpoint should Return a HTTP 204 - No Content
        self.expected_success(204, resp.status)

        return resp, body
