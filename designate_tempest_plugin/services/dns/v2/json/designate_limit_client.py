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
from designate_tempest_plugin.services.dns.v2.json import base


class DesignateLimitClient(base.DnsClientV2Base):

    @base.handle_errors
    def list_designate_limits(self, headers=None):
        """Show the limits for Designate fields

        :param headers: (dict): The headers to use for the request.
        :return: Dictionary of limits
        """
        return self._list_request(
            'limits', headers=headers)[1]
