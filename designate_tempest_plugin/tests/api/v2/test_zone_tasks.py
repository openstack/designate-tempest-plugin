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
from unittest import expectedFailure

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

from designate_tempest_plugin.services.dns.query.query_client \
    import SingleQueryClient

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseZonesTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                    'status', 'action']

    @classmethod
    def setup_clients(cls):
        super(BaseZonesTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
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
    credentials = ["primary", "alt", "admin", "system_admin", "system_reader",
                   "project_member", "project_reader"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZoneTasks, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZoneTasks, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.ZonesClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.ZonesClient()
        cls.client = cls.os_primary.dns_v2.ZonesClient()
        cls.alt_client = cls.os_alt.dns_v2.ZonesClient()

    @decorators.idempotent_id('287e2cd0-a0e7-11eb-b962-74e5f9e2a801')
    def test_zone_abandon(self):
        LOG.info('Create a PRIMARY zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="zone_abandon", suffix=self.tld_name)
        pr_zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, pr_zone['id'])
        waiters.wait_for_zone_status(self.client, pr_zone['id'], 'ACTIVE')

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', pr_zone['action'])
        self.assertEqual('PENDING', pr_zone['status'])

        LOG.info('Fetch the zone')
        self.client.show_zone(pr_zone['id'])

        LOG.info('Check that the zone was created on Nameserver/BIND')
        waiters.wait_for_query(self.query_client, pr_zone['name'], "SOA")

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

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
        waiters.wait_for_zone_404(self.client, pr_zone['id'])

        LOG.info('Check that the zone is still exists in Nameserver/BIND')
        waiters.wait_for_query(
            self.query_client, pr_zone['name'], "SOA")

    @decorators.idempotent_id('90b21d1a-a1ba-11eb-84fa-74e5f9e2a801')
    def test_zone_abandon_forbidden(self):

        LOG.info('Create a PRIMARY zone and add to the cleanup')
        zone_name = dns_data_utils.rand_zone_name(
            name="zone_abandon_forbidden", suffix=self.tld_name)
        pr_zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, pr_zone['id'])
        waiters.wait_for_zone_status(self.client, pr_zone['id'], 'ACTIVE')

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', pr_zone['action'])
        self.assertEqual('PENDING', pr_zone['status'])

        LOG.info('Fetch the zone')
        self.client.show_zone(pr_zone['id'])

        LOG.info('Check that the zone was created on Nameserver/BIND')
        waiters.wait_for_query(self.query_client, pr_zone['name'], "SOA")

        LOG.info('Abandon a zone as primary client, Expected: should '
                 'fail with: 403 forbidden')
        self.assertRaises(
            lib_exc.Forbidden, self.client.abandon_zone,
            zone_id=pr_zone['id'])


class ZoneTasksNegative(BaseZonesTest):
    credentials = ["primary", "alt", "admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZoneTasksNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZoneTasksNegative, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.ZonesClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.ZonesClient()
        cls.client = cls.os_primary.dns_v2.ZonesClient()
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

    @expectedFailure
    @decorators.idempotent_id('ca250d92-8a2b-11eb-b49b-74e5f9e2a801')
    def test_manually_trigger_update_secondary_zone_negative(self):
        # Create a PRIMARY zone
        LOG.info('Create a PRIMARY zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="manually_trigger_update_primary", suffix=self.tld_name)
        pr_zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, pr_zone['id'])
        waiters.wait_for_zone_status(self.client, pr_zone['id'], 'ACTIVE')

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', pr_zone['action'])
        self.assertEqual('PENDING', pr_zone['status'])

        # Get the Name Servers created for a PRIMARY zone
        nameservers = [
            dic['hostname'] for dic in self.client.show_zone_nameservers(
                pr_zone['id'])[1]['nameservers']]

        # Make sure that the nameservers are not available using DNS
        # query and if it does, skip the test.
        LOG.info('Check if NameServers are available, skip the test if not')
        for ns in nameservers:
            if self._query_nameserver(
                    ns, 5, pr_zone['name'], zone_type='SOA') is True:
                raise self.skipException(
                    "Nameserver:{} is available, but negative test scenario "
                    "needs it to be unavailable, therefore test is "
                    "skipped.".format(ns.strip('.')))

        # Create a SECONDARY zone
        LOG.info('Create a SECONDARY zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="manually_trigger_update_secondary", suffix=self.tld_name)
        sec_zone = self.client.create_zone(name=zone_name,
            zone_type=const.SECONDARY_ZONE_TYPE, primaries=nameservers)[1]
        self.addCleanup(self.wait_zone_delete, self.client, sec_zone['id'])
        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual('CREATE', sec_zone['action'])
        self.assertEqual('PENDING', sec_zone['status'])

        # Manually trigger_update zone
        LOG.info('Manually Trigger an Update of a Secondary Zone when the '
                 'nameservers not pingable. Expected: error status code 500')
        with self.assertRaisesDns(lib_exc.ServerFault, 'unknown', 500):
            self.client.trigger_manual_update(sec_zone['id'])
