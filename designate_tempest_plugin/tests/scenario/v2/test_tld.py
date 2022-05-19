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
from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TldZoneTest(base.BaseDnsV2Test):
    credentials = ["admin", "system_admin", "primary"]
    tld_suffix = '.'.join(["TldZoneTest", CONF.dns.tld_suffix])

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TldZoneTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TldZoneTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
        cls.primary_tld_client = cls.os_primary.dns_v2.TldClient()
        cls.primary_zone_client = cls.os_primary.dns_v2.ZonesClient()

    @classmethod
    def resource_setup(cls):
        super(TldZoneTest, cls).resource_setup()
        cls.class_tld = cls.admin_tld_client.create_tld(
            tld_name=cls.tld_suffix)

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(TldZoneTest, cls).resource_cleanup()

    @decorators.idempotent_id('68b3e7cc-bf0e-11ec-b803-201e8823901f')
    def test_create_zone_using_existing_tld(self):
        LOG.info('Creates a zone using existing TLD:"{}"'.format(
            self.tld_suffix))
        zone_name = dns_data_utils.rand_zone_name(
            name='existing_tld_zone', prefix='rand',
            suffix='.{}.'.format(self.tld_suffix))
        zone = self.primary_zone_client.create_zone(
            name=zone_name, wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete, self.primary_zone_client, zone['id'])

    @decorators.idempotent_id('06deced8-d4de-11eb-b8ee-74e5f9e2a801')
    def test_create_zone_using_not_existing_tld(self):
        LOG.info('Try to create a Zone using not existing TLD:"{}"'.format(
            self.tld_suffix[::-1]))
        zone_name = dns_data_utils.rand_zone_name(
            name='not_existing_tld_zone', prefix='rand',
            suffix='.{}.'.format(self.tld_suffix)[::-1])
        self.assertRaises(
            lib_exc.BadRequest, self.primary_zone_client.create_zone,
            name=zone_name)
