# Copyright 2023 Red Hat
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
from oslo_utils import versionutils
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import base

CONF = config.CONF
LOG = logging.getLogger(__name__)


class SharedZonesTest(base.BaseDnsV2Test):
    credentials = ['primary', 'admin', 'system_admin', 'alt',
                   ['demo', 'member']]

    @classmethod
    def setup_clients(cls):
        super(SharedZonesTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
        cls.share_zone_client = cls.os_primary.dns_v2.SharedZonesClient()
        cls.rec_client = cls.os_primary.dns_v2.RecordsetClient()
        cls.alt_rec_client = cls.os_alt.dns_v2.RecordsetClient()
        cls.demo_rec_client = cls.os_demo.dns_v2.RecordsetClient()

    @classmethod
    def resource_setup(cls):
        super(SharedZonesTest, cls).resource_setup()

        if not versionutils.is_compatible('2.1', cls.api_version,
                                          same_major=False):
            raise cls.skipException(
                'The shared zones scenario tests require Designate API '
                'version 2.1 or newer. Skipping Shared Zones scenario tests.')

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name='SharedZonesTest')
        cls.tld_name = f'.{tld_name}'
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(SharedZonesTest, cls).resource_cleanup()

    @decorators.attr(type='slow')
    @decorators.idempotent_id('b0fad45d-25ec-49b9-89a8-10b0e3c8b14c')
    def test_zone_share_CRUD_recordset(self):
        # Create a zone to share with the alt credential
        zone_name = dns_data_utils.rand_zone_name(name='TestZone',
                                                  suffix=self.tld_name)
        LOG.info('Create a zone: %s', zone_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        recordset_data = dns_data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        # Check that the alt user has no access to the zone before the share
        self.assertRaises(lib_exc.NotFound,
                          self.alt_rec_client.create_recordset,
                          zone['id'], recordset_data)

        # Check that the demo user has no access to the zone before the share
        self.assertRaises(lib_exc.NotFound,
                          self.demo_rec_client.create_recordset,
                          zone['id'], recordset_data)

        # Share the zone with the alt credential
        shared_zone = self.share_zone_client.create_zone_share(
            zone['id'], self.alt_rec_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        zone['id'], shared_zone['id'])

        # Check that the demo user has no access to the zone after the share
        self.assertRaises(lib_exc.NotFound,
                          self.demo_rec_client.create_recordset,
                          zone['id'], recordset_data)

        # Check that the alt user can create a recordset on the shared zone
        recordset = self.alt_rec_client.create_recordset(zone['id'],
                                                         recordset_data)[1]
        self.addCleanup(self.wait_recordset_delete, self.alt_rec_client,
            zone['id'], recordset['id'], ignore_errors=lib_exc.NotFound)

        # Check that the demo user cannot see the alt recordset
        self.assertRaises(lib_exc.NotFound,
                          self.demo_rec_client.show_recordset,
                          zone['id'], recordset['id'])

        # Check that the alt user can see the alt recordset
        show_recordset = self.alt_rec_client.show_recordset(
            zone['id'], recordset['id'])[1]

        self.assertEqual(recordset['id'], show_recordset['id'])

        # Check that the zone owner can see the alt recordset
        show_recordset = self.rec_client.show_recordset(zone['id'],
                                                        recordset['id'])[1]

        self.assertEqual(recordset['id'], show_recordset['id'])

        recordset_data = {
            'ttl': dns_data_utils.rand_ttl(start=recordset['ttl'] + 1)
        }

        # Check that the demo user cannot update the recordset created by alt
        self.assertRaises(lib_exc.NotFound,
                          self.demo_rec_client.update_recordset,
                          zone['id'], recordset['id'], recordset_data)

        # Check that the alt user can update a recordset on the shared zone
        update = self.alt_rec_client.update_recordset(zone['id'],
            recordset['id'], recordset_data)[1]

        self.assertNotEqual(recordset['ttl'], update['ttl'])

        recordset_data = {
            'ttl': dns_data_utils.rand_ttl(start=update['ttl'] + 1)
        }

        # Check that the zone owner can update a recordset on the shared zone
        primary_update = self.rec_client.update_recordset(zone['id'],
            recordset['id'], recordset_data)[1]

        self.assertNotEqual(update['ttl'], primary_update['ttl'])

        # Check that the demo user cannot delete the alt recordset
        self.assertRaises(lib_exc.NotFound,
                          self.demo_rec_client.delete_recordset,
                          zone['id'], recordset['id'])

        # Check that the alt user can delete it's recordset
        self.alt_rec_client.delete_recordset(zone['id'], recordset['id'])

        LOG.info('Ensure successful deletion of Recordset')
        self.assertRaises(lib_exc.NotFound,
                          self.alt_rec_client.show_recordset,
                          zone['id'], recordset['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('de03b4d3-3ccf-4291-a920-89e2694bba22')
    def test_zone_owner_can_delete_shared_recordset(self):
        # Create a zone to share with the alt credential
        zone_name = dns_data_utils.rand_zone_name(name='TestZone',
                                                  suffix=self.tld_name)
        LOG.info('Create a zone: %s', zone_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        recordset_data = dns_data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        # Share the zone with the alt credential
        shared_zone = self.share_zone_client.create_zone_share(
            zone['id'], self.alt_rec_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        zone['id'], shared_zone['id'])

        # Check that the alt user can create a recordset on the shared zone
        recordset = self.alt_rec_client.create_recordset(zone['id'],
                                                         recordset_data)[1]
        self.addCleanup(self.wait_recordset_delete, self.alt_rec_client,
            zone['id'], recordset['id'], ignore_errors=lib_exc.NotFound)

        # Check that the alt user can see the alt recordset
        show_recordset = self.alt_rec_client.show_recordset(
            zone['id'], recordset['id'])[1]

        self.assertEqual(recordset['id'], show_recordset['id'])

        # Check that the zone owner can delete the recordset
        self.rec_client.delete_recordset(zone['id'], recordset['id'])

        LOG.info('Ensure successful deletion of Recordset')
        self.assertRaises(lib_exc.NotFound,
                          self.alt_rec_client.show_recordset,
                          zone['id'], recordset['id'])
