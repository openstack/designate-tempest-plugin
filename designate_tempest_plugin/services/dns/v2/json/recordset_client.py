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


class RecordsetClient(base.DnsClientV2Base):
    """API V2 Tempest REST client for Recordset API"""

    SHOW_STATUS_CODES = [200, 301]

    def __init__(self, auth_provider, service, region,
                 endpoint_type='publicURL',
                 build_interval=1, build_timeout=60,
                 disable_ssl_certificate_validation=False, ca_certs=None,
                 trace_requests='', name=None, http_timeout=None,
                 proxy_url=None):
        super(RecordsetClient, self).__init__(
                auth_provider, service, region, endpoint_type, build_interval,
                build_timeout, disable_ssl_certificate_validation, ca_certs,
                trace_requests, name, http_timeout, proxy_url,
                follow_redirects=False)

    @base.handle_errors
    def create_recordset(self, zone_uuid, recordset_data,
                         params=None, wait_until=False):
        """Create a recordset for the specified zone.

        :param zone_uuid: Unique identifier of the zone in UUID format..
        :param recordset_data: A dictionary that represents the recordset
                               data.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the created zone.
        """
        resp, body = self._create_request(
            "/zones/{0}/recordsets".format(zone_uuid), params=params,
            data=recordset_data)

        # Create Recordset should Return a HTTP 202
        self.expected_success(202, resp.status)

        if wait_until:
            waiters.wait_for_recordset_status(self, body['id'], wait_until)

        return resp, body

    @base.handle_errors
    def update_recordset(self, zone_uuid, recordset_uuid,
                         recordet_data, params=None):
        """Update the recordset related to the specified zone.
        :param zone_uuid: Unique identifier of the zone in UUID format.
        :param recordset_uuid: Unique identifier of the recordset in UUID
                               format.
        :param recordset_data: A dictionary that represents the recordset
                               data.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the created zone.
        """
        resp, body = self._put_request(
            'zones/{0}/recordsets'.format(zone_uuid), recordset_uuid,
            data=recordet_data, params=params)

        # Update Recordset should Return a HTTP 202, or a 200 if the recordset
        # is already active
        self.expected_success([200, 202], resp.status)

        return resp, body

    @base.handle_errors
    def show_recordset(self, zone_uuid, recordset_uuid, params=None):
        """Gets a specific recordset related to a specific zone.
        :param zone_uuid: Unique identifier of the zone in UUID format.
        :param recordset_uuid: Unique identifier of the recordset in
                               UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized recordset as a list.
        """
        return self._show_request(
            'zones/{0}/recordsets'.format(zone_uuid), recordset_uuid,
            params=params)

    @base.handle_errors
    def delete_recordset(self, zone_uuid, recordset_uuid, params=None):
        """Deletes a recordset related to the specified zone UUID.
        :param zone_uuid: The unique identifier of the zone.
        :param recordset_uuid: The unique identifier of the record in
                               uuid format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._delete_request(
            'zones/{0}/recordsets'.format(zone_uuid), recordset_uuid)

        # Delete Recordset should Return a HTTP 202
        self.expected_success(202, resp.status)

        return resp, body

    @base.handle_errors
    def list_recordset(self, uuid, params=None):
        """List recordsets related to the specified zone.
        :param uuid: Unique identifier of the zone in UUID format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized recordset as a list.
        """
        return self._list_request(
            'zones/{0}/recordsets'.format(uuid), params=params)

    @base.handle_errors
    def show_zones_recordset(self, recordset_uuid, params=None):
        """Gets a single recordset, using the cross_zone endpoint
        :param recordset_uuid: Unique identifier of the recordset in UUID
                               format.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: A tuple with the server response and the response body.
        """
        resp, body = self._show_request(
            'recordsets', recordset_uuid,
            params=params)

        # Show recordsets/id should return a HTTP 301
        self.expected_success(301, resp.status)

        return resp, body

    @base.handle_errors
    def list_zones_recordsets(self, params=None):
        """List recordsets across all zones.
        :param params: A Python dict that represents the query paramaters to
                       include in the request URI.
        :return: Serialized recordset as a list.
        """
        return self._list_request(
            'recordsets', params=params)
