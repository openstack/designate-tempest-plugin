"""
Copyright 2016 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import ddt
from tempest.lib import exceptions
from tempest.lib import decorators

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils


RECORDSETS_DATASET = [
    'A',
    'AAAA',
    'CNAME',
    'MX',
    'SPF',
    'SRV',
    'SSHFP',
    'TXT',
]


@ddt.ddt
class RecordsetValidationTest(base.BaseDnsV2Test):

    def setUp(self):
        super(RecordsetValidationTest, self).setUp()
        self._zone = None

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(RecordsetValidationTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(RecordsetValidationTest, cls).setup_clients()

        cls.recordset_client = cls.os_primary.recordset_client
        cls.zones_client = cls.os_primary.zones_client

    @property
    def zone(self):
        if self._zone is None:
            zone_data = data_utils.rand_zone_data()
            resp, body = self.zones_client.create_zone(**zone_data)
            self._zone = body
            self.addCleanup(self.wait_zone_delete,
                            self.zones_client,
                            body['id'])
        return self._zone

    def create_recordset(self, data):
        resp, body = self.recordset_client.create_recordset(
            self.zone['id'], data)

        return body

    @decorators.idempotent_id('c5ef87e2-cb79-4758-b968-18eef2c251df')
    @ddt.data(*RECORDSETS_DATASET)
    def test_create_invalid(self, rtype):
        data = ["b0rk"]

        for i in data:
            model = data_utils.make_rand_recordset(self.zone['name'], rtype)
            model['data'] = i

            self.assertRaisesDns(
                exceptions.BadRequest, 'invalid_object', 400,
                self.recordset_client.create_recordset,
                self.zone['id'], model
            )

    @decorators.idempotent_id('1164c826-dceb-4557-9a22-7d65c4a4f5f4')
    @ddt.data(*RECORDSETS_DATASET)
    def test_update_invalid(self, rtype):
        data = ["b0rk"]

        post_model = data_utils.make_rand_recordset(self.zone['name'], rtype)
        recordset = self.create_recordset(post_model)

        for i in data:
            model = data_utils.make_rand_recordset(self.zone['name'], rtype)
            model['data'] = i
            self.assertRaisesDns(
                exceptions.BadRequest, 'invalid_object', 400,
                self.recordset_client.update_recordset,
                self.zone['id'], recordset['id'], model
            )

    @decorators.idempotent_id('61da1015-291f-43d1-a1a8-345cff12d201')
    def test_cannot_create_wildcard_NS_recordset(self):
        model = data_utils.wildcard_ns_recordset(self.zone['name'])
        self.assertRaisesDns(
            exceptions.BadRequest, 'invalid_object', 400,
            self.recordset_client.create_recordset, self.zone['id'], model
        )

    @decorators.idempotent_id('92f681aa-d953-4d18-b12e-81a9149ccfd9')
    def test_cname_recordsets_cannot_have_more_than_one_record(self):
        post_model = data_utils.rand_cname_recordset(
            zone_name=self.zone['name'])

        post_model['records'] = [
            "a.{0}".format(self.zone['name']),
            "b.{0}".format(self.zone['name']),
        ]

        self.assertRaises(
            exceptions.BadRequest,
            self.recordset_client.create_recordset,
            self.zone['id'], post_model
        )

    @decorators.idempotent_id('22a9544b-2382-4ed2-ba12-4dbaedb8e880')
    @ddt.file_data("invalid_txt_dataset.json")
    def test_cannot_create_TXT_with(self, data):
        post_model = data_utils.rand_txt_recordset(self.zone['name'], data)
        self.assertRaisesDns(
            exceptions.BadRequest, 'invalid_object', 400,
            self.recordset_client.create_recordset,
            self.zone['id'], post_model
        )

    @decorators.idempotent_id('03e4f811-0c37-4ce2-8b16-662c824f8f18')
    @ddt.file_data("valid_txt_dataset.json")
    def test_create_TXT_with(self, data):
        post_model = data_utils.rand_txt_recordset(self.zone['name'], data)
        recordset = self.create_recordset(post_model)

        waiters.wait_for_recordset_status(
            self.recordset_client, self.zone['id'], recordset['id'], 'ACTIVE')

    @decorators.idempotent_id('775b3db5-ec60-4dd7-85d2-f05a9c544978')
    @ddt.file_data("valid_txt_dataset.json")
    def test_create_SPF_with(self, data):
        post_model = data_utils.rand_spf_recordset(self.zone['name'], data)
        recordset = self.create_recordset(post_model)

        waiters.wait_for_recordset_status(
            self.recordset_client, self.zone['id'], recordset['id'], 'ACTIVE')

    @decorators.idempotent_id('7fa7783f-1624-4122-bfb2-6cfbf7a5b49b')
    @ddt.file_data("invalid_mx_dataset.json")
    def test_cannot_create_MX_with(self, pref):
        post_model = data_utils.rand_mx_recordset(
            self.zone['name'], pref=pref
        )

        self.assertRaisesDns(
            exceptions.BadRequest, 'invalid_object', 400,
            self.recordset_client.create_recordset,
            self.zone['id'], post_model,
        )

    @decorators.idempotent_id('3016f998-4e4a-4712-b15a-4e8dfbc5a60b')
    @ddt.data("invalid_sshfp_dataset.json")
    def test_cannot_create_SSHFP_with(self, algo=None, finger=None):
        post_model = data_utils.rand_sshfp_recordset(
            zone_name=self.zone['name'],
            algorithm_number=algo,
            fingerprint_type=finger,
        )

        self.assertRaisesDns(
            exceptions.BadRequest, 'invalid_object', 400,
            self.recordset_client.create_recordset,
            self.zone['id'], post_model,
        )
