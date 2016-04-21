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
from tempest import test
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils

LOG = logging.getLogger(__name__)


class BaseRecordsetsTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                     'type']


class RecordsetsTest(BaseRecordsetsTest):
    @classmethod
    def setup_clients(cls):
        super(RecordsetsTest, cls).setup_clients()

        cls.client = cls.os.recordset_client
        cls.zone_client = cls.os.zones_client

    @test.attr(type='smoke')
    @test.idempotent_id('631d74fd-6909-4684-a61b-5c4d2f92c3e7')
    def test_create_recordset(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        LOG.info('Create a Recordset')
        resp, body = self.client.create_recordset(zone['id'], recordset_data)

        LOG.info('Ensure we respond with PENDING')
        self.assertEqual('PENDING', body['status'])

    @test.attr(type='smoke')
    @test.idempotent_id('5964f730-5546-46e6-9105-5030e9c492b2')
    def test_list_recordsets(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        LOG.info('Create a Recordset')
        resp, body = self.client.create_recordset(zone['id'], recordset_data)

        self.assertTrue(len(body) > 0)

    @test.attr(type='smoke')
    @test.idempotent_id('84c13cb2-9020-4c1e-aeb0-c348d9a70caa')
    def test_show_recordsets(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        LOG.info('Create a Recordset')
        resp, body = self.client.create_recordset(zone['id'], recordset_data)

        LOG.info('Re-Fetch the Recordset')
        _, record = self.client.show_recordset(zone['id'], body['id'])

        LOG.info('Ensure the fetched response matches the expected one')
        self.assertExpected(body, record, self.excluded_keys)

    @test.attr(type='smoke')
    @test.idempotent_id('855399c1-8806-4ae5-aa31-cb8a6f35e218')
    def test_delete_recordset(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        LOG.info('Create a Recordset')
        _, record = self.client.create_recordset(zone['id'], recordset_data)

        LOG.info('Delete a Recordset')
        _, body = self.client.delete_recordset(zone['id'], record['id'])

        LOG.info('Ensure successful deletion of Recordset')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.show_recordset(zone['id'], record['id']))

    @test.attr(type='smoke')
    @test.idempotent_id('8d41c85f-09f9-48be-a202-92d1bdf5c796')
    def test_update_recordset(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone['id'])

        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        LOG.info('Create a recordset')
        _, record = self.client.create_recordset(zone['id'], recordset_data)

        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'], name=record['name'])

        LOG.info('Update the recordset')
        _, update = self.client.update_recordset(zone['id'],
            record['id'], recordset_data)

        self.assertEqual(record['name'], update['name'])
        self.assertNotEqual(record['records'], update['records'])
