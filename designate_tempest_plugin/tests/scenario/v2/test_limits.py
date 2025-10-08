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
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class DesignateLimit(base.BaseDnsV2Test):

    credentials = ["primary", "admin"]

    @classmethod
    def setup_clients(cls):
        super(DesignateLimit, cls).setup_clients()
        cls.limit_client = cls.os_primary.dns_v2.DesignateLimitClient()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()
        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(DesignateLimit, cls).resource_setup()
        cls.project_limits = cls.limit_client.list_designate_limits()
        cls.tld = cls.admin_tld_client.create_tld(
            tld_name=dns_data_utils.rand_string(5))[1]

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.tld['id'])
        super(DesignateLimit, cls).resource_cleanup()

    @decorators.idempotent_id('3d1b09a2-b8be-11ec-86fe-201e8823901f')
    def test_max_zone_name_length(self):
        allowed_limit = self.project_limits[
            'max_zone_name_length'] - 1  # The final root null byte
        LOG.info(
            'Attempting to create a Zone of length:{}, expected: zone is'
            ' successfully created'.format(allowed_limit))
        zone_name = dns_data_utils.rand_dns_name_by_size(allowed_limit)
        # Use class TLD at the end of generated Zone Name
        zone_name = zone_name[:-(
                len(self.tld['name']) + 2)] + '.' + self.tld['name'] + '.'
        zone = self.zone_client.create_zone(
            name=zone_name, wait_until=const.ACTIVE)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info(
            'Attempting to create a Zone of length:{}, expected: zone is '
            'failed to be created'.format(allowed_limit + 1))
        zone_name = dns_data_utils.rand_dns_name_by_size(allowed_limit + 1)
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.zone_client.create_zone,
            name=zone_name
        )

    @decorators.idempotent_id('86646744-b98a-11ec-b3a4-201e8823901f')
    def test_max_recordset_name_length(self):
        # The full recordset name is a combination of its short name
        # and the zone name. e.g., "www" + "example.com." = "www.example.com."
        # In this section, we'll set the lengths needed for testing.
        allowed_recordset_limit = self.project_limits[
            'max_recordset_name_length'] - 1  # The final root null byte
        reserved_recordset_length = 10  # Reserved for recordset's host part.
        zone_name_size = allowed_recordset_limit - reserved_recordset_length
        zone_name = dns_data_utils.rand_dns_name_by_size(
            name_size=zone_name_size)
        # Use class TLD at the end of generated Zone Name
        zone_name = zone_name[:-(
                len(self.tld['name']) + 2)] + '.' + self.tld['name'] + '.'
        max_valid_record_name_size = allowed_recordset_limit - len(zone_name)

        LOG.info('Create a Zone')
        zone = self.zone_client.create_zone(
            name=zone_name, wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Recordset name of length:{} is successfully '
                 'created'.format(allowed_recordset_limit))
        recordset_data = dns_data_utils.rand_recordset_data(
            record_type='A',
            zone_name=zone_name,
            # Reserve 1 char for the dot between the record name and zone name.
            name=dns_data_utils.rand_string(
                max_valid_record_name_size - 1) + '.' + zone_name)
        recordset = self.recordset_client.create_recordset(
            zone['id'], recordset_data)[1]
        self.addCleanup(
            self.wait_recordset_delete, self.recordset_client,
            zone['id'], recordset['id'])
        LOG.info(
            'Attempting to create a Recordset of length:{}, expected:'
            ' Recordset is failed to be created'.format(
                allowed_recordset_limit + 1))
        recordset_data = dns_data_utils.rand_recordset_data(
            record_type='A',
            zone_name=zone_name,
            name=dns_data_utils.rand_string(
                max_valid_record_name_size) + '.' + zone_name)

        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.recordset_client.create_recordset,
            zone_uuid=zone['id'],
            recordset_data=recordset_data)
