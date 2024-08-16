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

from socket import gaierror

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
import testtools

from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

from designate_tempest_plugin.services.dns.query.query_client import (
    SingleQueryClient)

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseZonesTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                    'status', 'action']

    @classmethod
    def setup_clients(cls):
        super(BaseZonesTest, cls).setup_clients()

        cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(BaseZonesTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="BaseZonesTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(BaseZonesTest, cls).resource_cleanup()


class ZoneTasks(BaseZonesTest):
    credentials = ["primary", "alt", "admin",
                   "project_member", "project_reader"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZoneTasks, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZoneTasks, cls).setup_clients()
        cls.admin_client = cls.os_admin.dns_v2.ZonesClient()
        cls.alt_client = cls.os_alt.dns_v2.ZonesClient()

    @decorators.idempotent_id('287e2cd0-a0e7-11eb-b962-74e5f9e2a801')
    @testtools.skipUnless(
        config.CONF.dns.nameservers,
        "Config option dns.nameservers is missing or empty")
    def test_zone_abandon(self):
        LOG.info('Create a PRIMARY zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="zone_abandon", suffix=self.tld_name)
        pr_zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client,
                        pr_zone['id'])
        waiters.wait_for_zone_status(self.zones_client, pr_zone['id'],
                                     'ACTIVE')

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', pr_zone['action'])
        self.assertEqual('PENDING', pr_zone['status'])

        LOG.info('Fetch the zone')
        self.zones_client.show_zone(pr_zone['id'])

        LOG.info('Check that the zone was created on Nameserver/BIND')
        waiters.wait_for_query(self.query_client, pr_zone['name'], "SOA")

        # Test RBAC
        expected_allowed = ['os_admin']

        self.check_CUD_RBAC_enforcement(
            'ZonesClient', 'abandon_zone', expected_allowed, False,
            pr_zone['id'],
            headers={'x-auth-sudo-project-id': pr_zone['project_id']})

        # Test abandoning the zone
        LOG.info('Abandon a zone')
        self.admin_client.abandon_zone(
            pr_zone['id'],
            headers={'x-auth-sudo-project-id': pr_zone['project_id']})

        LOG.info('Wait for the zone to become 404/NotFound in Designate')
        waiters.wait_for_zone_404(self.zones_client, pr_zone['id'])

        LOG.info('Check that the zone is still exists in Nameserver/BIND')
        waiters.wait_for_query(
            self.query_client, pr_zone['name'], "SOA")

    @decorators.idempotent_id('90b21d1a-a1ba-11eb-84fa-74e5f9e2a801')
    @testtools.skipUnless(
        config.CONF.dns.nameservers,
        "Config option dns.nameservers is missing or empty")
    def test_zone_abandon_forbidden(self):

        LOG.info('Create a PRIMARY zone and add to the cleanup')
        zone_name = dns_data_utils.rand_zone_name(
            name="zone_abandon_forbidden", suffix=self.tld_name)
        pr_zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client,
                        pr_zone['id'])
        waiters.wait_for_zone_status(self.zones_client, pr_zone['id'],
                                     'ACTIVE')

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', pr_zone['action'])
        self.assertEqual('PENDING', pr_zone['status'])

        LOG.info('Fetch the zone')
        self.zones_client.show_zone(pr_zone['id'])

        LOG.info('Check that the zone was created on Nameserver/BIND')
        waiters.wait_for_query(self.query_client, pr_zone['name'], "SOA")

        LOG.info('Abandon a zone as primary client, Expected: should '
                 'fail with: 403 forbidden')
        self.assertRaises(
            lib_exc.Forbidden, self.zones_client.abandon_zone,
            zone_id=pr_zone['id'])


class ZoneTasksNegative(BaseZonesTest):
    credentials = ["primary", "alt", "admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZoneTasksNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZoneTasksNegative, cls).setup_clients()
        cls.admin_client = cls.os_admin.dns_v2.ZonesClient()
        cls.alt_client = cls.os_alt.dns_v2.ZonesClient()

    def _query_nameserver(self, nameserver, query_timeout,
                          zone_name, zone_type='SOA'):
        query_succeeded = False
        ns_obj = SingleQueryClient(nameserver, query_timeout)
        try:
            ns_obj.query(zone_name, zone_type)
            query_succeeded = True
        except gaierror as e:
            LOG.info('Function "_query_nameserver" failed with:{} '.format(e))
        return query_succeeded
