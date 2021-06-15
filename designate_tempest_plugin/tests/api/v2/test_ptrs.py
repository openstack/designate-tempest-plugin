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
from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base
import tempest.test

LOG = logging.getLogger(__name__)

CONF = config.CONF


class BasePtrTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                     'status', 'action']


class DesignatePtrRecord(BasePtrTest, tempest.test.BaseTestCase):
    credentials = ['primary']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(DesignatePtrRecord, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(DesignatePtrRecord, cls).setup_clients()
        cls.primary_ptr_client = cls.os_primary.ptr_client
        cls.primary_floating_ip_client = cls.os_primary.floating_ips_client

    def _set_ptr(self):
        fip = self.primary_floating_ip_client.create_floatingip(
            floating_network_id=CONF.network.public_network_id)['floatingip']
        fip_id = fip['id']
        self.addCleanup(self.primary_floating_ip_client.delete_floatingip,
                        fip_id)
        ptr = self.primary_ptr_client.set_ptr_record(fip_id)
        self.addCleanup(self.primary_ptr_client.unset_ptr_record, fip_id)
        self.assertEqual('CREATE', ptr['action'])
        self.assertEqual('PENDING', ptr['status'])
        return fip_id, ptr

    @decorators.idempotent_id('2fb9d6ea-871d-11eb-9f9a-74e5f9e2a801')
    def test_set_floatingip_ptr(self):
        self._set_ptr()

    @decorators.idempotent_id('9179325a-87d0-11eb-9f9a-74e5f9e2a801')
    def test_show_floatingip_ptr(self):
        fip_id, ptr = self._set_ptr()
        show_ptr = self.primary_ptr_client.show_ptr_record(
            floatingip_id=fip_id)
        self.assertExpected(ptr, show_ptr, self.excluded_keys)

    @decorators.idempotent_id('9187a9c6-87d4-11eb-9f9a-74e5f9e2a801')
    def test_list_floatingip_ptr_records(self):
        number_of_ptr_records = 3
        created_ptr_ids = []
        for _ in range(number_of_ptr_records):
            fip_id, ptr = self._set_ptr()
            created_ptr_ids.append(ptr['id'])
        received_ptr_ids = sorted(
            [item['id'] for item in
             self.primary_ptr_client.list_ptr_records()])
        self.assertEqual(
            sorted(created_ptr_ids), received_ptr_ids,
            'Failed - received PTR IDs: {} are not as'
            ' expected: {}'.format(created_ptr_ids, received_ptr_ids))

    @decorators.idempotent_id('499b5a7e-87e1-11eb-b412-74e5f9e2a801')
    def test_unset_floatingip_ptr(self):
        fip_id, ptr = self._set_ptr()
        self.primary_ptr_client.unset_ptr_record(fip_id)


class DesignatePtrRecordNegative(BasePtrTest, tempest.test.BaseTestCase):
    credentials = ['primary']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(DesignatePtrRecordNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(DesignatePtrRecordNegative, cls).setup_clients()
        cls.primary_ptr_client = cls.os_primary.ptr_client
        cls.primary_floating_ip_client = cls.os_primary.floating_ips_client

    def _set_ptr(self, ptr_name=None, ttl=None, description=None,
                 headers=None):
        fip = self.primary_floating_ip_client.create_floatingip(
            floating_network_id=CONF.network.public_network_id)[
            'floatingip']
        fip_id = fip['id']
        self.addCleanup(self.primary_floating_ip_client.delete_floatingip,
                        fip_id)
        ptr = self.primary_ptr_client.set_ptr_record(
            fip_id, ptr_name=ptr_name, ttl=ttl, description=description,
            headers=headers)
        self.addCleanup(self.primary_ptr_client.unset_ptr_record, fip_id)
        self.assertEqual('CREATE', ptr['action'])
        self.assertEqual('PENDING', ptr['status'])
        return fip_id, ptr

    def test_set_floatingip_ptr_invalid_ttl(self):
        LOG.info('Try to set PTR record using invalid TTL value')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self._set_ptr(ttl=-10)
