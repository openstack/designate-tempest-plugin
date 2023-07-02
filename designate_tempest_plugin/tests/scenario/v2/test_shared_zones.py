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
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import waiters
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
            cls.adm_shr_client = cls.os_system_admin.dns_v2.SharedZonesClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
            cls.adm_shr_client = cls.os_admin.dns_v2.SharedZonesClient()
        cls.share_zone_client = cls.os_primary.dns_v2.SharedZonesClient()
        cls.rec_client = cls.os_primary.dns_v2.RecordsetClient()
        cls.alt_rec_client = cls.os_alt.dns_v2.RecordsetClient()
        cls.demo_rec_client = cls.os_demo.dns_v2.RecordsetClient()
        cls.primary_import_client = cls.os_primary.dns_v2.ZoneImportsClient()

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

    @decorators.attr(type='slow')
    @decorators.idempotent_id('fb170be8-c0bc-11ed-99a3-201e8823901f')
    def test_admin_zone_share_CRUD_recordset(self):

        # Create a zone to share with the alt credential
        zone_name = dns_data_utils.rand_zone_name(name='TestZone',
                                                  suffix=self.tld_name)
        LOG.info('Create a zone: %s', zone_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        # Generate recordset data to be used latter in the test
        recordset_data = dns_data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        # Check that the alt user has no access to the zone before the share
        self.assertRaises(lib_exc.NotFound,
                          self.alt_rec_client.create_recordset,
                          zone['id'], recordset_data)

        # Admin creates shared zone for Alt using "x-auth-sudo-project-id"
        sudo_header = {
            'x-auth-sudo-project-id': self.zones_client.project_id}
        shared_zone = self.adm_shr_client.create_zone_share(
            zone['id'], self.alt_rec_client.project_id,
            headers=sudo_header)[1]
        self.addCleanup(
            self.adm_shr_client.delete_zone_share, zone['id'],
            shared_zone['id'], headers=sudo_header)

        # Check that the alt user can create a recordset on the shared zone
        recordset = self.alt_rec_client.create_recordset(zone['id'],
                                                         recordset_data)[1]
        self.addCleanup(self.wait_recordset_delete, self.alt_rec_client,
            zone['id'], recordset['id'], ignore_errors=lib_exc.NotFound)

        # Check that the alt user can see the alt recordset
        show_recordset = self.alt_rec_client.show_recordset(
            zone['id'], recordset['id'])[1]
        self.assertEqual(recordset['id'], show_recordset['id'])

        # Check that the zone owner can see the alt recordset
        show_recordset = self.rec_client.show_recordset(
            zone['id'], recordset['id'])[1]
        self.assertEqual(recordset['id'], show_recordset['id'])
        recordset_data = {
            'ttl': dns_data_utils.rand_ttl(start=recordset['ttl'] + 1)
        }

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

        # Check that the alt user can delete it's recordset
        self.alt_rec_client.delete_recordset(zone['id'], recordset['id'])
        LOG.info('Ensure successful deletion of Recordset')
        self.assertRaises(lib_exc.NotFound,
                          self.alt_rec_client.show_recordset,
                          zone['id'], recordset['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('b7dd37b8-c3ea-11ed-a102-201e8823901f')
    def test_share_imported_zone(self):
        # Primary user imports zone from a zone file
        zone_name = dns_data_utils.rand_zone_name(
            name="test_share_imported_zone", suffix=self.tld_name)
        zone_data = dns_data_utils.rand_zonefile_data(name=zone_name)
        zone_import = self.primary_import_client.create_zone_import(
            zonefile_data=zone_data)[1]
        self.addCleanup(
            self.primary_import_client.delete_zone_import, zone_import['id'])
        waiters.wait_for_zone_import_status(
            self.primary_import_client, zone_import['id'], const.COMPLETE)

        # Primary shares previously created zone with Alt user
        zone_id = self.primary_import_client.show_zone_import(
            zone_import['id'])[1]['zone_id']
        shared_zone = self.share_zone_client.create_zone_share(
            zone_id, self.alt_rec_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        zone_id, shared_zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('c5d83684-18cb-11ee-a872-201e8823901f')
    def test_list_zones_shared_with_more_then_two_projects(self):
        # Create a zone to share with the alt credentialzones_client
        zone_name = dns_data_utils.rand_zone_name(name='TestZone',
                                                  suffix=self.tld_name)
        LOG.info('Create a zone: %s', zone_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]
        zone_id = zone['id']
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        # Share the zone with the alt credential
        shared_zone = self.share_zone_client.create_zone_share(
            zone['id'], self.alt_rec_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        zone['id'], shared_zone['id'])

        # Share the zone with the demo credential
        shared_zone = self.share_zone_client.create_zone_share(
            zone['id'], self.demo_rec_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        zone['id'], shared_zone['id'])

        zones = self.zones_client.list_zones()[1]['zones']
        zones_ids = [zone['id'] for zone in zones]
        self.assertEqual(
            1, zones_ids.count(zone_id),
            'Failed, ID:{} counted in zones listed:{} must be one'.format(
                zone_id, zones))

    @decorators.attr(type='slow')
    @decorators.idempotent_id('78b77c6c-18cf-11ee-a872-201e8823901f')
    def test_create_recordset_for_zone_shared_with_two_projects(self):
        # Create a zone to share with the alt credential
        zone_name = dns_data_utils.rand_zone_name(name='TestZone',
                                                  suffix=self.tld_name)
        LOG.info('Create a zone: %s', zone_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        # Share the zone with the alt credential
        shared_zone = self.share_zone_client.create_zone_share(
            zone['id'], self.alt_rec_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        zone['id'], shared_zone['id'])

        # Check that the alt user can create a recordset on the shared zone
        recordset_data = dns_data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])
        recordset = self.alt_rec_client.create_recordset(
            zone['id'], recordset_data)[1]
        self.addCleanup(self.wait_recordset_delete, self.alt_rec_client,
            zone['id'], recordset['id'], ignore_errors=lib_exc.NotFound)

        # Share the zone with the demo credential
        shared_zone = self.share_zone_client.create_zone_share(
            zone['id'], self.demo_rec_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        zone['id'], shared_zone['id'])

        # Check that the demo user can create a recordset on the shared zone
        recordset_data = dns_data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])
        recordset = self.demo_rec_client.create_recordset(
            zone['id'], recordset_data)[1]
        self.addCleanup(self.wait_recordset_delete, self.demo_rec_client,
            zone['id'], recordset['id'], ignore_errors=lib_exc.NotFound)


class SharedZonesTestNegative(base.BaseDnsV2Test):
    credentials = ['primary', 'admin', 'system_admin', 'alt',
                   ['demo', 'member']]

    @classmethod
    def setup_clients(cls):
        super(SharedZonesTestNegative, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
            cls.adm_shr_client = cls.os_system_admin.dns_v2.SharedZonesClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
            cls.adm_shr_client = cls.os_admin.dns_v2.SharedZonesClient()
        cls.share_zone_client = cls.os_primary.dns_v2.SharedZonesClient()
        cls.alt_export_client = cls.os_alt.dns_v2.ZoneExportsClient()
        cls.primary_export_client = cls.os_primary.dns_v2.ZoneExportsClient()
        cls.alt_zone_client = cls.os_alt.dns_v2.ZonesClient()
        cls.primary_import_client = cls.os_primary.dns_v2.ZoneImportsClient()
        cls.alt_import_client = cls.os_alt.dns_v2.ZoneImportsClient()
        cls.prm_transfer_client = cls.os_primary.dns_v2.TransferRequestClient()
        cls.alt_transfer_client = cls.os_alt.dns_v2.TransferRequestClient()

    @classmethod
    def resource_setup(cls):
        super(SharedZonesTestNegative, cls).resource_setup()
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
        super(SharedZonesTestNegative, cls).resource_cleanup()

    def _create_shared_zone(self, zone_name):
        # Primary tenant creates zone and shares it with Alt tenant
        zone_name = dns_data_utils.rand_zone_name(
            name=zone_name, suffix=self.tld_name)
        LOG.info('Create a zone: %s', zone_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)
        shared_zone = self.share_zone_client.create_zone_share(
            zone['id'], self.alt_export_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        zone['id'], shared_zone['id'])
        return zone, shared_zone

    @decorators.attr(type='slow')
    @decorators.idempotent_id('1d2c91c2-c328-11ed-a033-201e8823901f')
    def test_alt_create_export_for_shared_zone(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_create_export_for_shared_zone')[0]
        self.assertRaises(
            lib_exc.Forbidden,
            self.alt_export_client.create_zone_export, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('1e74410c-c32c-11ed-a033-201e8823901f')
    def test_alt_list_shared_zone_exports(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_list_shared_zone_exports')[0]

        # Primary creates zone export
        zone_export = self.primary_export_client.create_zone_export(
            zone['id'])[1]
        self.addCleanup(
            self.primary_export_client.delete_zone_export, zone_export['id'])
        waiters.wait_for_zone_export_status(
            self.primary_export_client, zone_export['id'], const.COMPLETE)

        # Primary lists zone exports
        prim_zone_exports = self.primary_export_client.list_zone_exports()[1]
        self.assertEqual(1, len(prim_zone_exports['exports']),
                         'Failed, no zone exports listed for a primary tenant')

        # Alt tries to list Primary's zone exports
        alt_zone_exports = self.alt_export_client.list_zone_exports()[1]
        self.assertEqual(
            0, len(alt_zone_exports['exports']),
            'Failed, Alt tenant is expected to receive an '
            'empty list of zone exports')

    @decorators.attr(type='slow')
    @decorators.idempotent_id('cac8ea8e-c33b-11ed-a033-201e8823901f')
    def test_alt_delete_shared_zone_export(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_delete_shared_zone_export')[0]
        self.assertRaises(
            lib_exc.NotFound,
            self.alt_export_client.delete_zone_export, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('962df772-c33d-11ed-a033-201e8823901f')
    def test_alt_fails_to_show_exported_zonefile_for_shared_zone(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_show_exported_zonefile_for_shared_zone')[0]
        self.assertRaises(
            lib_exc.NotFound,
            self.alt_export_client.show_exported_zonefile, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('089136f2-c3e4-11ed-a102-201e8823901f')
    def test_alt_shows_shared_zones_nameservers(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_shows_shared_zones_nameservers')[0]
        self.assertRaises(
            lib_exc.Forbidden,
            self.alt_zone_client.show_zone_nameservers, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('6376d4ca-c3f6-11ed-a102-201e8823901f')
    def test_alt_transfers_shared_zone(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_transfers_shared_zone')[0]
        # Alt creates a zone transfer_request
        self.assertRaises(
            lib_exc.Forbidden,
            self.alt_transfer_client.create_transfer_request, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('80ffbd8a-c3f7-11ed-a102-201e8823901f')
    def test_alt_show_delete_transfers_of_shared_zone(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_show_delete_transfers_of_shared_zone')[0]

        # Primary user creates a zone transfer_request
        transfer_request = self.prm_transfer_client.create_transfer_request(
            zone['id'])[1]
        self.addCleanup(
            self.prm_transfer_client.delete_transfer_request,
            transfer_request['id'])
        self.assertEqual('ACTIVE', transfer_request['status'])

        # Alt shows a zone transfer_request
        self.assertRaises(
            lib_exc.NotFound,
            self.alt_transfer_client.show_transfer_request, zone['id'])

        # Alt deletes a zone transfer_request
        self.assertRaises(
            lib_exc.NotFound,
            self.alt_transfer_client.delete_transfer_request, zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('1da0ff64-c3f8-11ed-a102-201e8823901f')
    def test_alt_lists_transfers_of_shared_zone(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_lists_transfers_of_shared_zone')[0]

        # Primary user creates a zone transfer_request
        transfer = self.prm_transfer_client.create_transfer_request(
            zone['id'])[1]
        self.addCleanup(self.prm_transfer_client.delete_transfer_request,
                        transfer['id'])
        self.assertEqual('ACTIVE', transfer['status'])
        transfer = self.prm_transfer_client.list_transfer_requests()[1]
        self.assertEqual(
            1, len(transfer['transfer_requests']),
            'Failed, there is no transfer request listed for a primary user')

        # Alt user lists shared zone transfer requests
        transfer = self.alt_transfer_client.list_transfer_requests()[1]
        self.assertEqual(
            0, len(transfer['transfer_requests']),
            'Failed, transfer request list should be empty for for Alt user')

    @decorators.attr(type='slow')
    @decorators.idempotent_id('1702c1d6-c643-11ed-8d86-201e8823901f')
    def test_alt_abandon_shared_zone(self):
        # Primary creates Zone and shares it with Alt
        zone = self._create_shared_zone(
            'test_alt_lists_transfers_of_shared_zone')[0]
        self.assertRaises(
            lib_exc.Forbidden, self.alt_zone_client.abandon_zone,
            zone['id'])
