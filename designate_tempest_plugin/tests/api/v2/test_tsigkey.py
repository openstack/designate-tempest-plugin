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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseTsigkeyTest(base.BaseDnsV2Test):
    excluded_keys = ['created_at', 'updated_at', 'links']

    @classmethod
    def setup_clients(cls):
        super(BaseTsigkeyTest, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(BaseTsigkeyTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="BaseTsigkeyTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(BaseTsigkeyTest, cls).resource_cleanup()


class TsigkeyAdminTest(BaseTsigkeyTest):
    credentials = ["primary", "admin", "system_admin", "system_reader",
                   "project_member", "project_reader", "alt"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TsigkeyAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TsigkeyAdminTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.TsigkeyClient()
            cls.pool_admin_client = cls.os_system_admin.dns_v2.PoolClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.TsigkeyClient()
            cls.pool_admin_client = cls.os_admin.dns_v2.PoolClient()

        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.primary_client = cls.os_primary.dns_v2.TsigkeyClient()

    @decorators.idempotent_id('e7b484e3-7ed5-4840-89d7-1e696986f8e4')
    def test_create_tsigkey_for_zone(self):
        LOG.info('Create a resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_tsigkey_for_zone", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        tsigkey_data = {
                        "name": dns_data_utils.rand_zone_name(
                            'test_create_tsigkey_for_zone'),
                        "algorithm": "hmac-sha256",
                        "secret": "SomeSecretKey",
                        "scope": "ZONE",
                        "resource_id": zone['id']}

        LOG.info('Create a tsigkey')
        tsigkey = self.admin_client.create_tsigkey(
                         tsigkey_data['resource_id'],
                         tsigkey_data['name'], tsigkey_data['algorithm'],
                         tsigkey_data['secret'], tsigkey_data['scope'])[1]
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])

        self.assertEqual(tsigkey_data["name"], tsigkey['name'])
        self.assertEqual(tsigkey_data["scope"], 'ZONE')

    @decorators.idempotent_id('45975fa6-d726-11eb-beba-74e5f9e2a801')
    def test_create_tsigkey_for_pool(self):
        LOG.info('Get the valid pool ID from list of pools')
        pool = self.pool_admin_client.list_pools()[1]['pools'][0]

        LOG.info('Create a tsigkey')
        tsigkey_data = {
                        "name": dns_data_utils.rand_zone_name('Example_Key'),
                        "algorithm": "hmac-sha256",
                        "secret": "SomeSecretKey",
                        "scope": "POOL",
                        "resource_id": pool['id']}
        tsigkey = self.admin_client.create_tsigkey(
                         tsigkey_data['resource_id'],
                         tsigkey_data['name'], tsigkey_data['algorithm'],
                         tsigkey_data['secret'], tsigkey_data['scope'])[1]
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])
        self.assertEqual(tsigkey_data["name"], tsigkey['name'])
        self.assertEqual(tsigkey_data["scope"], 'POOL')

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'TsigkeyClient', 'create_tsigkey', expected_allowed, False,
            tsigkey_data['resource_id'],
            tsigkey_data['name'], tsigkey_data['algorithm'],
            tsigkey_data['secret'], tsigkey_data['scope'])

    @decorators.idempotent_id('d46e5e86-a18c-4315-aa0c-95a00e816fbf')
    def test_list_tsigkey(self):
        LOG.info('Create a resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_tsigkey", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        LOG.info('Create a tsigkey')
        tsigkey = self.admin_client.create_tsigkey(resource_id=zone['id'])[1]
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])
        body = self.admin_client.list_tsigkeys()[1]
        self.assertGreater(len(body['tsigkeys']), 0)

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader']
        self.check_list_IDs_RBAC_enforcement(
            'TsigkeyClient', 'list_tsigkeys', expected_allowed,
            [tsigkey['id']])

    @decorators.idempotent_id('d46e5e86-a18c-4315-aa0c-95a00e816fbf')
    def test_list_tsigkeys_limit_results(self):
        for i in range(3):
            LOG.info('As Primary user create a zone: {} '.format(i))
            zone_name = dns_data_utils.rand_zone_name(
                name="list_tsigkey_limit", suffix=self.tld_name)
            zone = self.zone_client.create_zone(name=zone_name)[1]
            self.addCleanup(
                self.wait_zone_delete, self.zone_client, zone['id'])
            LOG.info('As Admin user create a tsigkey: {} '.format(i))
            tsigkey = self.admin_client.create_tsigkey(
                resource_id=zone['id'])[1]
            self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])
        LOG.info('As Admin client, list all tsigkey using '
                 'URL query: "limit=2"')
        body = self.admin_client.list_tsigkeys(params={'limit': 2})[1]
        self.assertEqual(len(body['tsigkeys']), 2)

    @decorators.idempotent_id('f31447b0-d817-11eb-b95a-74e5f9e2a801')
    def test_list_tsigkeys_using_marker(self):
        test_tsigkeys_name = 'marker_tsigkey_'
        test_tsigkeys_names = [test_tsigkeys_name + str(i) for i in range(4)]

        LOG.info('Create tsigkeys named: {}'.format(test_tsigkeys_names))
        created_tsigkeys = []
        for name in test_tsigkeys_names:
            LOG.info('As Primary user create a zone to be used '
                     'for {}'.format(name))
            zone_name = dns_data_utils.rand_zone_name(
                name="list_tsigkey_marker", suffix=self.tld_name)
            zone = self.zone_client.create_zone(name=zone_name)[1]
            self.addCleanup(
                self.wait_zone_delete, self.zone_client, zone['id'])
            LOG.info('As Admin user create "{}" tsigkey'.format(name))
            tsigkey = self.admin_client.create_tsigkey(
                resource_id=zone['id'], name=name)[1]
            self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])
            created_tsigkeys.append(tsigkey['id'])

        LOG.info('As Admin, list all tsigkeys using url queries:"limit=2" '
                 'and "name={}*"'.format(test_tsigkeys_name))
        body = self.admin_client.list_tsigkeys(
            params={
                'limit': 2, 'name': test_tsigkeys_name + '*'})[1]
        tsigkeys = body['tsigkeys']
        self.assertEqual(2, len(tsigkeys),
                         'Failed, response is not limited as expected')

        LOG.info('Get the marker to be used for subsequent request')
        first_set_of_ids = [item['id'] for item in tsigkeys]
        links = body['links']
        marker = links['next'].split('marker=')[-1]

        LOG.info('Use marker for subsequent request to get the rest of '
                 'tsigkeys that contains "{}*" in their '
                 'names'.format(test_tsigkeys_name))
        tsigkeys = self.admin_client.list_tsigkeys(
            params={'marker': marker, 'limit': 2,
                    'name': test_tsigkeys_name + '*'})[1]['tsigkeys']
        self.assertEqual(2, len(tsigkeys),
                         'Failed, response is not limited as expected')
        second_set_of_ids = [item['id'] for item in tsigkeys]

        LOG.info('Make sure that the merge of tsigkeys IDs received in two '
                 'phases using "marker" url query, contains all the IDs '
                 'created within the test')
        self.assertEqual(
            sorted(first_set_of_ids + second_set_of_ids),
            sorted(created_tsigkeys),
            'Failed, tsigkeys IDs received in two phases are not as expected')

    @decorators.idempotent_id('d5c6dfcc-d8af-11eb-b95a-74e5f9e2a801')
    def test_list_tsigkey_sort_key_with_sort_direction(self):
        names_to_create = [data_utils.rand_name(name) for name in
                           ['bbb_tsgikey', 'aaa_tsgikey', 'ccc_tsgikey']]
        created_tsigkey_ids = []
        for name in names_to_create:
            LOG.info('As Primary user create a zone for: {} '.format(name))
            zone_name = dns_data_utils.rand_zone_name(
                name="list_tsigkey_sort", suffix=self.tld_name)
            zone = self.zone_client.create_zone(name=zone_name)[1]
            self.addCleanup(
                self.wait_zone_delete, self.zone_client, zone['id'])
            LOG.info('As Admin user create a tsigkey: {} '.format(name))
            tsigkey = self.admin_client.create_tsigkey(
                resource_id=zone['id'], name=name)[1]
            self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])
            created_tsigkey_ids.append(tsigkey['id'])

        LOG.info('As Admin, list all tsigkeys using "asc" to sort by names')
        sorted_tsigkeys = self.admin_client.list_tsigkeys(
            params={'sort_dir': 'asc', 'sort_key': 'name'})[1]['tsigkeys']
        sorted_by_names = [item['name'] for item in sorted_tsigkeys]
        self.assertEqual(
            sorted(sorted_by_names),
            sorted_by_names,
            'Failed, tsgikeys names are not sorted in "asc" as expected')

        LOG.info('As Admin, list all tsigkey using "desc" to sort by names')
        sorted_tsigkeys = self.admin_client.list_tsigkeys(
            params={'sort_dir': 'desc', 'sort_key': 'name'})[1]['tsigkeys']
        sorted_by_names = [item['name'] for item in sorted_tsigkeys]
        self.assertEqual(
            sorted(sorted_by_names, reverse=True),
            sorted_by_names,
            'Failed, tsgikeys names are not sorted in "desc" as expected')

        LOG.info('As Admin, list all tsigkeys using "asc" to sort by ID')
        sorted_tsigkeys = self.admin_client.list_tsigkeys(
            params={'sort_dir': 'asc', 'sort_key': 'id'})[1]['tsigkeys']
        sorted_by_ids = [item['id'] for item in sorted_tsigkeys]
        self.assertEqual(
            sorted(sorted_by_ids),
            sorted_by_ids,
            'Failed, tsgikeys IDs are not sorted in "asc" as expected')

        LOG.info('As Admin, list all tsigkeys using "zababun" direction '
                 'to sort by names, expected: "invalid_sort_dir"')
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_sort_dir', 400,
            self.admin_client.list_tsigkeys,
            params={'sort_dir': 'zababun', 'sort_key': 'name'})

        LOG.info('As Admin, list all tsigkeys using "zababun" as a key value,'
                 'expected: "invalid_sort_key"')
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_sort_key', 400,
            self.admin_client.list_tsigkeys,
            params={'sort_dir': 'asc', 'sort_key': 'zababun'})

    @decorators.idempotent_id('4162a840-d8b2-11eb-b95a-74e5f9e2a801')
    def test_list_tsigkey_filter_by_name(self):
        tsigkey_name = data_utils.rand_name('ddd_tsgikey')
        LOG.info('As Primary user create a zone for: {} '.format(tsigkey_name))
        zone_name = dns_data_utils.rand_zone_name(
            name="list_tsigkey_filter_name", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        LOG.info('As Admin user create a tsigkey: {} '.format(tsigkey_name))
        tsigkey = self.admin_client.create_tsigkey(
            resource_id=zone['id'], name=tsigkey_name)[1]
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])

        LOG.info('As Admin, list all tsigkeys named:{}'.format(tsigkey_name))
        listed_tsigkeys = self.admin_client.list_tsigkeys(
            params={'name': tsigkey_name})[1]['tsigkeys']
        self.assertEqual(
            1, len(listed_tsigkeys),
            'Failed, only a single tsigkey, named: {} should be '
            'listed.'.format(tsigkey_name))

        LOG.info('As Admin, list all tsigkeys named:"zababun"')
        listed_tsigkeys = self.admin_client.list_tsigkeys(
            params={'name': 'zababun'})[1]['tsigkeys']
        self.assertEqual(
            0, len(listed_tsigkeys), 'Failed, no tsigkey should be listed')

    @decorators.idempotent_id('e8bcf80a-d8b4-11eb-b95a-74e5f9e2a801')
    def test_list_tsigkey_filter_by_scope(self):

        LOG.info('Create tsigkey for a pool')
        pool = self.pool_admin_client.create_pool(
            project_id=self.os_admin.credentials.project_id)[1]
        self.addCleanup(
            self.pool_admin_client.delete_pool, pool['id'],
            headers={
                'x-auth-sudo-project-id':
                    self.os_admin.credentials.project_id})
        pool_tsigkey = self.admin_client.create_tsigkey(
            resource_id=pool['id'], scope='POOL')[1]
        self.addCleanup(self.admin_client.delete_tsigkey, pool_tsigkey['id'])

        LOG.info('Create tsigkey for a zone')
        zone_name = dns_data_utils.rand_zone_name(
            name="list_tsigkey_filter_scope", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        zone_tsigkey = self.admin_client.create_tsigkey(
            resource_id=zone['id'], scope='ZONE')[1]
        self.addCleanup(self.admin_client.delete_tsigkey, zone_tsigkey['id'])

        LOG.info('List all "scope=POOL" tsigkeys')
        listed_pool_scopes = [
            item['scope'] for item in self.admin_client.list_tsigkeys(
                params={'scope': 'POOL'})[1]['tsigkeys']]
        self.assertEqual(
            {'POOL'}, set(listed_pool_scopes),
            'Failed, the only scopes expected to be listed are: "POOL"')

        LOG.info('List all "scope=ZONE" tsigkeys')
        listed_zone_scopes = [
            item['scope'] for item in self.admin_client.list_tsigkeys(
                params={'scope': 'ZONE'})[1]['tsigkeys']]
        self.assertEqual(
            {'ZONE'}, set(listed_zone_scopes),
            'Failed, the only scopes expected to be listed are: "ZONE"')

        LOG.info('List all "scope=zababun" tsigkeys')
        listed_zone_scopes = [
            item['scope'] for item in self.admin_client.list_tsigkeys(
                params={'scope': 'zababun'})[1]['tsigkeys']]
        self.assertEqual(
            0, len(listed_zone_scopes),
            'Failed, no tsigkey is expected to be listed')

    @decorators.idempotent_id('794554f0-d8b8-11eb-b95a-74e5f9e2a801')
    def test_list_tsigkey_filter_by_algorithm(self):

        LOG.info('Create tsigkey for a pool')
        algorithm = 'hmac-sha256'
        pool = self.pool_admin_client.create_pool(
            project_id=self.os_admin.credentials.project_id)[1]
        self.addCleanup(
            self.pool_admin_client.delete_pool, pool['id'],
            headers={
                'x-auth-sudo-project-id':
                    self.os_admin.credentials.project_id})
        pool_tsigkey = self.admin_client.create_tsigkey(
            resource_id=pool['id'], algorithm=algorithm)[1]
        self.addCleanup(self.admin_client.delete_tsigkey, pool_tsigkey['id'])

        LOG.info('List all "algorithm={}" tsigkeys '.format(algorithm))
        listed_tsigkeys = [
            item['algorithm'] for item in self.admin_client.list_tsigkeys(
                params={'algorithm': algorithm})[1]['tsigkeys']]
        self.assertEqual(
            {algorithm}, set(listed_tsigkeys),
            'Failed, the only tsigkeys expected to be listed must '
            'have algorithm:{} '.format(algorithm))

        LOG.info('List all "algorithm=zababun" tsigkeys')
        listed_tsigkeys = [
            item['algorithm'] for item in self.admin_client.list_tsigkeys(
                params={'algorithm': 'zababun'})[1]['tsigkeys']]
        self.assertEqual(
            0, len(listed_tsigkeys),
            "Failed, no tsigkey is expectedto be listed")

    @decorators.idempotent_id('c5d7facf-0f05-47a2-a4fb-87f203860880')
    def test_show_tsigkey(self):
        LOG.info('Create a resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="show_tsigkey", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a tsigkey')
        tsigkey = self.admin_client.create_tsigkey(resource_id=zone['id'])[1]
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])

        LOG.info('Fetch the tsigkey')
        body = self.admin_client.show_tsigkey(tsigkey['id'])[1]

        LOG.info('Ensure the fetched response matches the created tsigkey')
        self.assertExpected(tsigkey, body, self.excluded_keys)

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed = ['os_system_admin', 'os_system_reader']

        self.check_list_show_RBAC_enforcement(
            'TsigkeyClient', 'show_tsigkey', expected_allowed, True,
            tsigkey['id'])

    @decorators.idempotent_id('d09dc0dd-dd72-41ee-9085-2afb2bf35459')
    def test_update_tsigkey(self):
        LOG.info('Create a resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="update_tsigkey", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a tsigkey')
        tsigkey = self.admin_client.create_tsigkey(resource_id=zone['id'])[1]
        self.addCleanup(self.admin_client.delete_tsigkey, tsigkey['id'])

        tsigkey_data = {
                        "name": "Patch tsigkey",
                        "secret": "NewSecretKey"}

        LOG.info('Update the tsigkey')
        patch_tsigkey = self.admin_client.update_tsigkey(tsigkey['id'],
                               name=tsigkey_data['name'],
                               secret=tsigkey_data['secret'])[1]

        self.assertEqual(tsigkey_data['name'], patch_tsigkey['name'])
        self.assertEqual(tsigkey_data['secret'], patch_tsigkey['secret'])

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'TsigkeyClient', 'update_tsigkey', expected_allowed, False,
            tsigkey['id'], name=tsigkey_data['name'],
            secret=tsigkey_data['secret'])

    @decorators.idempotent_id('9cdffbd2-bc67-4a25-8eb7-4be8635c88a3')
    def test_delete_tsigkey(self):
        LOG.info('Create a resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="delete_tsigkey", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        LOG.info('Create a tsigkey')
        tsigkey = self.admin_client.create_tsigkey(resource_id=zone['id'])[1]

        # Test RBAC
        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.append('os_system_admin')

        self.check_CUD_RBAC_enforcement(
            'TsigkeyClient', 'delete_tsigkey', expected_allowed, False,
            tsigkey['id'])

        LOG.info('Delete the tsigkey')
        self.admin_client.delete_tsigkey(tsigkey['id'])

        self.assertRaises(lib_exc.NotFound,
           lambda: self.admin_client.show_tsigkey(tsigkey['id']))

    @decorators.idempotent_id('4bdc20ef-96f9-47f6-a1aa-275159af326b')
    def test_list_tsigkeys_dot_json_fails(self):
        uri = self.admin_client.get_uri('tsigkeys.json')

        self.assertRaises(lib_exc.NotFound,
            lambda: self.admin_client.get(uri))


class TestTsigkeyNotFoundAdmin(BaseTsigkeyTest):

    credentials = ["admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTsigkeyNotFoundAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTsigkeyNotFoundAdmin, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.TsigkeyClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.TsigkeyClient()

    @decorators.idempotent_id('824c9b49-edc5-4282-929e-467a158d23e4')
    def test_show_tsigkey_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.show_tsigkey,
                              data_utils.rand_uuid())
        self.assertTsigkey404(e.resp, e.resp_body)

    @decorators.idempotent_id('4ef3493a-ee66-4c62-b070-c57fa9568b69')
    def test_update_tsigkey_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.update_tsigkey,
                              data_utils.rand_uuid())
        self.assertTsigkey404(e.resp, e.resp_body)

    @decorators.idempotent_id('ba438ede-4823-4922-8f4c-8de278f3d454')
    def test_delete_tsigkey_404(self):
        e = self.assertRaises(lib_exc.NotFound,
                              self.admin_client.delete_tsigkey,
                              data_utils.rand_uuid())
        self.assertTsigkey404(e.resp, e.resp_body)

    def assertTsigkey404(self, resp, resp_body):
        self.assertEqual(404, resp.status)
        self.assertEqual(404, resp_body['code'])
        self.assertEqual("tsigkey_not_found", resp_body['type'])
        self.assertEqual("Could not find TsigKey", resp_body['message'])


class TestTsigkeyInvalidIdAdmin(BaseTsigkeyTest):

    credentials = ["admin", "primary", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(TestTsigkeyInvalidIdAdmin, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(TestTsigkeyInvalidIdAdmin, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.TsigkeyClient()
            cls.pool_admin_client = cls.os_system_admin.dns_v2.PoolClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.TsigkeyClient()
            cls.pool_admin_client = cls.os_admin.dns_v2.PoolClient()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()

    @decorators.idempotent_id('2a8dfc75-9884-4b1c-8f1f-ed835d96f2fe')
    def test_show_tsigkey_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.show_tsigkey,
                              'foo')
        self.assertTsigkeyInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('2befa10f-fc42-4ae9-9276-672e23f045f2')
    def test_update_tsigkey_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.update_tsigkey,
                              'foo')
        self.assertTsigkeyInvalidId(e.resp, e.resp_body)

    @decorators.idempotent_id('55c2fea0-ead6-44c7-8bb1-05111412afdd')
    def test_delete_tsigkey_invalid_uuid(self):
        e = self.assertRaises(lib_exc.BadRequest,
                              self.admin_client.delete_tsigkey,
                              'foo')
        self.assertTsigkeyInvalidId(e.resp, e.resp_body)

    def assertTsigkeyInvalidId(self, resp, resp_body):
        self.assertEqual(400, resp.status)
        self.assertEqual(400, resp_body['code'])
        self.assertEqual("invalid_uuid", resp_body['type'])
        self.assertEqual("Invalid UUID tsigkey_id: foo",
                         resp_body['message'])

    @decorators.idempotent_id('f94af13a-d743-11eb-beba-74e5f9e2a801')
    def test_create_tsigkey_for_zone_invalid_algorithm(self):
        zone_name = dns_data_utils.rand_zone_name(
            name="create_tsigkey_invalid_algo", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        tsigkey_data = {
                        "name": dns_data_utils.rand_zone_name('Example_Key'),
                        "algorithm": "zababun",
                        "secret": "SomeSecretKey",
                        "scope": "ZONE",
                        "resource_id": zone['id']}
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.admin_client.create_tsigkey,
            tsigkey_data['resource_id'],
            tsigkey_data['name'], tsigkey_data['algorithm'],
            tsigkey_data['secret'], tsigkey_data['scope'])

    @decorators.idempotent_id('4df903d8-d745-11eb-beba-74e5f9e2a801')
    def test_create_tsigkey_for_zone_invalid_name(self):
        LOG.info('Create a zone resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_tsigkey_invalid_name", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        tsigkey_data = {
                        "name": dns_data_utils.rand_zone_name(
                            'Example_Key') * 1000,
                        "algorithm": "hmac-sha256",
                        "secret": "SomeSecretKey",
                        "scope": "ZONE",
                        "resource_id": zone['id']}
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.admin_client.create_tsigkey,
            tsigkey_data['resource_id'],
            tsigkey_data['name'], tsigkey_data['algorithm'],
            tsigkey_data['secret'], tsigkey_data['scope'])

    @decorators.idempotent_id('5d6b8a84-d745-11eb-beba-74e5f9e2a801')
    @decorators.skip_because(bug="1933760")
    def test_create_tsigkey_for_zone_empty_secret(self):
        LOG.info('Create a zone resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_tsigkey_empty_secret", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        tsigkey_data = {
                        "name": dns_data_utils.rand_zone_name('Example_Key'),
                        "algorithm": "hmac-sha256",
                        "secret": '',
                        "scope": "ZONE",
                        "resource_id": zone['id']}
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.admin_client.create_tsigkey,
            tsigkey_data['resource_id'],
            tsigkey_data['name'], tsigkey_data['algorithm'],
            tsigkey_data['secret'], tsigkey_data['scope'])

    @decorators.idempotent_id('dfca9268-d745-11eb-beba-74e5f9e2a801')
    def test_create_tsigkey_for_zone_invalid_scope(self):
        LOG.info('Create a zone resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_tsigkey_invalid_scope", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        tsigkey_data = {
                        "name": dns_data_utils.rand_zone_name('Example_Key'),
                        "algorithm": "hmac-sha256",
                        "secret": "SomeSecretKey",
                        "scope": "zababun",
                        "resource_id": zone['id']}
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.admin_client.create_tsigkey,
            tsigkey_data['resource_id'],
            tsigkey_data['name'], tsigkey_data['algorithm'],
            tsigkey_data['secret'], tsigkey_data['scope'])

    @decorators.idempotent_id('57255858-d74a-11eb-beba-74e5f9e2a801')
    def test_create_tsigkey_for_zone_invalid_zone_id(self):
        LOG.info('Create a resource')
        zone_name = dns_data_utils.rand_zone_name(
            name="create_tsigkey_invalide_zone_id", suffix=self.tld_name)
        zone = self.zone_client.create_zone(name=zone_name)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])
        tsigkey_data = {
                        "name": dns_data_utils.rand_zone_name('Example_Key'),
                        "algorithm": "hmac-sha256",
                        "secret": "SomeSecretKey",
                        "scope": "ZONE",
                        "resource_id": data_utils.rand_uuid}
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.admin_client.create_tsigkey,
            tsigkey_data['resource_id'],
            tsigkey_data['name'], tsigkey_data['algorithm'],
            tsigkey_data['secret'], tsigkey_data['scope'])

    @decorators.idempotent_id('0dfbc2f8-d8bb-11eb-b95a-74e5f9e2a801')
    @decorators.skip_because(bug="1934120")
    def test_create_tsigkey_for_pool_with_scope_zone(self):
        pool = self.pool_admin_client.create_pool()[1]
        self.addCleanup(self.pool_admin_client.delete_pool, pool['id'])

        LOG.info('Try to create a tsigkey using pool ID and "scope:ZONE", '
                 'should fail because ID is for pool, but scope is ZONE')
        self.assertRaisesDns(
            lib_exc.BadRequest, 'invalid_object', 400,
            self.admin_client.create_tsigkey,
            resource_id=pool['id'], scope='ZONE')
