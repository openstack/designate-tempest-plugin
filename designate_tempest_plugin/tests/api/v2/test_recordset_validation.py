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
from oslo_log import log as logging

from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils


CONF = config.CONF
LOG = logging.getLogger(__name__)
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
INVALID_TXT_DATASET = {
    "trailing_slash": {"data": "\\"},
    "trailing_double_slash": {"data": "\\\\"},
    "trailing_slash_after_text": {"data": "testtext\\"}}
VALID_TXT_DATASET = {
    "slash_with_one_trailing_space": {"data": "\"\\ \""},
    "slash_with_many_trailing_space": {"data": "\"\\    \""},
    "text_with_slash_and_trailing_space": {"data": "\"the txts    \""}}
INVALID_MX_DATASET = {
    "empty_preference": {"pref": ""},
    "minus_zero_preference": {"pref": "-0"},
    "minus_one_preference": {"pref": "-1"}}
INVALID_SSHFP_DATASET = {
    "minus_zero_algorithm": {"algo": "-0", "finger": None},
    "minus_zero_fingerprint": {"algo": None, "finger": "-0"},
    "minus_one_algorithm": {"algo": "-1", "finger": None},
    "minus_one_fingerprint": {"algo": None, "finger": "-1"}}


class RecordsetValidationTest(base.BaseDnsV2Test):

    credentials = ["admin", "primary"]

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

        cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()

    @property
    def zone(self):
        if self._zone is None:
            tld_name = dns_data_utils.rand_zone_name(
                name="recordsetvalidation")
            self.class_tld = self.admin_tld_client.create_tld(
                tld_name=tld_name[:-1])
            self.addCleanup(
                self.admin_tld_client.delete_tld, self.class_tld[1]['id'])
            zone_name = dns_data_utils.rand_zone_name(name="TestZone",
                                                  suffix=f'.{tld_name}')
            zone_data = dns_data_utils.rand_zone_data(name=zone_name)
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
    def test_create_invalid(self):
        for rtype in RECORDSETS_DATASET:
            data = ["b0rk"]
            for i in data:
                model = dns_data_utils.make_rand_recordset(
                    self.zone['name'], rtype)
                model['data'] = i
                self.assertRaisesDns(
                    exceptions.BadRequest, 'invalid_object', 400,
                    self.recordset_client.create_recordset,
                    self.zone['id'], model
                )

    @decorators.idempotent_id('1164c826-dceb-4557-9a22-7d65c4a4f5f4')
    def test_update_invalid(self):
        for rtype in RECORDSETS_DATASET:
            data = ["b0rk"]
            post_model = dns_data_utils.make_rand_recordset(
                self.zone['name'], rtype)
            recordset = self.create_recordset(post_model)
            for i in data:
                model = dns_data_utils.make_rand_recordset(
                    self.zone['name'], rtype)
                model['data'] = i
                self.assertRaisesDns(
                    exceptions.BadRequest, 'invalid_object', 400,
                    self.recordset_client.update_recordset,
                    self.zone['id'], recordset['id'], model
                )

    @decorators.idempotent_id('61da1015-291f-43d1-a1a8-345cff12d201')
    def test_cannot_create_wildcard_NS_recordset(self):
        model = dns_data_utils.wildcard_ns_recordset(self.zone['name'])
        self.assertRaisesDns(
            exceptions.BadRequest, 'invalid_object', 400,
            self.recordset_client.create_recordset, self.zone['id'], model
        )

    @decorators.idempotent_id('92f681aa-d953-4d18-b12e-81a9149ccfd9')
    def test_cname_recordsets_cannot_have_more_than_one_record(self):
        post_model = dns_data_utils.rand_cname_recordset(
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
    def test_cannot_create_TXT_with(self):
        for key, data in INVALID_TXT_DATASET.items():
            LOG.info('Tested INVALID_TXT_DATASET: {}'.format(key))
            post_model = dns_data_utils.rand_txt_recordset(
                self.zone['name'], data['data'])
            self.assertRaisesDns(
                exceptions.BadRequest, 'invalid_object', 400,
                self.recordset_client.create_recordset,
                self.zone['id'], post_model
            )

    @decorators.idempotent_id('03e4f811-0c37-4ce2-8b16-662c824f8f18')
    def test_create_TXT_with(self):
        for key, data in VALID_TXT_DATASET.items():
            LOG.info('Tested VALID_TXT_DATASET: {}'.format(key))
        post_model = dns_data_utils.rand_txt_recordset(
            self.zone['name'], data['data'])
        recordset = self.create_recordset(post_model)

        waiters.wait_for_recordset_status(
            self.recordset_client, self.zone['id'], recordset['id'], 'ACTIVE')

    @decorators.idempotent_id('775b3db5-ec60-4dd7-85d2-f05a9c544978')
    def test_create_SPF_with(self):
        for key, data in VALID_TXT_DATASET.items():
            LOG.info('Tested VALID_TXT_DATASET: {}'.format(key))
            post_model = dns_data_utils.rand_spf_recordset(
                self.zone['name'], data['data'])
            recordset = self.create_recordset(post_model)

            waiters.wait_for_recordset_status(
                self.recordset_client, self.zone['id'],
                recordset['id'], 'ACTIVE')

    @decorators.idempotent_id('7fa7783f-1624-4122-bfb2-6cfbf7a5b49b')
    def test_cannot_create_MX_with(self):
        for key, pref in INVALID_MX_DATASET.items():
            LOG.info('Tested INVALID_MX_DATASET: {}'.format(key))

            post_model = dns_data_utils.rand_mx_recordset(
                self.zone['name'], pref=pref['pref']
            )

            self.assertRaisesDns(
                exceptions.BadRequest, 'invalid_object', 400,
                self.recordset_client.create_recordset,
                self.zone['id'], post_model,
            )

    @decorators.idempotent_id('3016f998-4e4a-4712-b15a-4e8dfbc5a60b')
    def test_cannot_create_SSHFP_with(self):
        for key, data in INVALID_SSHFP_DATASET.items():
            LOG.info('Tested INVALID_SSHFP_DATASET: {}'.format(key))

            post_model = dns_data_utils.rand_sshfp_recordset(
                zone_name=self.zone['name'],
                algorithm_number=data['algo'],
                fingerprint_type=data['finger'],
            )

            self.assertRaisesDns(
                exceptions.BadRequest, 'invalid_object', 400,
                self.recordset_client.create_recordset,
                self.zone['id'], post_model,
            )
