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

import time

from oslo_log import log as logging
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
import ddt

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.services.dns.query.query_client \
    import SingleQueryClient

LOG = logging.getLogger(__name__)

CONF = config.CONF


@ddt.ddt
class RecordsetsTest(base.BaseDnsV2Test):

    credentials = ["admin", "system_admin", "primary"]

    @classmethod
    def setup_clients(cls):
        super(RecordsetsTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.RecordsetClient()
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.RecordsetClient()
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
        cls.client = cls.os_primary.dns_v2.ZonesClient()
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()

    @classmethod
    def resource_setup(cls):
        super(RecordsetsTest, cls).resource_setup()

        zone_id = CONF.dns.zone_id
        if zone_id:
            LOG.info('Retrieve info from a zone')
            zone = cls.client.show_zone(zone_id)[1]
        else:
            # Make sure we have an allowed TLD available
            tld_name = dns_data_utils.rand_zone_name(name="RecordsetsTest")
            cls.tld_name = f".{tld_name}"
            cls.class_tld = cls.admin_tld_client.create_tld(
                tld_name=tld_name[:-1])
            LOG.info('Create a new zone')
            zone_name = dns_data_utils.rand_zone_name(
                name="recordsets_test_setup", suffix=cls.tld_name)
            zone = cls.client.create_zone(name=zone_name)[1]
            cls.addClassResourceCleanup(
                test_utils.call_and_ignore_notfound_exc,
                cls.client.delete_zone, zone['id'])

        LOG.info('Ensure we respond with ACTIVE')
        waiters.wait_for_zone_status(cls.client, zone['id'], 'ACTIVE')

        cls.zone = zone

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(RecordsetsTest, cls).resource_cleanup()

    @decorators.attr(type='slow')
    @decorators.idempotent_id('4664ed66-9ff1-45f2-9e60-d4913195c505')
    @ddt.file_data("recordset_data.json")
    def test_create_and_delete_records_on_existing_zone(self, name,
                                                        type, records):
        if name is not None:
            recordset_name = name + "." + self.zone['name']

        else:
            recordset_name = self.zone['name']

        recordset_data = {
            'name': recordset_name,
            'type': type,
            'records': records,
        }

        LOG.info('Create a Recordset on the existing zone')
        recordset = self.recordset_client.create_recordset(
            self.zone['id'], recordset_data)[1]
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.recordset_client.delete_recordset,
                        self.zone['id'], recordset['id'])

        LOG.info('Ensure we respond with PENDING')
        self.assertEqual('PENDING', recordset['status'])

        LOG.info('Wait until the recordset is active')
        waiters.wait_for_recordset_status(self.recordset_client,
                                          self.zone['id'], recordset['id'],
                                          'ACTIVE')

        LOG.info('Delete the recordset')
        body = self.recordset_client.delete_recordset(
            self.zone['id'], recordset['id'])[1]

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual('DELETE', body['action'])
        self.assertEqual('PENDING', body['status'])

        LOG.info('Ensure successful deletion of Recordset')
        self.assertRaises(lib_exc.NotFound,
                          lambda: self.recordset_client.show_recordset(
                              self.zone['id'], recordset['id']))

    @decorators.attr(type='slow')
    @decorators.idempotent_id('cbf756b0-ba64-11ec-93d4-201e8823901f')
    @ddt.file_data("recordset_data.json")
    def test_update_records_propagated_to_backends(self, name, type, records):
        if name:
            recordset_name = name + "." + self.zone['name']
        else:
            recordset_name = self.zone['name']

        orig_ttl = 666
        updated_ttl = 777
        recordset_data = {
            'name': recordset_name,
            'type': type,
            'records': records,
            'ttl': orig_ttl
        }

        LOG.info('Create a Recordset on the existing zone')
        recordset = self.recordset_client.create_recordset(
            self.zone['id'], recordset_data, wait_until=const.ACTIVE)[1]
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.recordset_client.delete_recordset,
                        self.zone['id'], recordset['id'])

        LOG.info('Update a Recordset on the existing zone')
        recordset_data['ttl'] = updated_ttl
        self.recordset_client.update_recordset(
            self.zone['id'], recordset['id'],
            recordset_data, wait_until=const.ACTIVE)

        LOG.info('Per Nameserver "dig" for a record until either:'
                 ' updated TTL is detected or build timeout has reached')
        for ns in config.CONF.dns.nameservers:
            start = time.time()
            while True:
                ns_obj = SingleQueryClient(ns, config.CONF.dns.query_timeout)
                ns_record = ns_obj.query(
                    self.zone['name'], rdatatype=recordset_data['type'])
                if str(updated_ttl) in str(ns_record):
                    return
                if time.time() - start >= config.CONF.dns.build_timeout:
                    raise lib_exc.TimeoutException(
                        'Failed, updated TTL:{} for the record was not'
                        ' detected on Nameserver:{} within a timeout of:{}'
                        ' seconds.'.format(
                            updated_ttl, ns, config.CONF.dns.build_timeout))
