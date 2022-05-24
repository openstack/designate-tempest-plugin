# Copyright 2016 Rackspace
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

import json
import os

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators

from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests.api.v2.test_zones_exports import \
    BaseZoneExportsTest

CONF = config.CONF
LOG = logging.getLogger(__name__)


class ZonesExportTest(BaseZoneExportsTest):
    credentials = ["primary", "admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(ZonesExportTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ZonesExportTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.ZoneExportsClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.ZoneExportsClient()
        cls.client = cls.os_primary.dns_v2.ZoneExportsClient()
        cls.zones_client = cls.os_primary.dns_v2.ZonesClient()
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()

    def _create_zone_export(self, test_name):
        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name=test_name, suffix=self.tld_name)
        zone = self.zones_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'])

        LOG.info('Create a zone export')
        zone_export = self.client.create_zone_export(
            zone['id'], wait_until=const.COMPLETE)[1]
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])

        return zone, zone_export

    @decorators.idempotent_id('0484c3c4-df57-458e-a6e5-6eb63e0475e0')
    def test_create_zone_export_and_show_exported_zonefile(self):
        zone, zone_export = self._create_zone_export(
            'create_zone_export_and_show_exported_zonefile')

        self.assertEqual(const.PENDING, zone_export['status'])
        self.assertEqual(zone['id'], zone_export['zone_id'])
        self.assertIsNone(zone_export['links'].get('export'))
        self.assertIsNone(zone_export['location'])

        LOG.info('Check the zone export looks good')
        _, zone_export = self.client.show_zone_export(zone_export['id'])

        self.assertEqual(const.COMPLETE, zone_export['status'])
        self.assertEqual(zone['id'], zone_export['zone_id'])
        self.assertIsNotNone(zone_export['links'].get('export'))
        self.assertIsNotNone(zone_export['location'])

        LOG.info('Fetch the exported zonefile')
        _, zonefile = self.client.show_exported_zonefile(zone_export['id'])
        self.assertEqual(zone['name'], zonefile.origin)
        self.assertEqual(zone['ttl'], zonefile.ttl)

    @decorators.idempotent_id('56b8f30e-cd45-4c7a-bc0c-bbf92d7dc697')
    def test_show_exported_zonefile_impersonate_another_project(self):
        zone, zone_export = self._create_zone_export(
            'show_exported_zonefile_impersonate')

        LOG.info('As Admin impersonate "primary" client,'
                 ' to show exported zone file')
        response = self.admin_client.show_exported_zonefile(
            zone_export['id'], headers={
                'x-auth-sudo-project-id': zone['project_id']})[1]
        self.assertEqual(zone['name'], response.origin)
        self.assertEqual(zone['ttl'], response.ttl)

    @decorators.idempotent_id('c2e55514-ff2e-41d9-a3cc-9e78873254c9')
    def test_show_exported_zonefile_all_projects(self):
        zone, zone_export = self._create_zone_export(
            'show_exported_zonefile_all_projects')
        resp_headers, resp_data = self.admin_client.show_exported_zonefile(
            zone_export['id'], headers={
                'x-auth-all-projects': True
            })
        self.assertEqual(zone['name'], resp_data.origin)
        self.assertEqual(zone['ttl'], resp_data.ttl)

    @decorators.idempotent_id('9746b7f2-2df4-448c-8a85-5ab6bf74f1fe')
    def test_show_exported_zonefile_any_mime_type(self):
        zone, zone_export = self._create_zone_export(
            'show_exported_zonefile_any_mime_type')
        resp_headers, resp_data = self.client.show_exported_zonefile(
            zone_export['id'], headers={'Accept': '*/*'})

        LOG.info('Ensure Content-Type: text/dns')
        self.assertIn(
            'text/dns', resp_headers['content-type'],
            "Failed, the expected 'Content-type:text/dns wasn't received.")

        LOG.info('Ensure exported data ia as expected')
        self.assertEqual(zone['name'], resp_data.origin)
        self.assertEqual(zone['ttl'], resp_data.ttl)

    @decorators.idempotent_id('dc7a9dde-d287-4e22-9788-26578f0d3bf0')
    def test_missing_accept_headers(self):
        zone, zone_export = self._create_zone_export(
            'missing_accept_headers')
        resp_headers, resp_data = self.client.show_exported_zonefile(
            zone_export['id'], headers={})
        LOG.info('Ensure Content-Type: text/dns')
        self.assertIn(
            'text/dns', resp_headers['content-type'],
            "Failed, the expected 'Content-type:text/dns wasn't received.")

        LOG.info('Ensure exported data ia as expected')
        self.assertEqual(zone['name'], resp_data.origin)
        self.assertEqual(zone['ttl'], resp_data.ttl)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('d8f444aa-a645-4a03-b366-46836f57dc69')
    def test_all_recordset_types_exist_in_show_zonefile(self):
        recorsets_data_file = os.path.join(
            os.path.dirname(__file__), 'recordset_data.json')

        if not os.path.exists(recorsets_data_file):
            raise self.skipException(
                f"Could not find {recorsets_data_file}")

        file = open(recorsets_data_file, "r")
        load_file = json.loads(file.read())
        file.close()

        LOG.info('Create a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="all_recordset_types_exist", suffix=self.tld_name)
        zone = self.zones_client.create_zone(name=zone_name,
                                             wait_until=const.ACTIVE)[1]
        self.addCleanup(self.wait_zone_delete, self.zones_client, zone['id'])

        created_records = []
        for record_data in load_file.values():
            recordset_data = {
                'name': f"{record_data['name']}.{zone['name']}",
                'type': record_data['type'],
                'records': record_data['records'],
            }
            try:
                LOG.info('Create a Recordset')
                recordset = self.recordset_client.create_recordset(
                    zone['id'], recordset_data)[1]
                self.addCleanup(self.wait_recordset_delete,
                                self.recordset_client, zone['id'],
                                recordset['id'])
                created_records.append(recordset['records'])
                waiters.wait_for_recordset_status(self.recordset_client,
                                                  zone['id'], recordset['id'],
                                                  const.ACTIVE)
            except Exception as err:
                LOG.warning(f"Record of type {recordset['type']} could not be"
                            f" created and failed with error: {err}")

        LOG.info('Create a zone export')
        zone_export = self.client.create_zone_export(
            zone['id'], wait_until=const.COMPLETE)[1]
        self.addCleanup(self.client.delete_zone_export, zone_export['id'])

        LOG.info('Show exported zonefile')
        created_zonefile = self.client.show_exported_zonefile(
            zone_export['id'])[1]

        file_records = [item.data for item in created_zonefile.records]
        for record in created_records:
            for r in record:
                self.assertIn(r, file_records,
                            f"Failed, missing record: {r} in zone file")
