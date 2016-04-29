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

from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.services.dns.v2.json import base


class ZoneExportsClient(base.DnsClientV2Base):

    @base.handle_errors
    def create_zone_export(self, uuid, params=None, wait_until=False):
        """Create a zone export.
        :param uuid: Unique identifier of the zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :param wait_until: Block until the exported zone reaches the
                           desired status
        :return: Serialized imported zone as a dictionary.
        """

        export_uri = 'zones/{0}/tasks/export'.format(uuid)
        resp, body = self._create_request(
            export_uri, params=params)

        # Create Zone Export should Return a HTTP 202
        self.expected_success(202, resp.status)

        if wait_until:
            waiters.wait_for_zone_export_status(self, body['id'], wait_until)

        return resp, body

    @base.handle_errors
    def show_zone_export_records(self, uuid, params=None):
        """Gets a specific exported zone.
        :param uuid: Unique identifier of the exported zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized exported zone as a dictionary.
        """
        return self._show_request(
             'zones/tasks/exports', uuid, params=params)

    @base.handle_errors
    def show_zone_exported(self, uuid, params=None):
        """Gets a specific exported zone.
        :param uuid: Unique identifier of the exported zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized exported zone as a dictionary.
        """
        headers = {'Accept': 'text/dns'}

        return self._show_request(
            'zones/tasks/exports/{0}/export'.format(uuid),
            headers=headers, params=params)

    @base.handle_errors
    def list_zones_exports(self, params=None):
        """Gets all the exported zones
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized exported zone as a list.
        """
        return self._list_request(
            'zones/tasks/exports', params=params)

    @base.handle_errors
    def delete_zone_export(self, uuid, params=None):
        """Deletes an exported zone having the specified UUID.
        :param uuid: The unique identifier of the exported zone.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request(
            'zones/tasks/exports', uuid, params=params)

        # Delete Zone export should Return a HTTP 204
        self.expected_success(204, resp.status)

        return resp, body
