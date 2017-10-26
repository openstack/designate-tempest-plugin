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

from designate_tempest_plugin.services.dns.v1.json.domains_client import \
    DomainsClient
from designate_tempest_plugin.services.dns.v1.json.records_client import \
    RecordsClient
from designate_tempest_plugin.services.dns.v1.json.servers_client import \
    ServersClient

__all__ = ['DomainsClient', 'RecordsClient', 'ServersClient']
