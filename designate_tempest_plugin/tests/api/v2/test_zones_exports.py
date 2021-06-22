# Copyright 2016 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base

LOG = logging.getLogger(__name__)


class BaseZoneExportsTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                     'status', 'location']


class ZonesExportTest(BaseZoneExportsTest):
    credentials = ['primary', 'admin', 'alt']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesExportTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesExportTest, cls).setup_clients()

        cls.zone_client = cls.os_primary.zones_client
        cls.alt_zone_client = cls.os_alt.zones_client
        cls.client = cls.os_primary.zone_exports_client
        cls.alt_client = cls.os_alt.zone_exports_client
        cls.admin_client = cls.os_admin.zone_exports_client

    @decorators.idempotent_id('2dd8a9a0-98a2-4bf6-bb51-286583b30f40')
    def test_create_zone_export(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone export')
        _, zone_export = self.client.create_zone_export(zone['id'])
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])

        LOG.info('Ensure we respond with PENDING')
        self.assertEqual('PENDING', zone_export['status'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('2d29a2a9-1941-4b7e-9d8a-ad6c2140ea68')
    def test_show_zone_export(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone export')
        resp, zone_export = self.client.create_zone_export(zone['id'])
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])

        LOG.info('Re-Fetch the zone export')
        _, body = self.client.show_zone_export(zone_export['id'])

        LOG.info('Ensure the fetched response matches the zone export')
        self.assertExpected(zone_export, body, self.excluded_keys)

    @decorators.idempotent_id('fb04507c-9600-11eb-b1cd-74e5f9e2a801')
    def test_show_zone_export_impersonate_another_project(self):
        LOG.info('Create a zone')
        zone = self.zone_client.create_zone()[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a zone export using primary client')
        resp, zone_export = self.client.create_zone_export(zone['id'])
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])

        LOG.info('Impersonate "primary" client, to show created zone exports')
        body = self.admin_client.show_zone_export(uuid=None, headers={
            'x-auth-sudo-project-id': zone['project_id']})[1]['exports']
        listed_export_ids = [item['id'] for item in body]

        LOG.info('Ensure that the fetched response, contains the ID '
                 'for a zone export created by primary client.')
        self.assertIn(
            zone_export['id'], listed_export_ids,
            'Failed, expected ID:{} was not found in listed export zones '
            'for a primary client: {}'.format(
                zone_export['id'], listed_export_ids))

    @decorators.idempotent_id('97234f00-8bcb-43f8-84dd-874f8bc4a80e')
    def test_delete_zone_export(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info('Create a zone export')
        _, zone_export = self.client.create_zone_export(zone['id'])

        LOG.info('Delete the zone export')
        _, body = self.client.delete_zone_export(zone_export['id'])

        LOG.info('Ensure the zone export has been successfully deleted')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.show_zone_export(zone_export['id']))

    @decorators.idempotent_id('476bfdfe-58c8-46e2-b376-8403c0fff440')
    def test_list_zone_exports(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        _, export = self.client.create_zone_export(zone['id'])
        self.addCleanup(self.client.delete_zone_export, export['id'])

        LOG.info('List zone exports')
        _, body = self.client.list_zone_exports()

        self.assertGreater(len(body['exports']), 0)

    @decorators.idempotent_id('f34e7f34-9613-11eb-b1cd-74e5f9e2a801')
    def test_list_zone_exports_all_projects(self):
        LOG.info('Create a primary zone and its export')
        primary_zone = self.zone_client.create_zone()[1]
        self.addCleanup(
            self.wait_zone_delete, self.zone_client, primary_zone['id'])
        primary_export = self.client.create_zone_export(primary_zone['id'])[1]
        self.addCleanup(self.client.delete_zone_export, primary_export['id'])

        LOG.info('Create an alt zone and its export')
        alt_zone = self.alt_zone_client.create_zone()[1]
        self.addCleanup(
            self.wait_zone_delete, self.alt_zone_client, alt_zone['id'])
        alt_export = self.alt_client.create_zone_export(alt_zone['id'])[1]
        self.addCleanup(self.alt_client.delete_zone_export, alt_export['id'])

        LOG.info('As admin user list zone exports for all projects')
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        listed_exports_ids = [
            item['id'] for item in self.admin_client.list_zone_exports(
                headers={'x-auth-all-projects': True},
                params={'limit': 1000})[1]['exports']]

        LOG.info('Make sure that all previously created zone '
                 'export IDs are listed')
        for id in [primary_export['id'], alt_export['id']]:
            self.assertIn(
                id, listed_exports_ids,
                'Failed, expected ID:{} was not found in '
                'listed IDs:{}'.format(id, listed_exports_ids))

    @decorators.idempotent_id('e4a11a14-9aaa-11eb-be59-74e5f9e2a801')
    def test_list_zone_exports_filter_results(self):

        LOG.info('Create a primary zone and its export')
        primary_zone = self.zone_client.create_zone()[1]
        self.addCleanup(
            self.wait_zone_delete, self.zone_client, primary_zone['id'])
        primary_export = self.client.create_zone_export(primary_zone['id'])[1]
        self.addCleanup(self.client.delete_zone_export, primary_export['id'])

        LOG.info('Create an alt zone, its export and delete it')
        alt_zone = self.alt_zone_client.create_zone()[1]
        self.addCleanup(
            self.wait_zone_delete, self.alt_zone_client, alt_zone['id'])
        alt_export = self.alt_client.create_zone_export(alt_zone['id'])[1]
        self.alt_client.delete_zone_export(alt_export['id'])
        LOG.info('Ensure the zone export has been successfully deleted')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.alt_client.show_zone_export(alt_export['id']))

        LOG.info('Filter out "export zones" in status:ZAHLABUT,'
                 ' expected: empty list')
        self.assertEqual(
            [], self.admin_client.list_zone_exports(
                headers={'x-auth-all-projects': True},
                params={'status': 'ZAHLABUT'})[1]['exports'],
            'Failed, filtered result is expected to be empty.')

        LOG.info('Filter out "export zones" with message:ZABABUN,'
                 ' expected: empty list')
        self.assertEqual(
            [], self.admin_client.list_zone_exports(
                headers={'x-auth-all-projects': True},
                params={'message': 'ZABABUN'})[1]['exports'],
            'Failed, filtered result is expected to be empty.')

        LOG.info('Filter out "export zones" that have been created for '
                 'a primary zone. Expected: single zone export is listed')
        self.assertEqual(
            1, len(self.admin_client.list_zone_exports(
                headers={'x-auth-all-projects': True},
                params={'zone_id': primary_zone['id']})[1]['exports']),
            'Failed, filtered result should contain a single zone '
            '(primary zone export)')

        LOG.info('Filter out "export zones" that have been created for '
                 'an alt zone expected: empty list (it was deleted)')
        self.assertEqual(
            [], self.admin_client.list_zone_exports(
                headers={'x-auth-all-projects': True},
                params={'zone_id': alt_zone['id']})[1]['exports'],
            'Failed, filtered result should be empty.')


class ZonesExportTestNegative(BaseZoneExportsTest):
    credentials = ['primary', 'alt']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesExportTestNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesExportTestNegative, cls).setup_clients()

        cls.zone_client = cls.os_primary.zones_client
        cls.client = cls.os_primary.zone_exports_client
        cls.alt_client = cls.os_alt.zone_exports_client

    @decorators.idempotent_id('76ab8ec4-95fd-11eb-b1cd-74e5f9e2a801')
    def test_create_zone_export_using_invalid_zone_id(self):
        self.assertRaises(
            lib_exc.NotFound, self.client.create_zone_export,
            'e35bc796-9841-11eb-898b-74e5f9e2a801')

    @decorators.idempotent_id('943dad4a-9617-11eb-b1cd-74e5f9e2a801')
    def test_export_not_your_zone(self):
        LOG.info('Create a primary zone.')
        primary_zone = self.zone_client.create_zone()[1]
        self.addCleanup(
            self.wait_zone_delete, self.zone_client, primary_zone['id'])

        LOG.info('Make sure that "404 NotFound" status code is raised.')
        self.assertRaises(
            lib_exc.NotFound, self.alt_client.create_zone_export,
            primary_zone['id'])

    @decorators.idempotent_id('518dc308-9604-11eb-b1cd-74e5f9e2a801')
    def test_create_zone_export_using_deleted_zone(self):
        LOG.info('Create a zone')
        zone = self.zone_client.create_zone()[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        LOG.info("Delete the zone and wait till it's done.")
        self.zone_client.delete_zone(zone['id'])[1]
        self.wait_zone_delete(self.zone_client, zone['id'])

        LOG.info('Ensure we respond with NotFound exception')
        self.assertRaises(
            lib_exc.NotFound, self.client.create_zone_export, zone['id'])
