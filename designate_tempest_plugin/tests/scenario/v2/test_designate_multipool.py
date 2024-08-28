# Copyright 2024 Red Hat
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
import os
import random

import testtools
import yaml
from oslo_log import log as logging
from tempest import config
import subprocess

from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.tests import resources
from designate_tempest_plugin.services.dns.query.query_client import (
    SingleQueryClient)

CONF = config.CONF
LOG = logging.getLogger(__name__)


class DesignateManageTest(base.BaseDnsV2Test):
    credentials = ["admin", 'primary', 'system_admin']
    managed_resource = None

    @classmethod
    def skip_checks(cls) -> None:
        super().skip_checks()
        if CONF.dns_feature_enabled.designate_manage_path:
            cls.designate_manage_cmd = (
                CONF.dns_feature_enabled.designate_manage_path)
        else:
            raise cls.skipException('designate-manage path was not found. '
                                    'Skipping this test class')

    @classmethod
    def _run_designate_manage_command(cls,
                                      managed_resource: str,
                                      command: str,
                                      *args) -> str:
        """Runs the designate-manage command with the provided arguments.

        :param managed_resource: (str): The resource managed by the
         designate-manage command. For example: pool
        :param command: (str): The command to run. For example: update
        :return: The command output
        """
        managed_resource = managed_resource or cls.managed_resource

        commands_list = [cls.designate_manage_cmd, managed_resource]
        if command and isinstance(command, tuple):
            commands_list.extend(command)
        else:
            commands_list.append(command)
        if args and isinstance(args, tuple):
            commands_list.extend(args[0])
        try:
            output = subprocess.check_output(commands_list,
                    stderr=subprocess.STDOUT,
                    text=True)
            return output
        except subprocess.CalledProcessError as e:
            LOG.error(e.output)


def _get_pools_path(name: str) -> str:
    return os.path.join(resources.path, 'pools_yaml', name)


@testtools.skipUnless(CONF.dns_feature_enabled.test_multipool_with_delete_opt,
                      'Multipools feature is being tested with --delete '
                      'option. It might delete pools that were created in '
                      'other tests.')
class DesignateManagePoolTest(DesignateManageTest):
    managed_resource = 'pool'
    file_attributes_to_num_of_appearances = {  # per each Pool
        'also_notifies:': 1, 'attributes:': 1, 'description:': 2, 'id:': 1,
        'name:': 2, 'nameservers:': 1, 'ns_records:': 1, 'targets:': 1
    }
    MULTIPOOLS_FILE_PATH = "/etc/designate/multiple-pools.yaml"

    @classmethod
    def resource_setup(cls):
        testtools.skipUnless(os.path.exists(cls.MULTIPOOLS_FILE_PATH),
        f"multiple-pools configuration file {cls.MULTIPOOLS_FILE_PATH} was "
        "not found, skipping the test")
        cls._update_pools_file(cls.MULTIPOOLS_FILE_PATH)

    @classmethod
    def _update_pools_file(cls, pools_file_path):
        if not pools_file_path.startswith('/'):
            pools_file_path = _get_pools_path(name=pools_file_path)
        cls._run_designate_manage_pool_command(
            'update',
            '--file',
            pools_file_path,
            '--delete')

    def tearDown(self):
        super(DesignateManagePoolTest, self).tearDown()
        self._update_pools_file(self.MULTIPOOLS_FILE_PATH)

    @staticmethod
    def _load_config(filename) -> str:
        with open(filename) as stream:
            return yaml.safe_load(stream)

    @classmethod
    def _run_designate_manage_pool_command(cls, command: str, *args) -> str:
        return super(
            DesignateManagePoolTest, cls)._run_designate_manage_command(
            'pool', command, args)

    @decorators.idempotent_id('ed42f367-e5ba-40d7-a08d-366ad787d21d')
    def test_pool_show_config(self):
        self._update_pools_file(self.MULTIPOOLS_FILE_PATH)
        pool_config = self._run_designate_manage_pool_command(
            command='show_config').split('\n\n')[0]
        self.assertIn('BIND Pool', pool_config)

    @decorators.idempotent_id('ed42f367-e5ba-40d7-a08d-366ad787d21e')
    def test_pool_show_config_all(self):
        self._update_pools_file(pools_file_path='multiple-pools.yaml')
        pool_config = self._run_designate_manage_pool_command(
            'show_config', '--all').split('\n\n')[0]

        pool_config_list = pool_config.split('\n')

        for attribute in self.file_attributes_to_num_of_appearances:
            num_of_occurrences = sum(attribute in s for s in pool_config_list)
            file_attributes_to_num_of_appearances = {
                'also_notifies:': 2, 'attributes:': 2, 'description:': 4,
                'id:': 2, 'name:': 7, 'nameservers:': 2, 'ns_records:': 2,
                'targets:': 2
            }
            err_msg = (f'{attribute} was supposed to appear '
                       f'{file_attributes_to_num_of_appearances[attribute]} '
                       'times on the designate-manage output, but '
                       f'it appeared {num_of_occurrences} times.')
            self.assertEqual(
                file_attributes_to_num_of_appearances[attribute],
                num_of_occurrences, err_msg)

    @decorators.idempotent_id('ed42f367-e5ba-40d7-a08d-366ad787d220')
    def test_pool_update_multiple_pools_without_delete(self):

        # Updating to multiple-pools.yaml with --delete
        self._update_pools_file(pools_file_path='multiple-pools.yaml')

        # Updating to other-pools.yaml without --delete. There should be 5
        # pools after the update
        pools_yaml_path = _get_pools_path(name='other-pools.yaml')
        self._run_designate_manage_pool_command(
            'update',
            '--file',
            pools_yaml_path,
        )

        pool_config = self._run_designate_manage_pool_command(
            'show_config', '--all').split('\n\n')[0]

        pool_config_list = pool_config.split('\n')
        for attribute in self.file_attributes_to_num_of_appearances:
            num_of_occurrences = sum(attribute in s for s in pool_config_list)
            file_attributes_to_num_of_appearances = {
                'also_notifies:': 3, 'attributes:': 3, 'description:': 6,
                'id:': 3, 'name:': 11, 'nameservers:': 3, 'ns_records:': 3,
                'targets:': 3
            }
            err_msg = (f'{attribute} was supposed to appear '
                       f'{file_attributes_to_num_of_appearances[attribute]} '
                       'times on the designate-manage output, but '
                       f'it appeared {num_of_occurrences} times.')
            self.assertEqual(
                file_attributes_to_num_of_appearances[attribute],
                num_of_occurrences, err_msg)

    @decorators.idempotent_id('ed42f367-e5ba-40d7-a08d-366ad787d223')
    def test_pool_update_multiple_pools_dry_run(self):
        self._update_pools_file(pools_file_path='multiple-pools.yaml')

        pools_yaml_path = _get_pools_path(name='other-pools.yaml')
        self._run_designate_manage_pool_command(
            'update',
            '--file',
            pools_yaml_path,
            '--dry-run'
        )

        pool_config = self._run_designate_manage_pool_command(
            'show_config', '--all').split('\n\n')[0]

        pool_config_list = pool_config.split('\n')

        for attribute in self.file_attributes_to_num_of_appearances:
            num_of_occurrences = sum(attribute in s for s in pool_config_list)
            file_attributes_to_num_of_appearances = {
                'also_notifies:': 2, 'attributes:': 2, 'description:': 4,
                'id:': 2, 'name:': 7, 'nameservers:': 2, 'ns_records:': 2,
                'targets:': 2
            }
            err_msg = (f'{attribute} was supposed to appear '
                       f'{file_attributes_to_num_of_appearances[attribute]} '
                       'times on the designate-manage output, but '
                       f'it appeared {num_of_occurrences} times.')
            self.assertEqual(
                file_attributes_to_num_of_appearances[attribute],
                num_of_occurrences, err_msg)

    @decorators.idempotent_id('ed42f367-e5ba-40d7-a08d-366ad787d224')
    def test_pool_generate_file(self):
        temp_pools_yaml_conf_path = '/tmp/pools_tempest.yaml'
        if os.path.exists(temp_pools_yaml_conf_path):
            LOG.debug(f'Temporary pools.yaml file {temp_pools_yaml_conf_path} '
                      'exists.\nRemoving this file so we could continue '
                      'testing')
            os.remove(temp_pools_yaml_conf_path)
        self._run_designate_manage_pool_command('generate_file',
                                                '--file',
                                                temp_pools_yaml_conf_path)
        self.assertTrue(os.path.exists(path=temp_pools_yaml_conf_path))
        # (At least) the default pool config should be written to the file
        pools_conf = self._load_config(filename=temp_pools_yaml_conf_path)
        if len(pools_conf) > 1:
            pool_idx = random.randint(0, len(pools_conf) - 1)
        else:
            pool_idx = 0
        pool = yaml.safe_dump(pools_conf[pool_idx]).split('\n')

        for attribute in self.file_attributes_to_num_of_appearances:
            self.assertTrue(
                any(attribute in s for s in pool),
                f'{attribute} not in {pool}'
            )
        if os.path.exists(temp_pools_yaml_conf_path):
            os.remove(temp_pools_yaml_conf_path)


@testtools.skipUnless(CONF.dns_feature_enabled.test_multipool_with_delete_opt,
                      'Multipools feature is being tested with --delete '
                      'option. It might delete pools that were created in '
                      'other tests.')
class DesignateMultiPoolTest(DesignateManagePoolTest):

    _pool1_id = None
    _pool2_id = None

    @property
    def pool1_id(self):
        if not self._pool1_id:
            self._set_pool_ids()
        return self._pool1_id

    @property
    def pool2_id(self):
        if not self._pool2_id:
            self._set_pool_ids()
        return self._pool2_id

    def _set_pool_ids(self):
        pool_config = self._run_designate_manage_pool_command(
            'show_config', '--all').split('\n\n')[0]
        pool_config_list = pool_config.split('\n')
        pool_ids = list()
        for item in pool_config_list:
            if 'id:' in item:
                id = item.split()[1]
                pool_ids.append(id)
        if len(pool_ids) < 2:
            self.skipException('Multipool tests require at least 2 pools.')
        self._pool1_id = pool_ids[0]
        self._pool2_id = pool_ids[1]

    @classmethod
    def setup_clients(cls):
        super(DesignateMultiPoolTest, cls).setup_clients()
        cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
        cls.rec_client = cls.os_admin.dns_v2.RecordsetClient()
        cls.admin_zones_client = cls.os_admin.dns_v2.ZonesClient()

    @classmethod
    def resource_setup(cls):
        super().resource_setup()
        super()._update_pools_file(cls.MULTIPOOLS_FILE_PATH)
        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="ZonesTest")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    def tearDown(self):
        super().tearDown()
        super()._update_pools_file(self.MULTIPOOLS_FILE_PATH)

    @classmethod
    def resource_cleanup(cls):
        super().resource_cleanup()
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])

    @decorators.attr(type='smoke')
    @decorators.attr(type='slow')
    @decorators.idempotent_id('c0648f53-4114-45bd-8792-462a82f69d32')
    def test_create_zones(self):
        LOG.info('Create 2 zones, one per pool')

        zone1_name = dns_data_utils.rand_zone_name(
            name="create_zones_multipool-",
            suffix=self.tld_name)

        zone1 = self.admin_zones_client.create_zone(
            name=f"{zone1_name}",
            attributes={'pool_id': f'{self.pool1_id}'})[1]
        self.addCleanup(self.wait_zone_delete,
                        self.admin_zones_client, zone1['id'],
                        ignore_errors=lib_exc.NotFound)

        zone2_name = dns_data_utils.rand_zone_name(
            name="create_zones_multipool-",
            suffix=self.tld_name)

        zone2 = self.admin_zones_client.create_zone(
            name=f"{zone2_name}",
            attributes={'pool_id': f'{self.pool2_id}'})[1]
        self.addCleanup(self.wait_zone_delete,
                        self.admin_zones_client,
                        zone2['id'],
                        ignore_errors=lib_exc.NotFound)

        self.assertNotEqual(zone1['pool_id'], zone2['pool_id'])

        # wait for both of them to be active
        for zone in [zone1, zone2]:
            waiters.wait_for_zone_status(
                self.admin_zones_client, zone['id'], const.ACTIVE)

            # Create a type A recordset for each zone
            recordset_data = dns_data_utils.rand_recordset_data(
                record_type='A', zone_name=zone['name'])
            body = self.rec_client.create_recordset(zone['id'],
            recordset_data)[1]
            self.addCleanup(
                self.wait_recordset_delete, self.rec_client,
                zone['id'], body['id'])
            self.assertEqual(const.PENDING, body['status'],
                            'Failed, expected status is PENDING')
            waiters.wait_for_recordset_status(
                self.rec_client, zone['id'],
                body['id'], const.ACTIVE)

            for ns in config.CONF.dns.nameservers:
                ns_obj = SingleQueryClient(ns, config.CONF.dns.query_timeout)
                a_record = str(ns_obj.query(zone['name'], rdatatype='A'))
                self.assertNotEmpty(a_record)
