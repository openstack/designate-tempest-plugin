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
import requests

from oslo_log import log as logging
from tempest.lib import decorators

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.services.dns.v2.json import base as service_base

from tempest import config

CONF = config.CONF
LOG = logging.getLogger(__name__)


class DesignateApiVersion(base.BaseDnsV2Test, service_base.DnsClientV2Base):
    credentials = ['admin', 'primary']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(DesignateApiVersion, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(DesignateApiVersion, cls).setup_clients()

        cls.admin_client = cls.os_admin.dns_v2.ApiVersionClient()
        cls.primary_client = cls.os_primary.dns_v2.ApiVersionClient()

    @decorators.idempotent_id('aa84986e-f2ad-11eb-b58d-74e5f9e2a801')
    def test_list_enabled_api_versions(self):
        for user in ['admin', 'primary', 'not_auth_user']:
            if user == 'admin':
                ver_doc = self.admin_client.list_enabled_api_versions()[1]
                # The version document was updated to match OpenStack
                # version discovery standards in Zed. Accomodate the legacy
                # format for backward compatibility.
                try:
                    versions = ver_doc['versions']['values']
                except TypeError:
                    versions = ver_doc['versions']
            if user == 'primary':
                ver_doc = self.primary_client.list_enabled_api_versions()[1]
                # The version document was updated to match OpenStack
                # version discovery standards in Zed. Accomodate the legacy
                # format for backward compatibility.
                try:
                    versions = ver_doc['versions']['values']
                except TypeError:
                    versions = ver_doc['versions']
            if user == 'not_auth_user':
                response = requests.get(self.primary_client.base_url,
                                        verify=False)
                headers = {
                    k.lower(): v.lower() for k, v in response.headers.items()}
                # The version document was updated to match OpenStack
                # version discovery standards in Zed. Accomodate the legacy
                # format for backward compatibility.
                try:
                    versions = self.deserialize(
                        headers, str(response.text))['versions']['values']
                except TypeError:
                    versions = self.deserialize(
                        headers, str(response.text))['versions']

            LOG.info('Received enabled API versions for {} '
                     'user are:{}'.format(user, versions))
            for item in versions:
                enabled_ids = [
                    item['id'] for key in item.keys() if key == 'id']
            LOG.info('Enabled versions IDs are:{}'.format(enabled_ids))
            possible_options = [['v1'], ['v2'], ['v1', 'v2'], ['v2.0']]
            self.assertIn(
                enabled_ids, possible_options,
                'Failed, received version: {} is not in possible options'
                ' list:{}'.format(enabled_ids, possible_options))
