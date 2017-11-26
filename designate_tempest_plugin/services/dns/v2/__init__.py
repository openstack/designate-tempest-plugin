# Copyright (c) 2017 Andrea Frittoli
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from designate_tempest_plugin.services.dns.v2.json.blacklists_client import \
    BlacklistsClient
from designate_tempest_plugin.services.dns.v2.json.pool_client import \
    PoolClient
from designate_tempest_plugin.services.dns.v2.json.quotas_client import \
    QuotasClient
from designate_tempest_plugin.services.dns.v2.json.recordset_client import \
    RecordsetClient
from designate_tempest_plugin.services.dns.v2.json.tld_client import TldClient
from designate_tempest_plugin.services.dns.v2.json.transfer_accepts_client \
    import TransferAcceptClient
from designate_tempest_plugin.services.dns.v2.json.transfer_request_client \
    import TransferRequestClient
from designate_tempest_plugin.services.dns.v2.json.tsigkey_client import \
    TsigkeyClient
from designate_tempest_plugin.services.dns.v2.json.zone_exports_client import \
    ZoneExportsClient
from designate_tempest_plugin.services.dns.v2.json.zone_imports_client import \
    ZoneImportsClient
from designate_tempest_plugin.services.dns.v2.json.zones_client import \
    ZonesClient

__all__ = ['BlacklistsClient', 'PoolClient', 'QuotasClient', 'RecordsetClient',
           'TldClient', 'TransferAcceptClient', 'TransferRequestClient',
           'TsigkeyClient', 'ZoneExportsClient', 'ZoneImportsClient',
           'ZonesClient']
