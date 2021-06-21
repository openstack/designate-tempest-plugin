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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.lib.common.utils import data_utils as lib_data_utils
import ddt

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import waiters
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
        cls.zone_client.delete_zone(
            cls.zone['id'], ignore_errors=lib_exc.NotFound)

        super(BaseRecordsetsTest, cls).resource_cleanup()


@ddt.ddt
class RecordsetsTest(BaseRecordsetsTest):

    credentials = ["admin", 'primary', 'alt']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(RecordsetsTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(RecordsetsTest, cls).setup_clients()

        cls.client = cls.os_primary.recordset_client
        cls.alt_client = cls.os_alt.recordset_client
        cls.admin_client = cls.os_admin.recordset_client
        cls.zone_client = cls.os_primary.zones_client
        cls.alt_zone_client = cls.os_alt.zones_client
        cls.admin_zone_client = cls.os_admin.zones_client

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('631d74fd-6909-4684-a61b-5c4d2f92c3e7')
    def test_create_recordset(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])

        LOG.info('Create a Recordset')
        resp, body = self.client.create_recordset(
            self.zone['id'], recordset_data)

        LOG.info('Ensure we respond with PENDING')
        self.assertEqual('PENDING', body['status'])

    @decorators.idempotent_id('d03b69a5-5052-43bc-a38a-b511b6b34304')
    @ddt.file_data("recordset_data.json")
    def test_create_all_recordset_types(self, name, type, records):
        if name is not None:
            recordset_name = name + "." + self.zone['name']

        else:
            recordset_name = self.zone['name']

        recordset_data = {
            'name': recordset_name,
            'type': type,
            'records': records,
        }

        LOG.info('Create a Recordset')
        resp, body = self.client.create_recordset(
            self.zone['id'], recordset_data)

        LOG.info('Ensure we respond with PENDING')
        self.assertEqual('PENDING', body['status'])

    @decorators.idempotent_id('69f002e5-6511-43d3-abae-7abdd45ae03e')
    @ddt.file_data("recordset_wildcard_data.json")
    def test_create_wildcard_recordset(self, name, type, records):
        if name is not None:
            recordset_name = name + "." + self.zone['name']

        else:
            recordset_name = "*." + self.zone['name']

        recordset_data = {
            'name': recordset_name,
            'type': type,
            'records': records,
        }

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

    @decorators.idempotent_id('3f3575a0-a28b-11eb-ab42-74e5f9e2a801')
    def test_show_recordsets_impersonate_another_project(self):

        LOG.info('Create a Recordset')
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])
        resp, body = self.client.create_recordset(
            self.zone['id'], recordset_data)
        self.assertEqual('PENDING', body['status'],
                         'Failed, expected status is PENDING')
        LOG.info('Wait until the recordset is active')
        waiters.wait_for_recordset_status(
            self.client, self.zone['id'],
            body['id'], 'ACTIVE')

        LOG.info('Re-Fetch the Recordset as Alt tenant with '
                 '"x-auth-sudo-project-id" HTTP header included in request. '
                 'Expected: 403')
        self.assertRaises(
            lib_exc.Forbidden, lambda: self.alt_client.show_recordset(
                self.zone['id'], body['id'], headers={
                    'x-auth-sudo-project-id': body['project_id']}))

        LOG.info('Re-Fetch the Recordset as Admin tenant without '
                 '"x-auth-sudo-project-id" HTTP header. Expected: 404')
        self.assertRaises(lib_exc.NotFound,
                          lambda: self.admin_client.show_recordset(
                              self.zone['id'], body['id']))

        record = self.admin_client.show_recordset(
            self.zone['id'], body['id'],
            headers={'x-auth-sudo-project-id': body['project_id']})[1]

        LOG.info('Ensure the fetched response matches the expected one')
        self.assertExpected(body, record,
                            self.excluded_keys + ['action', 'status'])

    @decorators.idempotent_id('9f364a64-a2aa-11eb-aad4-74e5f9e2a801')
    def test_admin_list_all_recordsets_for_a_project(self):

        LOG.info('Create a Recordset as Primary tenant')
        recordset_data_primary_1 = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])
        body_pr_1 = self.client.create_recordset(
            self.zone['id'], recordset_data_primary_1)[1]
        self.assertEqual('PENDING', body_pr_1['status'],
                         'Failed, expected status is PENDING')
        recordset_data_primary_2 = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])
        body_pr_2 = self.client.create_recordset(
            self.zone['id'], recordset_data_primary_2)[1]
        self.assertEqual('PENDING', body_pr_2['status'],
                         'Failed, expected status is PENDING')

        LOG.info('Re-Fetch Recordsets as Alt tenant for a Primary project. '
                 'Expected: 404')
        self.assertRaises(lib_exc.NotFound,
            lambda: self.alt_client.list_recordset(
                self.zone['id']))

        LOG.info('Re-Fetch Recordsets as Alt tenant for a Primary project '
                 'using "x-auth-all-projects" HTTP header. Expected: 403')
        self.assertRaises(lib_exc.Forbidden,
            lambda: self.alt_client.list_recordset(
                self.zone['id'],
                headers={'x-auth-all-projects': True}))

        LOG.info('Re-Fetch Recordsets as Admin tenant for a Primary project '
                 'using "x-auth-all-projects" HTTP header.')
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        primary_recordsets_ids = [
            item['id'] for item in self.admin_client.list_recordset(
                self.zone['id'],
                headers={'x-auth-all-projects': True},
                params={'limit': 1000})[1]['recordsets']]

        for recordset_id in [body_pr_1['id'], body_pr_2['id']]:
            self.assertIn(
                recordset_id, primary_recordsets_ids,
                'Failed, recordset ID:{} was not found in listed '
                'recordsets: {}'.format(recordset_id, primary_recordsets_ids))


@ddt.ddt
class RecordsetsNegativeTest(BaseRecordsetsTest):

    credentials = ['primary', 'alt']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(RecordsetsNegativeTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(RecordsetsNegativeTest, cls).setup_clients()

        cls.client = cls.os_primary.recordset_client
        cls.alt_client = cls.os_alt.recordset_client
        cls.zone_client = cls.os_primary.zones_client

    @decorators.idempotent_id('98c94f8c-217a-4056-b996-b1f856d0753e')
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

    @decorators.idempotent_id('b6dad57e-5ce9-4fa5-8d66-aebbcd23b4ad')
    def test_get_nonexistent_recordset(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Attempt to get an invalid Recordset')
        with self.assertRaisesDns(
                lib_exc.NotFound, 'recordset_not_found', 404):
            self.client.show_recordset(zone['id'], lib_data_utils.rand_uuid())

    @decorators.idempotent_id('93d744a8-0dfd-4650-bcef-1e6ad632ad72')
    def test_get_nonexistent_recordset_invalid_id(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Attempt to get an invalid Recordset')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_uuid', 400):
            self.client.show_recordset(zone['id'], 'invalid')

    @decorators.idempotent_id('da08f19a-7f10-47cc-8b41-994507190812')
    def test_update_nonexistent_recordset(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        recordset_data = data_utils.rand_recordset_data('A', zone['name'])

        LOG.info('Attempt to update an invalid Recordset')
        with self.assertRaisesDns(
                lib_exc.NotFound, 'recordset_not_found', 404):
            self.client.update_recordset(
                zone['id'], lib_data_utils.rand_uuid(), recordset_data)

    @decorators.idempotent_id('158340a1-3f69-4aaa-9968-956190563768')
    def test_update_nonexistent_recordset_invalid_id(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        recordset_data = data_utils.rand_recordset_data('A', zone['name'])

        LOG.info('Attempt to update an invalid Recordset')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_uuid', 400):
            self.client.update_recordset(
                zone['id'], 'invalid', recordset_data)

    @decorators.idempotent_id('64bd94d4-54bd-4bee-b6fd-92ede063234e')
    def test_delete_nonexistent_recordset(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Attempt to delete an invalid Recordset')
        with self.assertRaisesDns(
                lib_exc.NotFound, 'recordset_not_found', 404):
            self.client.delete_recordset(
                zone['id'], lib_data_utils.rand_uuid())

    @decorators.idempotent_id('5948b599-a332-4dcb-840b-afc825075ba3')
    def test_delete_nonexistent_recordset_invalid_id(self):
        LOG.info('Create a zone')
        _, zone = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Attempt to get an invalid Recordset')
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_uuid', 400):
            self.client.delete_recordset(zone['id'], 'invalid')

    @decorators.idempotent_id('64e01dc4-a2a8-11eb-aad4-74e5f9e2a801')
    def test_show_recordsets_invalid_ids(self):

        LOG.info('Create a Recordset')
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])
        resp, body = self.client.create_recordset(
            self.zone['id'], recordset_data)
        self.assertEqual('PENDING', body['status'],
                         'Failed, expected status is PENDING')
        LOG.info('Wait until the recordset is active')
        waiters.wait_for_recordset_status(
            self.client, self.zone['id'],
            body['id'], 'ACTIVE')

        LOG.info('Ensure 404 NotFound status code is received if '
                 'recordset ID is invalid.')
        self.assertRaises(
            lib_exc.NotFound, lambda: self.client.show_recordset(
                zone_uuid=self.zone['id'],
                recordset_uuid=lib_data_utils.rand_uuid()))

        LOG.info('Ensure 404 NotFound status code is received if '
                 'zone ID is invalid.')
        self.assertRaises(
            lib_exc.NotFound, lambda: self.client.show_recordset(
                zone_uuid=lib_data_utils.rand_uuid(),
                recordset_uuid=body['id']))

    @decorators.idempotent_id('c1d9f046-a2b1-11eb-aad4-74e5f9e2a801')
    def test_create_recordset_for_other_tenant(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])

        LOG.info('Create a Recordset as Alt tenant for a zone created by '
                 'Primary tenant. Expected: 404 NotFound')
        self.assertRaises(
            lib_exc.NotFound, lambda: self.alt_client.create_recordset(
                self.zone['id'], recordset_data))


class RootRecordsetsTests(BaseRecordsetsTest):
    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(RootRecordsetsTests, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(RootRecordsetsTests, cls).setup_clients()

        cls.client = cls.os_primary.recordset_client
        cls.zone_client = cls.os_primary.zones_client

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

    @decorators.idempotent_id('65ec0495-81d9-4cfb-8007-9d93b32ae883')
    def test_get_single_zones_recordsets(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'], records=['10.1.0.2'])

        LOG.info('Create a Recordset')
        resp, zone_recordset = self.client.create_recordset(
            self.zone['id'], recordset_data)

        self.client.show_zones_recordset(zone_recordset['id'])

    @decorators.idempotent_id('a8e41020-65be-453b-a8c1-2497d539c345')
    def test_list_filter_zones_recordsets(self):
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'], records=['10.0.1.2'])

        LOG.info('Create a Recordset')
        resp, zone_recordset = self.client.create_recordset(
            self.zone['id'], recordset_data)

        LOG.info('Create another zone')
        _, zone2 = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone2['id'])

        LOG.info('Create another Recordset')
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone2['name'],
            records=['10.0.1.3'])
        resp, zone_recordset2 = self.client.create_recordset(
            zone2['id'], recordset_data)

        LOG.info('List recordsets')
        _, body = self.client.list_zones_recordsets(params={"data": "10.0.*"})

        recordsets = body['recordsets']

        ids = [r['id'] for r in recordsets]
        self.assertIn(zone_recordset['id'], ids)
        self.assertIn(zone_recordset2['id'], ids)
        # Ensure that every rrset has a record with the filtered data
        for r in recordsets:
            one_record_has_data = False
            for record in r['records']:
                if record.startswith('10.0.'):
                    one_record_has_data = True
            self.assertTrue(one_record_has_data)

    @decorators.idempotent_id('7f4970bf-9aeb-4a3c-9afd-02f5a7178d35')
    def test_list_zones_recordsets_zone_names(self):
        LOG.info('Create another zone')
        _, zone2 = self.zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone2['id'])

        LOG.info('List recordsets')
        _, body = self.client.list_zones_recordsets()

        recordsets = body['recordsets']
        zone_names = set()
        for r in recordsets:
            zone_names.add(r['zone_name'])

        self.assertGreaterEqual(len(zone_names), 2)


class RecordsetOwnershipTest(BaseRecordsetsTest):

    credentials = ['primary', 'alt', 'admin']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(RecordsetOwnershipTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(RecordsetOwnershipTest, cls).setup_clients()

        cls.client = cls.os_primary.recordset_client
        cls.zone_client = cls.os_primary.zones_client
        cls.alt_client = cls.os_alt.recordset_client
        cls.alt_zone_client = cls.os_alt.zones_client
        cls.admin_client = cls.os_admin.recordset_client

    def _create_client_recordset(self, clients_list):
        """Create a zone and asoociated recordset using given credentials
        :param clients_list: supported credentials are: 'primary' and 'alt'.
        :return: dictionary of created recordsets.
        """
        recordsets_created = {}
        for client in clients_list:
            if client == 'primary':
                # Create a zone and wait till it's ACTIVE
                zone = self.zone_client.create_zone()[1]
                self.addCleanup(self.wait_zone_delete,
                                self.zone_client,
                                zone['id'])
                waiters.wait_for_zone_status(
                    self.zone_client, zone['id'], 'ACTIVE')

                # Create a recordset and wait till it's ACTIVE
                recordset_data = data_utils.rand_recordset_data(
                    record_type='A', zone_name=zone['name'])
                resp, body = self.client.create_recordset(
                    zone['id'], recordset_data)
                self.assertEqual('PENDING', body['status'],
                                 'Failed, expected status is PENDING')
                LOG.info('Wait until the recordset is active')
                waiters.wait_for_recordset_status(
                    self.client, zone['id'],
                    body['id'], 'ACTIVE')

                # Add "project_id" into the recordset_data
                recordset_data['project_id'] = zone['project_id']
                recordsets_created['primary'] = recordset_data

            if client == 'alt':
                # Create a zone and wait till it's ACTIVE
                alt_zone = self.alt_zone_client.create_zone()[1]
                self.addCleanup(self.wait_zone_delete,
                                self.alt_zone_client,
                                alt_zone['id'])
                waiters.wait_for_zone_status(
                    self.alt_zone_client, alt_zone['id'], 'ACTIVE')

                # Create a recordset and wait till it's ACTIVE
                recordset_data = data_utils.rand_recordset_data(
                    record_type='A', zone_name=alt_zone['name'])
                resp, body = self.alt_client.create_recordset(
                    alt_zone['id'], recordset_data)
                self.assertEqual('PENDING', body['status'],
                                 'Failed, expected status is PENDING')
                LOG.info('Wait until the recordset is active')
                waiters.wait_for_recordset_status(
                    self.alt_client, alt_zone['id'],
                    body['id'], 'ACTIVE')

                # Add "project_id" into the recordset_data
                recordset_data['project_id'] = alt_zone['project_id']
                recordsets_created['alt'] = recordset_data

        return recordsets_created

    @decorators.idempotent_id('9c0f58ad-1b31-4899-b184-5380720604e5')
    def test_no_create_recordset_by_alt_tenant(self):
        # try with name=A123456.zone.com.
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=self.zone['name'])
        resp, rrset = self.client.create_recordset(
            self.zone['id'], recordset_data)
        self.assertRaises(
            lib_exc.RestClientException,
            lambda: self.alt_client.create_recordset(
                self.zone['id'], recordset_data)
        )

    @decorators.idempotent_id('d4a9aad9-c778-429b-9a0c-4cd2b61a0a01')
    def test_no_create_super_recordsets(self):
        zone_name = data_utils.rand_zone_name()

        LOG.info('Create a zone as a default user')
        _, zone = self.zone_client.create_zone(name='a.b.' + zone_name)
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        rrset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone_name)

        LOG.info('Create a zone as an alt user with existing superdomain')
        self.assertRaises(
            lib_exc.NotFound,
            self.alt_client.create_recordset,
            self.zone['id'], rrset_data)

    @decorators.idempotent_id('3dbe244d-fa85-4afc-869b-0306388d8746')
    def test_no_create_recordset_via_alt_domain(self):
        _, zone = self.zone_client.create_zone()
        _, alt_zone = self.alt_zone_client.create_zone()
        self.addCleanup(self.wait_zone_delete,
                        self.zone_client,
                        zone['id'])
        self.addCleanup(self.wait_zone_delete,
                        self.alt_zone_client,
                        alt_zone['id'])

        # alt attempts to create record with name A12345.{zone}
        recordset_data = data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'])

        self.assertRaises(
            lib_exc.RestClientException,
            lambda: self.alt_client.create_recordset(
                zone['id'],
                recordset_data
            )
        )
        self.assertRaises(
            lib_exc.RestClientException,
            lambda: self.alt_client.create_recordset(
                alt_zone['id'],
                recordset_data
            )
        )

    @decorators.idempotent_id('4d0ff972-7c19-11eb-b331-74e5f9e2a801')
    def test_list_all_recordsets_for_project(self):
        # Create recordsets using "primary" and "alt" credentials.
        # Execute "list_owned_recordsets" API to list "primary" recordsets.
        # Validate that the only "project_id" retrieved within the API is
        # a "primary" project.
        primary_project_id = self._create_client_recordset(
            ['primary', 'alt'])['primary']['project_id']
        recordsets = self.client.list_owned_recordsets()
        LOG.info('Received by API recordsets are {} '.format(recordsets))
        project_ids_api = set([item['project_id'] for item in recordsets])
        self.assertEqual(
            {primary_project_id}, project_ids_api,
            'Failed, unique project_ids {} are not as expected {}'.format(
                project_ids_api, primary_project_id))

    @decorators.idempotent_id('bc0af248-7b4f-11eb-98a5-74e5f9e2a801')
    def test_list_all_projects_recordsets(self):
        # Create recordsets using "primary" and "alt" credentials.
        # Execute "list_owned_recordsets" API using admin client to list
        # recordsets for all projects.
        # Validate that project_ids of: "primary" and "alt" projects
        # are both listed in received API response.
        project_ids_used = [
            item['project_id'] for item in self._create_client_recordset(
                ['primary', 'alt']).values()]
        # Note: This is an all-projects list call, so other tests running
        #       in parallel will impact the list result set. Since the default
        #       pagination limit is only 20, we set a param limit of 1000 here.
        recordsets = self.admin_client.list_owned_recordsets(
            headers={'x-auth-all-projects': True}, params={'limit': 1000})
        LOG.info('Received by API recordsets are {} '.format(recordsets))
        project_ids_api = set([item['project_id'] for item in recordsets])
        for prj_id in project_ids_used:
            self.assertIn(
                prj_id, project_ids_api,
                'Failed, project_id:{} is missing in received recordsets'
                ' for all projects {} '.format(prj_id, project_ids_api))

    @decorators.idempotent_id('910eb17e-7c3a-11eb-a40b-74e5f9e2a801')
    def test_list_recordsets_impersonate_project(self):
        # Create recordsets using "primary" and "alt" credentials.
        # Use admin client to impersonate "primary" project.
        # Validate that received recordsets are all associated with
        # expected("primary") project only.
        primary_project_id = self._create_client_recordset(
            ['primary', 'alt'])['primary']['project_id']
        recordsets = self.admin_client.list_owned_recordsets(
            headers={'x-auth-sudo-project-id': primary_project_id})
        LOG.info('Received by API recordsets are {} '.format(recordsets))
        project_ids_api = set([item['project_id'] for item in recordsets])
        self.assertEqual(
            {primary_project_id}, project_ids_api,
            'Failed, unique project_ids {} are not as expected {}'.format(
                project_ids_api, primary_project_id))
