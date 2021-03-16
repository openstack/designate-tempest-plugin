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
from oslo_log import log as logging
from tempest.lib import decorators

from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class DesignateLimit(base.BaseDnsV2Test):
    credentials = ['admin']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(DesignateLimit, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(DesignateLimit, cls).setup_clients()

        cls.admin_client = cls.os_admin.designate_limit_client

    @decorators.idempotent_id('828572be-8662-11eb-8ff2-74e5f9e2a801')
    def test_list_designate_limits(self):
        expected_default_limits_fields = [
            "max_page_limit", "max_recordset_name_length",
            "max_recordset_records", "max_zone_name_length",
            "max_zone_records", "max_zone_recordsets",
            "max_zones", "min_ttl"].sort()
        project_limits = self.admin_client.list_designate_limits()
        LOG.info(
            'Retrieved designate limits are: {} '.format(project_limits))
        self.assertEqual(
            expected_default_limits_fields,
            list(project_limits.keys()).sort(),
            'Retrieved fields: {} are not as expected: {} '.format(
                list(project_limits.keys()).sort(),
                expected_default_limits_fields))
