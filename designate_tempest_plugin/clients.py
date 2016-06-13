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
from tempest import clients
from tempest import config
from tempest.lib.auth import KeystoneV2AuthProvider

from designate_tempest_plugin.services.dns.v1.json.domains_client import \
    DomainsClient
from designate_tempest_plugin.services.dns.v1.json.records_client import \
    RecordsClient
from designate_tempest_plugin.services.dns.v1.json.servers_client import \
    ServersClient
from designate_tempest_plugin.services.dns.v2.json.zones_client import \
    ZonesClient
from designate_tempest_plugin.services.dns.v2.json.zone_imports_client import \
    ZoneImportsClient
from designate_tempest_plugin.services.dns.v2.json.blacklists_client import \
    BlacklistsClient
from designate_tempest_plugin.services.dns.admin.json.quotas_client import \
    QuotasClient
from designate_tempest_plugin.services.dns.v2.json.zone_exports_client import \
    ZoneExportsClient
from designate_tempest_plugin.services.dns.v2.json.recordset_client import \
    RecordsetClient
from designate_tempest_plugin.services.dns.v2.json.pool_client import \
    PoolClient
from designate_tempest_plugin.services.dns.v2.json.tld_client import \
    TldClient
from designate_tempest_plugin.services.dns.query.query_client import \
    QueryClient
from designate_tempest_plugin.services.dns.v2.json.transfer_request_client \
    import TransferRequestClient
from designate_tempest_plugin.services.dns.v2.json.transfer_accepts_client \
    import TransferAcceptClient
from designate_tempest_plugin.services.dns.v2.json.tsigkey_client \
    import TsigkeyClient

CONF = config.CONF


class ManagerV1(clients.Manager):

    def __init__(self, credentials=None, service=None):
        super(ManagerV1, self).__init__(credentials, service)
        self._init_clients(self._get_params())

    def _init_clients(self, params):
        self.domains_client = DomainsClient(**params)
        self.records_client = RecordsClient(**params)
        self.servers_client = ServersClient(**params)

    def _get_params(self):
        params = dict(self.default_params)
        params.update({
            'auth_provider': self.auth_provider,
            'service': CONF.dns.catalog_type,
            'region': CONF.identity.region,
            'endpoint_type': CONF.dns.endpoint_type,
            'build_interval': CONF.dns.build_interval,
            'build_timeout': CONF.dns.build_timeout
        })
        return params


class ManagerV2(clients.Manager):

    def __init__(self, credentials=None, service=None):
        super(ManagerV2, self).__init__(credentials, service)
        self._init_clients(self._get_params())

    def _init_clients(self, params):
        self.zones_client = ZonesClient(**params)
        self.zone_imports_client = ZoneImportsClient(**params)
        self.blacklists_client = BlacklistsClient(**params)
        self.quotas_client = QuotasClient(**params)
        self.zone_exports_client = ZoneExportsClient(**params)
        self.recordset_client = RecordsetClient(**params)
        self.pool_client = PoolClient(**params)
        self.tld_client = TldClient(**params)
        self.transfer_request_client = TransferRequestClient(**params)
        self.transfer_accept_client = TransferAcceptClient(**params)
        self.tsigkey_client = TsigkeyClient(**params)

        self.query_client = QueryClient(
            nameservers=CONF.dns.nameservers,
            query_timeout=CONF.dns.query_timeout,
            build_interval=CONF.dns.build_interval,
            build_timeout=CONF.dns.build_timeout,
        )

    def _get_params(self):
        params = dict(self.default_params)
        params.update({
            'auth_provider': self.auth_provider,
            'service': CONF.dns.catalog_type,
            'region': CONF.identity.region,
            'endpoint_type': CONF.dns.endpoint_type,
            'build_interval': CONF.dns.build_interval,
            'build_timeout': CONF.dns.build_timeout
        })
        return params


class ManagerV2Unauthed(ManagerV2):

    def __init__(self, credentials=None, service=None):
        super(ManagerV2Unauthed, self).__init__(credentials, service)
        self.auth_provider = KeystoneV2UnauthedProvider(
            credentials=self.auth_provider.credentials,
            auth_url=self.auth_provider.auth_client.auth_url,
            disable_ssl_certificate_validation=self.auth_provider.dscv,
            ca_certs=self.auth_provider.ca_certs,
            trace_requests=self.auth_provider.trace_requests,
        )
        self._init_clients(self._get_params())


class KeystoneV2UnauthedProvider(KeystoneV2AuthProvider):
    """This auth provider will ensure requests are made without a token"""

    def _decorate_request(self, filters, method, url, headers=None, body=None,
                          auth_data=None):
        result = super(KeystoneV2UnauthedProvider, self)._decorate_request(
            filters, method, url, headers=headers, body=body,
            auth_data=auth_data)
        url, headers, body = result
        try:
            del headers['X-Auth-Token']
        except KeyError:
            pass
        return url, headers, body
