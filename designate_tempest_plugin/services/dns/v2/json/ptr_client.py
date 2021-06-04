# Copyright 2021 Red Hat.
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
from tempest import config

CONF = config.CONF


class PtrClient(base.DnsClientV2Base):

    @base.handle_errors
    def set_ptr_record(self, floatingip_id, ptr_name=None,
                       ttl=None, description=None, headers=None,
                       tld=None):
        """Set a PTR record for the given FloatingIP

        :param floatingip_id: valid UUID of floating IP to be used.
        :param ptr_name PTR record name or random if not provided.
        :param ttl TTL or random valid value if not provided.
        :param description Description or random if not provided.
        :param headers (dict): The headers to use for the request.
        :param tld, the TLD to be used in ptrdname generated value.
        :return: created PTR dictionary.
        """
        ptr = {
            'ptrdname': ptr_name or dns_data_utils.rand_domain_name(tld),
            'ttl': ttl or dns_data_utils.rand_ttl(),
            'description': description or data_utils.rand_name('test-ptr')}

        return self._update_request(
            resource='reverse/floatingips/{}'.format(CONF.identity.region),
            uuid=floatingip_id, data=ptr, headers=headers,
            uuid_prefix_char=':')[1]

    @base.handle_errors
    def show_ptr_record(self, floatingip_id, headers=None):
        """Show PTR record for the given FloatingIP

        :param floatingip_id: valid UUID of floating IP to show.
        :param headers (dict): The headers to use for the request.
        :return: Shown PTR dictionary.
        """
        return self._show_request(
            resource='reverse/floatingips/{}'.format(CONF.identity.region),
            uuid=floatingip_id, headers=headers, uuid_prefix_char=':')[1]

    @base.handle_errors
    def list_ptr_records(self, headers=None):
        """List PTR records for the given FloatingIP

        :param headers (dict): The headers to use for the request.
        :return: List of PTR records.
        """
        return self._list_request(
            'reverse/floatingips', headers=headers)[1]['floatingips']

    @base.handle_errors
    def unset_ptr_record(self, floatingip_id, headers=None):
        """Unset the PTR record for a given FloatingIP

        :param floatingip_id: valid UUID of floating IP to unset.
        :param headers (dict): The headers to use for the request.
        :return: Tuple (Response, Body)
        """
        data = {"ptrdname": None}
        resp, body = self._update_request(
            resource='reverse/floatingips/{}'.format(CONF.identity.region),
            uuid=floatingip_id, data=data, headers=headers,
            uuid_prefix_char=':')
        # Unset PTR should Return a HTTP 202
        self.expected_success(202, resp.status)
        return resp, body
