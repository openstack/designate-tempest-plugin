# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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

import time
import math

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
import testtools

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.services.dns.query.query_client \
    import SingleQueryClient

CONF = config.CONF

CONF = config.CONF
LOG = logging.getLogger(__name__)


class ZonesTest(base.BaseDnsV2Test):
    credentials = ["primary", "admin", "system_admin"]

    @classmethod
    def setup_clients(cls):
        super(ZonesTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
            cls.rec_client = cls.os_system_admin.dns_v2.RecordsetClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
            cls.rec_client = cls.os_admin.dns_v2.RecordsetClient()
        cls.client = cls.os_primary.dns_v2.ZonesClient()
        cls.primary_client = cls.os_primary.dns_v2.BlacklistsClient()

    @classmethod
    def resource_setup(cls):
        super(ZonesTest, cls).resource_setup()
        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="ZonesTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(ZonesTest, cls).resource_cleanup()

    @decorators.attr(type='smoke')
    @decorators.attr(type='slow')
    @decorators.idempotent_id('d0648f53-4114-45bd-8792-462a82f69d32')
    def test_create_and_delete_zone(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_and_delete_zone", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Ensure we respond with CREATE+PENDING')
        self.assertEqual(const.CREATE, zone['action'])
        self.assertEqual(const.PENDING, zone['status'])

        waiters.wait_for_zone_status(
            self.client, zone['id'], const.ACTIVE)

        LOG.info('Re-Fetch the zone')
        zone = self.client.show_zone(zone['id'])[1]

        LOG.info('Ensure we respond with NONE+ACTIVE')
        self.assertEqual(const.NONE, zone['action'])
        self.assertEqual(const.ACTIVE, zone['status'])

        LOG.info('Delete the zone')
        zone = self.client.delete_zone(zone['id'])[1]

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual(const.DELETE, zone['action'])
        self.assertEqual(const.PENDING, zone['status'])

        waiters.wait_for_zone_404(self.client, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('cabd6334-ba37-11ec-9d8c-201e8823901f')
    def test_create_and_update_zone(self):

        LOG.info('Create a zone and wait until it becomes ACTIVE')
        orig_ttl = 666
        orig_description = 'test_create_and_update_zone: org description'
        zone_name = dns_data_utils.rand_zone_name(
            name="create_and_update_zone", suffix=self.tld_name)
        zone = self.client.create_zone(
            name=zone_name,
            ttl=orig_ttl, description=orig_description,
            wait_until=const.ACTIVE)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info("Update zone's: TTL and Description, wait until ACTIVE")
        updated_ttl = 777
        updated_description = dns_data_utils.rand_string(20)
        self.client.update_zone(
            zone['id'], ttl=updated_ttl, description=updated_description,
            wait_until=const.ACTIVE)

        LOG.info('Re-Fetch/Show the zone')
        show_zone = self.client.show_zone(zone['id'])[1]

        LOG.info('Ensure that the Description and TLL has been updated')
        self.assertEqual(
            updated_ttl, show_zone['ttl'],
            'Failed, actual TTL value:{} is not as expected:{} after '
            'the update)'.format(show_zone['ttl'], updated_ttl))
        self.assertEqual(
            updated_description, show_zone['description'],
            'Failed, actual Description:{} is not as expected:{} after '
            'the update)'.format(show_zone['description'], orig_description))

    @decorators.attr(type='slow')
    @decorators.idempotent_id('c9838adf-14dc-4097-9130-e5cea3727abb')
    def test_delete_zone_pending_create(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="delete_zone_pending_create", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        # NOTE(kiall): This is certainly a little racey, it's entirely
        #              possible the zone will become active before we delete
        #              it. Worst case, that means we get an unexpected pass.
        #              Theres not a huge amount we can do, given this is
        #              black-box testing.
        LOG.info('Delete the zone while it is still pending')
        zone = self.client.delete_zone(zone['id'])[1]

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual(const.DELETE, zone['action'])
        self.assertEqual(const.PENDING, zone['status'])

        waiters.wait_for_zone_404(self.client, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('ad8d1f5b-da66-46a0-bbee-14dc84a5d791')
    @testtools.skipUnless(
        config.CONF.dns.nameservers,
        "Config option dns.nameservers is missing or empty")
    def test_zone_create_propagates_to_nameservers(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="zone_create_propagates", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])

        waiters.wait_for_zone_status(self.client, zone['id'], const.ACTIVE)
        waiters.wait_for_query(self.query_client, zone['name'], const.SOA)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('d13d3095-c78f-4aae-8fe3-a74ccc335c84')
    @testtools.skipUnless(
        config.CONF.dns.nameservers,
        "Config option dns.nameservers is missing or empty")
    def test_zone_delete_propagates_to_nameservers(self):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="zone_delete_propagates", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        waiters.wait_for_zone_status(self.client, zone['id'], const.ACTIVE)
        waiters.wait_for_query(self.query_client, zone['name'], const.SOA)

        LOG.info('Delete the zone')
        self.client.delete_zone(zone['id'])

        waiters.wait_for_zone_404(self.client, zone['id'])
        waiters.wait_for_query(self.query_client, zone['name'], const.SOA,
                               found=False)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('ff9b9fc4-85b4-11ec-bcf5-201e8823901f')
    @testtools.skipUnless(
        config.CONF.dns.nameservers,
        "Config option dns.nameservers is missing or empty")
    def test_notify_msg_sent_to_nameservers(self):

        # Test will only run when the SOA record Refresh is close to one hour,
        # otherwise skipped.
        # This implies that the only reason "A" record was propagated is as a
        # result of successfully sent NOTIFY message.

        LOG.info('Create a zone, wait until ACTIVE and get the Serial'
                 ' and SOA Refresh values')
        zone_name = dns_data_utils.rand_zone_name(
            name="test_notify_msg_sent_to_nameservers", suffix=self.tld_name)
        zone = self.client.create_zone(name=zone_name, wait_until='ACTIVE')[1]

        org_serial = zone['serial']
        self.addCleanup(self.wait_zone_delete, self.client, zone['id'])
        try:
            soa = [
                rec['records'] for rec in self.rec_client.list_recordset(
                    zone['id'], headers=self.all_projects_header)[1][
                    'recordsets'] if rec['type'] == 'SOA'][0]
            refresh = int(soa[0].split(' ')[3])
            if math.isclose(3600, refresh, rel_tol=0.1) is False:
                raise self.skipException(
                    'Test is skipped, actual SOA REFRESH is:{} unlike test'
                    ' prerequisites that requires a value close to 3600'
                    ' (one hour)'.format(refresh))
        except Exception as e:
            raise self.skipException(
                'Test is skipped, something went wrong on getting SOA REFRESH'
                ' value, the error was:{}'.format(e))

        LOG.info("Update Zone's TTL, wait until ACTIVE and"
                 " ensure Zone's Serial has changed")
        updated_zone = self.client.update_zone(
            zone['id'], ttl=dns_data_utils.rand_ttl(), wait_until='ACTIVE')[1]
        new_serial = updated_zone['serial']
        self.assertNotEqual(
            new_serial, org_serial,
            "Failed, expected behaviour is that the Designate DNS changes the"
            " Serial after updating Zone's TTL value")
        waiters.wait_for_query(self.query_client, zone['name'], "SOA")

        LOG.info('Per Nameserver "dig" for a SOA record until either:'
                 ' updated Serial is detected or build timeout has reached')
        for ns in config.CONF.dns.nameservers:
            start = time.time()
            while True:
                ns_obj = SingleQueryClient(ns, config.CONF.dns.query_timeout)
                ns_soa_record = ns_obj.query(zone['name'], rdatatype='SOA')
                if str(new_serial) in str(ns_soa_record):
                    return
                if time.time() - start >= config.CONF.dns.build_timeout:
                    raise lib_exc.TimeoutException(
                        'Failed, expected Serial:{} for a Zone was not'
                        ' detected on Nameserver:{} within a timeout of:{}'
                        ' seconds.'.format(
                            new_serial, ns, config.CONF.dns.build_timeout))
