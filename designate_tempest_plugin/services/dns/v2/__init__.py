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

from .json.blacklists_client import BlacklistsClient
from .json.designate_limit_client import DesignateLimitClient
from .json.pool_client import PoolClient
from .json.ptr_client import PtrClient
from .json.quotas_client import QuotasClient
from .json.recordset_client import RecordsetClient
from .json.service_client import ServiceClient
from .json.shared_zones_client import SharedZonesClient
from .json.tld_client import TldClient
from .json.transfer_accepts_client import TransferAcceptClient
from .json.transfer_request_client import TransferRequestClient
from .json.tsigkey_client import TsigkeyClient
from .json.zones_client import ZonesClient
from .json.zone_exports_client import ZoneExportsClient
from .json.zone_imports_client import ZoneImportsClient
from .json.api_version_client import ApiVersionClient

__all__ = ['BlacklistsClient', 'DesignateLimitClient', 'PoolClient',
           'PtrClient', 'QuotasClient', 'RecordsetClient', 'ServiceClient',
           'SharedZonesClient', 'TldClient', 'TransferAcceptClient',
           'TransferRequestClient', 'TsigkeyClient', 'ZonesClient',
           'ZoneExportsClient', 'ZoneImportsClient', 'ApiVersionClient']
