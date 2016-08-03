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
from tempest import config
from tempest import test
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
import ddt

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils

LOG = logging.getLogger(__name__)

CONF = config.CONF


class BaseRecordsetsTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                     'type']

    @classmethod
    def resource_setup(cls):
        super(BaseRecordsetsTest, cls).resource_setup()

        # All the recordset tests need a zone, create one to share
        LOG.info('Create a zone')
        _, cls.zone = cls.zone_client.create_zone()

    @classmethod
    def resource_cleanup(cls):
        super(BaseRecordsetsTest, cls).resource_cleanup()

        cls.zone_client.delete_zone(
            cls.zone['id'], ignore_errors=lib_exc.NotFound)


@ddt.ddt
class RecordsetsTest(BaseRecordsetsTest):
    @classmethod
    def setup_clients(cls):
        super(RecordsetsTest, cls).setup_clients()

        cls.client = cls.os.recordset_client
        cls.zone_client = cls.os.zones_client

    @test.attr(type='smoke')
    @decorators.idempotent_id('631d74fd-6909-4684-a61b-5c4d2f92c3e7')
    def test_create_recordset(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])

        LOG.info('Create a Recordset')
        resp, body = self.client.create_recordset(
            self.zone['id'], recordset_data)

        LOG.info('Ensure we respond with PENDING')
        self.assertEqual('PENDING', body['status'])

    @decorators.idempotent_id('5964f730-5546-46e6-9105-5030e9c492b2')
    def test_list_recordsets(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])

        LOG.info('Create a Recordset')
        resp, body = self.client.create_recordset(
            self.zone['id'], recordset_data)

        LOG.info('List zone recordsets')
        _, body = self.client.list_recordset(self.zone['id'])

        self.assertGreater(len(body), 0)

    @decorators.idempotent_id('84c13cb2-9020-4c1e-aeb0-c348d9a70caa')
    def test_show_recordsets(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])

        LOG.info('Create a Recordset')
        resp, body = self.client.create_recordset(
            self.zone['id'], recordset_data)

        LOG.info('Re-Fetch the Recordset')
        _, record = self.client.show_recordset(self.zone['id'], body['id'])

        LOG.info('Ensure the fetched response matches the expected one')
        self.assertExpected(body, record, self.excluded_keys)

    @decorators.idempotent_id('855399c1-8806-4ae5-aa31-cb8a6f35e218')
    def test_delete_recordset(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])

        LOG.info('Create a Recordset')
        _, record = self.client.create_recordset(
            self.zone['id'], recordset_data)

        LOG.info('Delete a Recordset')
        _, body = self.client.delete_recordset(self.zone['id'], record['id'])

        LOG.info('Ensure successful deletion of Recordset')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.client.show_recordset(self.zone['id'], record['id']))

    @decorators.idempotent_id('8d41c85f-09f9-48be-a202-92d1bdf5c796')
    def test_update_recordset(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])

        LOG.info('Create a recordset')
        _, record = self.client.create_recordset(
            self.zone['id'], recordset_data)

        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'], name=record['name'])

        LOG.info('Update the recordset')
        _, update = self.client.update_recordset(self.zone['id'],
            record['id'], recordset_data)

        self.assertEqual(record['name'], update['name'])
        self.assertNotEqual(record['records'], update['records'])

    @decorators.idempotent_id('60904cc5-148b-4e3b-a0c6-35656dc8d44c')
    def test_update_recordset_one_field(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])

        LOG.info('Create a recordset')
        _, record = self.client.create_recordset(
            self.zone['id'], recordset_data)

        recordset_data = {
            'ttl': data_utils.rand_ttl(start=record['ttl'] + 1)
        }

        LOG.info('Update the recordset')
        _, update = self.client.update_recordset(self.zone['id'],
            record['id'], recordset_data)

        self.assertEqual(record['name'], update['name'])
        self.assertEqual(record['records'], update['records'])
        self.assertEqual(record['description'], update['description'])
        self.assertNotEqual(record['ttl'], update['ttl'])


@ddt.ddt
class RecordsetsNegativeTest(BaseRecordsetsTest):
    @classmethod
    def setup_clients(cls):
        super(RecordsetsNegativeTest, cls).setup_clients()

        cls.client = cls.os.recordset_client
        cls.zone_client = cls.os.zones_client

    @decorators.idempotent_id('631d74fd-6909-4684-a61b-5c4d2f92c3e7')
    @ddt.file_data("recordset_data_invalid.json")
    def test_create_recordset_invalid(self, name, type, records):
        if name is not None:
            recordset_name = name + "." + self.zone['name']

        else:
            recordset_name = self.zone['name']

        recordset_data = {
            'name': recordset_name,
            'type': type,
            'records': records,
        }

        LOG.info('Attempt to create a invalid Recordset')
        self.assertRaises(lib_exc.BadRequest,
            lambda: self.client.create_recordset(
                self.zone['id'], recordset_data))


class RootRecordsetsTests(BaseRecordsetsTest):

    @classmethod
    def setup_clients(cls):
        super(RootRecordsetsTests, cls).setup_clients()

        cls.client = cls.os.recordset_client
        cls.zone_client = cls.os.zones_client

    @classmethod
    def skip_checks(cls):
        super(RootRecordsetsTests, cls).skip_checks()

        if not CONF.dns_feature_enabled.api_v2_root_recordsets:
            skip_msg = ("%s skipped as designate V2 recordsets API is not "
                        "available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @decorators.idempotent_id('48a081b9-4474-4da0-9b1a-6359a80456ce')
    def test_list_zones_recordsets(self):
        LOG.info('List recordsets')
        _, body = self.client.list_zones_recordsets()

        self.assertGreater(len(body['recordsets']), 0)

    @decorators.idempotent_id('a8e41020-65be-453b-a8c1-2497d539c345')
    def test_list_filter_zones_recordsets(self):
        recordset_data = {
            "name": self.zone['name'],
            "description": "This is an example record set.",
            "type": "A",
            "ttl": 3600,
            "records": [
                "10.1.0.2"
            ]
        }

        LOG.info('Create a Recordset')
        resp, zone_recordset = self.client.create_recordset(
            self.zone['id'], recordset_data)

        LOG.info('Create another zone')
        _, zone2 = self.zone_client.create_zone()
        self.addCleanup(self.zone_client.delete_zone, zone2['id'])

        LOG.info('List recordsets')
        _, body = self.client.list_zones_recordsets(params={"data": "10.1.*"})

        recordsets = body['recordsets']

        self.assertEqual(zone_recordset['id'], recordsets[0]['id'])
