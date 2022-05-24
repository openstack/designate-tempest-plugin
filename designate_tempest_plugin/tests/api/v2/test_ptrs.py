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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
import testtools

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils

import tempest.test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BasePtrTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'version', 'links',
                     'status', 'action']

    @classmethod
    def setup_clients(cls):
        super(BasePtrTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(BasePtrTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name='BasePtrTest')
        cls.tld_name = tld_name[:-1]
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(BasePtrTest, cls).resource_cleanup()


class DesignatePtrRecord(BasePtrTest, tempest.test.BaseTestCase):

    credentials = ['primary', 'admin', 'system_admin']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(DesignatePtrRecord, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(DesignatePtrRecord, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_ptr_client = cls.os_system_admin.dns_v2.PtrClient()
        else:
            cls.admin_ptr_client = cls.os_admin.dns_v2.PtrClient()
        cls.primary_ptr_client = cls.os_primary.dns_v2.PtrClient()
        cls.primary_floating_ip_client = cls.os_primary.floating_ips_client

    @classmethod
    def resource_setup(cls):
        super(DesignatePtrRecord, cls).resource_setup()

        # The 'arpa' TLD is a special case as the negative test class also
        # needs to use this space. To stop test class concurrency conflicts,
        # let each class manage different TLDs for the reverse namespace.
        cls.arpa_tld = cls.admin_tld_client.create_tld(tld_name='arpa')

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.arpa_tld[1]['id'])
        super(DesignatePtrRecord, cls).resource_cleanup()

    def _set_ptr(self, ptr_name=None, ttl=None, description=None,
                 headers=None, tld=None, fip_id=None):
        if not tld:
            tld = self.tld_name
        if not fip_id:
            fip = self.primary_floating_ip_client.create_floatingip(
                floating_network_id=CONF.network.public_network_id)[
                'floatingip']
            fip_id = fip['id']
            self.addCleanup(
                self.primary_floating_ip_client.delete_floatingip, fip_id)
        ptr = self.primary_ptr_client.set_ptr_record(
            fip_id, ptr_name=ptr_name, ttl=ttl, description=description,
            headers=headers, tld=tld)
        self.addCleanup(self.unset_ptr, self.primary_ptr_client, fip_id)

        self.assertEqual('CREATE', ptr['action'])
        self.assertEqual('PENDING', ptr['status'])
        waiters.wait_for_ptr_status(
            self.primary_ptr_client, fip_id=fip_id, status=const.ACTIVE)
        return fip_id, ptr

    def _unset_ptr(self, fip_id):
        self.primary_ptr_client.unset_ptr_record(fip_id)
        waiters.wait_for_ptr_status(
            self.primary_ptr_client, fip_id=fip_id, status=const.INACTIVE)

    @decorators.idempotent_id('2fb9d6ea-871d-11eb-9f9a-74e5f9e2a801')
    def test_set_floatingip_ptr(self):
        self._set_ptr()

    @decorators.idempotent_id('9179325a-87d0-11eb-9f9a-74e5f9e2a801')
    def test_show_floatingip_ptr(self):
        fip_id, ptr = self._set_ptr()
        show_ptr = self.primary_ptr_client.show_ptr_record(
            floatingip_id=fip_id)
        self.assertExpected(ptr, show_ptr, self.excluded_keys)

    @decorators.idempotent_id('d3128a92-e3bd-11eb-a097-74e5f9e2a801')
    def test_show_floatingip_ptr_impersonate_another_project(self):
        fip_id, ptr = self._set_ptr()

        LOG.info('As Admin user, show PTR record created by Primary'
                 ' user by including "x-auth-sudo-project-id" HTTP header'
                 ' in HTTP request.')
        show_ptr = self.admin_ptr_client.show_ptr_record(
            floatingip_id=fip_id,
            headers={
                'x-auth-sudo-project-id': self.primary_ptr_client.project_id})
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

    @decorators.idempotent_id('a108d6f2-e3c0-11eb-a097-74e5f9e2a801')
    @decorators.skip_because(bug="1935977")
    def test_list_floatingip_ptr_all_projects(self):
        ptr = self._set_ptr()[1]
        LOG.info('Created PTR is:{}'.format(ptr))

        LOG.info('As Admin user, try to list PTR record for all projects '
                 'by including "x-auth-all-projects" HTTP header.')
        received_ptr_ids = [
            item['id'] for item in self.admin_ptr_client.list_ptr_records(
                headers={'x-auth-all-projects': True})]
        self.assertGreater(
            len(received_ptr_ids), 0,
            'Failed, "received_ptr_ids" should not be empty')
        self.assertIn(
            ptr['id'], received_ptr_ids,
            'Failed, expected ID was not found in "received_ptr_ids" list.')

    @decorators.idempotent_id('499b5a7e-87e1-11eb-b412-74e5f9e2a801')
    @testtools.skipUnless(config.CONF.dns_feature_enabled.bug_1932026_fixed,
                          'Skip unless bug 1932026 has been fixed.')
    def test_unset_floatingip_ptr(self):
        fip_id, ptr = self._set_ptr()
        self._unset_ptr(fip_id)


class DesignatePtrRecordNegative(BasePtrTest, tempest.test.BaseTestCase):

    credentials = ['primary', 'admin', 'system_admin']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(DesignatePtrRecordNegative, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(DesignatePtrRecordNegative, cls).setup_clients()
        cls.primary_ptr_client = cls.os_primary.dns_v2.PtrClient()
        cls.primary_floating_ip_client = cls.os_primary.floating_ips_client
        cls.admin_ptr_client = cls.os_admin.dns_v2.PtrClient()

    @classmethod
    def resource_setup(cls):
        super(DesignatePtrRecordNegative, cls).resource_setup()

        # The 'arpa' TLD is a special case as the positive test class also
        # needs to use this space. To stop test class concurrency conflicts,
        # let each class manage different TLDs for the reverse namespace.
        cls.in_addr_arpa_tld = cls.admin_tld_client.create_tld(
            tld_name='in-addr.arpa')

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.in_addr_arpa_tld[1]['id'])
        super(DesignatePtrRecordNegative, cls).resource_cleanup()

    def _set_ptr(self, ptr_name=None, ttl=None, description=None,
                 headers=None, tld=None, fip_id=None):
        if not tld:
            tld = self.tld_name
        if not fip_id:
            fip = self.primary_floating_ip_client.create_floatingip(
                floating_network_id=CONF.network.public_network_id)[
                'floatingip']
            fip_id = fip['id']
            self.addCleanup(
                self.primary_floating_ip_client.delete_floatingip, fip_id)
        ptr = self.primary_ptr_client.set_ptr_record(
            fip_id, ptr_name=ptr_name, ttl=ttl, description=description,
            headers=headers, tld=tld)
        self.addCleanup(self.unset_ptr, self.primary_ptr_client, fip_id)
        self.assertEqual('CREATE', ptr['action'])
        self.assertEqual('PENDING', ptr['status'])
        waiters.wait_for_ptr_status(
            self.primary_ptr_client, fip_id=fip_id, status=const.ACTIVE)
        return fip_id, ptr

    @decorators.attr(type='negative')
    @decorators.idempotent_id('8392db50-cdd0-11eb-a00f-74e5f9e2a801')
    def test_set_floatingip_ptr_invalid_ttl(self):
        LOG.info('Try to set PTR record using invalid TTL value')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self._set_ptr(ttl=-10)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('0c9349ae-e2e8-11eb-a097-74e5f9e2a801')
    def test_set_floatingip_ptr_not_existing_fip_id(self):
        LOG.info('Try to set PTR record using not existing Floating IP')
        with self.assertRaisesDns(lib_exc.NotFound, 'not_found', 404):
            self._set_ptr(fip_id=data_utils.rand_uuid())

    @decorators.attr(type='negative')
    @decorators.idempotent_id('df217902-e3b2-11eb-a097-74e5f9e2a801')
    def test_set_floatingip_ptr_huge_size_description(self):
        LOG.info('Try to set PTR record using huge size description string')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_object', 400):
            self._set_ptr(description=dns_data_utils.rand_string(5000))

    @decorators.attr(type='negative')
    @decorators.idempotent_id('cb2264e2-e3b3-11eb-a097-74e5f9e2a801')
    def test_set_floatingip_ptr_invalid_name(self):
        invalid_names = ['', '@!(*&', 4564, dns_data_utils.rand_string(5000)]
        for name in invalid_names:
            LOG.info('Set PTR record using invalid name:{}'.format(name))
            with self.assertRaisesDns(
                    lib_exc.BadRequest, 'invalid_object', 400):
                self._set_ptr(description=dns_data_utils.rand_string(5000))

    @decorators.attr(type='negative')
    @decorators.idempotent_id('f616d216-51ac-11ec-8edf-201e8823901f')
    def test_show_floatingip_ptr_impersonate_another_project_no_header(self):
        fip_id, ptr = self._set_ptr()

        LOG.info('As Admin user, show PTR record created by Primary'
                 ' user, without including "x-auth-sudo-project-id" '
                 'HTTP header in request.')
        with self.assertRaisesDns(lib_exc.NotFound, 'not_found', 404):
            self.admin_ptr_client.show_ptr_record(floatingip_id=fip_id)

    @decorators.attr(type='negative')
    @decorators.idempotent_id('0d132ff0-51ad-11ec-8edf-201e8823901f')
    @decorators.skip_because(bug="1935977")
    def test_list_floatingip_ptr_all_projects_no_header(self):
        ptr = self._set_ptr()[1]
        LOG.info('Created PTR is:{}'.format(ptr))

        LOG.info('As Admin user, try to list PTR record for all projects '
                 'without including "x-auth-all-projects" HTTP header.')
        received_ptr_ids = [
            item['id'] for item in self.admin_ptr_client.list_ptr_records()]
        self.assertEqual([], received_ptr_ids,
                         'Failed, "received_ptr_ids" list should be empty')
