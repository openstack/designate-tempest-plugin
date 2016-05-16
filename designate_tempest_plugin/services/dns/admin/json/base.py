# Copyright 2016 Rackspace
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
from designate_tempest_plugin.services.dns.json import base

handle_errors = base.handle_errors


class DnsClientAdminBase(base.DnsClientBase):
    """Base Admin API Tempest REST client for Designate API"""
    uri_prefix = 'admin'

    CREATE_STATUS_CODES = [201, 202]
    SHOW_STATUS_CODES = [200]
    LIST_STATUS_CODES = [200]
    PUT_STATUS_CODES = [200, 202]
    UPDATE_STATUS_CODES = [200, 202]
    DELETE_STATUS_CODES = [202, 204]
