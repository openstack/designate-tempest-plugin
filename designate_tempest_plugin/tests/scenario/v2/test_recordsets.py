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
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
import ddt

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import waiters


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
        else:
            cls.admin_client = cls.os_admin.dns_v2.RecordsetClient()
        cls.client = cls.os_primary.dns_v2.ZonesClient()
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()

    @classmethod
    def resource_setup(cls):
        super(RecordsetsTest, cls).resource_setup()

        zone_id = CONF.dns.zone_id
        if zone_id:
            LOG.info('Retrieve info from a zone')
            _, zone = cls.client.show_zone(zone_id)
        else:
            LOG.info('Create a new zone')
            _, zone = cls.client.create_zone()
            cls.addClassResourceCleanup(
                test_utils.call_and_ignore_notfound_exc,
                cls.client.delete_zone, zone['id'])

        LOG.info('Ensure we respond with ACTIVE')
        waiters.wait_for_zone_status(cls.client, zone['id'], 'ACTIVE')

        cls.zone = zone

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
        _, recordset = self.recordset_client.create_recordset(
            self.zone['id'], recordset_data)
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
        _, body = self.recordset_client.delete_recordset(self.zone['id'],
                                                         recordset['id'])

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual('DELETE', body['action'])
        self.assertEqual('PENDING', body['status'])

        LOG.info('Ensure successful deletion of Recordset')
        self.assertRaises(lib_exc.NotFound,
                          lambda: self.recordset_client.show_recordset(
                              self.zone['id'], recordset['id']))

    @decorators.idempotent_id('1e78a742-66ee-11ec-8dc3-201e8823901f')
    def test_create_soa_record_not_permitted(self):
        # SOA record is automatically created for a zone, no user
        # should be able to create a SOA record.
        soa_record = ("s1.devstack.org. admin.example.net. 1510721487 3510"
                      " 600 86400 3600")
        LOG.info('Primary tries to create a Recordset on '
                 'the existing zone')
        self.assertRaises(
            lib_exc.BadRequest,
            self.recordset_client.create_recordset,
            self.zone['id'], soa_record)
        LOG.info('Admin tries to create a Recordset on the existing zone')
        self.assertRaises(
            lib_exc.BadRequest,
            self.admin_client.create_recordset,
            self.zone['id'], soa_record)
