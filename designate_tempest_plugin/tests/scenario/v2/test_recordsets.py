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
import testtools

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.common import waiters
from designate_tempest_plugin.services.dns.query.query_client import (
    SingleQueryClient)

LOG = logging.getLogger(__name__)

CONF = config.CONF


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
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()

    @classmethod
    def resource_setup(cls):
        super(RecordsetsTest, cls).resource_setup()

        zone_id = CONF.dns.zone_id
        if zone_id:
            LOG.info('Retrieve info from a zone')
            zone = cls.zones_client.show_zone(zone_id)[1]
        else:
            # Make sure we have an allowed TLD available
            tld_name = dns_data_utils.rand_zone_name(name="RecordsetsTest")
            cls.tld_name = f".{tld_name}"
            cls.class_tld = cls.admin_tld_client.create_tld(
                tld_name=tld_name[:-1])
            LOG.info('Create a new zone')
            zone_name = dns_data_utils.rand_zone_name(
                name="recordsets_test_setup", suffix=cls.tld_name)
            zone = cls.zones_client.create_zone(name=zone_name)[1]
            cls.addClassResourceCleanup(
                test_utils.call_and_ignore_notfound_exc,
                cls.zones_client.delete_zone, zone['id'])

        LOG.info('Ensure we respond with ACTIVE')
        waiters.wait_for_zone_status(cls.zones_client, zone['id'], 'ACTIVE')

        cls.zone = zone

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(RecordsetsTest, cls).resource_cleanup()

    def _test_create_and_delete_records_on_existing_zone(
            self, name, type, records):
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

        LOG.info('Wait until the recordset is active and propagated')
        waiters.wait_for_recordset_status(self.recordset_client,
                                          self.zone['id'], recordset['id'],
                                          'ACTIVE')
        waiters.wait_for_query(
            self.query_client, recordset_data['name'], type)

        LOG.info('Delete the recordset')
        body = self.recordset_client.delete_recordset(
            self.zone['id'], recordset['id'])[1]

        LOG.info('Ensure we respond with DELETE+PENDING')
        self.assertEqual('DELETE', body['action'])
        self.assertEqual('PENDING', body['status'])

        LOG.info('Ensure successful deletion of Recordset from:'
                 ' Designate and Backends')
        self.assertRaises(lib_exc.NotFound,
                          lambda: self.recordset_client.show_recordset(
                              self.zone['id'], recordset['id']))
        waiters.wait_for_query(
            self.query_client, recordset_data['name'], type, found=False)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('4664ed66-9ff1-45f2-9e60-d4913195c505')
    def test_create_and_delete_records_on_existing_zone_01_A(self):
        self._test_create_and_delete_records_on_existing_zone(
            "www", "A", ["192.0.2.1", "192.0.2.2", "192.0.2.3"])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('cecd9f20-0b62-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_02_AAAA(self):
        self._test_create_and_delete_records_on_existing_zone(
            "www", "AAAA", ["2001:db8::1", "2001:db8::1", "2001:db8::"])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('f5368d7a-0b62-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_03_SRV(self):
        self._test_create_and_delete_records_on_existing_zone(
            "_sip._tcp", "SRV", ["10 60 5060 server1.example.com.",
                    "20 60 5060 server2.example.com.",
                    "20 30 5060 server3.example.com."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('74ff9efc-0b63-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_04_SRV(self):
        self._test_create_and_delete_records_on_existing_zone(
            "_sip._udp", "SRV", ["10 60 5060 server1.example.com.",
                    "10 60 5060 server2.example.com.",
                    "20 30 5060 server3.example.com."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('82a14a2e-0b63-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_05_CNAME(self):
        self._test_create_and_delete_records_on_existing_zone(
            "alias-of-target", "CNAME", ["target.example.org."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('ae7a295e-0b63-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_06_MX(self):
        self._test_create_and_delete_records_on_existing_zone(
            None, "MX", ["10 mail1.example.org.",
                    "20 mail2.example.org."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('f9aa8512-0b64-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_07_MX(self):
        self._test_create_and_delete_records_on_existing_zone(
            "under", "MX", ["10 mail.example.org."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('fa6cbd12-0b64-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_08_SSHFP(self):
        self._test_create_and_delete_records_on_existing_zone(
            "www", "SSHFP", ["2 1 123456789abcdef67890123456789abcdef67890"])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('fa124a1c-0b64-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_09_TXT(self):
        self._test_create_and_delete_records_on_existing_zone(
            "www", "TXT", ["\"Any Old Text Goes Here\""])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('3e347c28-0b66-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_10_SPF(self):
        self._test_create_and_delete_records_on_existing_zone(
            "*.sub", "SPF", ["\"v=spf1; a -all\""])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('88f6c2ac-0b66-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_11_PTR(self):
        self._test_create_and_delete_records_on_existing_zone(
            "PTR_Record_IPV4", "PTR", ["34.216.184.93.in-addr.arpa."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('b9591eea-0b66-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_12_PTR(self):
        self._test_create_and_delete_records_on_existing_zone(
            "PTR_Record_IPV6", "PTR",
            ["6.4.9.1.8.c.5.2.3.9.8.1.8.4.2.0.1.0.0.0.0.2.2.0.0.0.8"
             ".2.6.0.6.2.ip6.arpa."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('c98cd9b4-0b66-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_13_CAA(self):
        self._test_create_and_delete_records_on_existing_zone(
            "CAA_Record", "CAA", ["0 issue letsencrypt.org"])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('f78d6e8c-0b66-11ee-bbcc-201e8823901f')
    def test_create_and_delete_records_on_existing_zone_14_NAPTR(self):
        self._test_create_and_delete_records_on_existing_zone(
            "NAPTR_Record", "NAPTR",
            ["0 0 S SIP+D2U !^.*$!sip:customer-service@example"
             ".com! _sip._udp.example.com."])

    @testtools.skipUnless(
        config.CONF.dns.nameservers,
        "Config option dns.nameservers is missing or empty")
    def _test_update_records_propagated_to_backends(self, name, type, records):
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

    # These tests were unrolled from DDT to allow accurate tracking by
    # idempotent_id's. The naming convention for the tests has been preserved.
    @decorators.attr(type='slow')
    @decorators.idempotent_id('cbf756b0-ba64-11ec-93d4-201e8823901f')
    def test_update_records_propagated_to_backends_01_A(self):
        self._test_update_records_propagated_to_backends(
            "www", "A", ["192.0.2.1", "192.0.2.2", "192.0.2.3"])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('258f7f57-9a74-4e72-bbfb-c709c411af14')
    def test_update_records_propagated_to_backends_02_AAAA(self):
        self._test_update_records_propagated_to_backends(
            "www", "AAAA", ["2001:db8::1", "2001:db8::1", "2001:db8::"])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('304adbc5-668a-457e-9496-8efd20b8ae82')
    def test_update_records_propagated_to_backends_03_SRV_TCP(self):
        self._test_update_records_propagated_to_backends(
            "_sip._tcp", "SRV", ["10 60 5060 server1.example.com.",
                                 "20 60 5060 server2.example.com.",
                                 "20 30 5060 server3.example.com."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('bd1283b3-423c-4bb9-8c4f-a205f31f1c2d')
    def test_update_records_propagated_to_backends_04_SRV_UDP(self):
        self._test_update_records_propagated_to_backends(
            "_sip._udp", "SRV", ["10 60 5060 server1.example.com.",
                                 "10 60 5060 server2.example.com.",
                                 "20 30 5060 server3.example.com."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('8b53ae20-d096-4651-a6cf-efd7c98ae8d1')
    def test_update_records_propagated_to_backends_05_CNAME(self):
        self._test_update_records_propagated_to_backends(
            "alias-of-target", "CNAME", ["target.example.org."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('0fd0046a-ac5a-468d-94b3-8a6bde790589')
    def test_update_records_propagated_to_backends_06_MX_at_APEX(self):
        self._test_update_records_propagated_to_backends(
            None, "MX", ["10 mail1.example.org.",
                         "20 mail2.example.org."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('31176def-3f95-459d-8bdd-b9994335b2d9')
    def test_update_records_propagated_to_backends_07_MX_under_APEX(self):
        self._test_update_records_propagated_to_backends(
            "under", "MX", ["10 mail.example.org."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('0009d787-c590-4149-9f30-082195326fad')
    def test_update_records_propagated_to_backends_08_SSHFP(self):
        self._test_update_records_propagated_to_backends(
            "www", "SSHFP", ["2 1 123456789abcdef67890123456789abcdef67890"])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('af7cec16-dfad-4071-aa05-cafa60bf12a5')
    def test_update_records_propagated_to_backends_09_TXT(self):
        self._test_update_records_propagated_to_backends(
            "www", "TXT", ["\"Any Old Text Goes Here\""])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('b3fd1f77-c318-4ab0-b18d-34611e51e9e4')
    def test_update_records_propagated_to_backends_10_SPF(self):
        self._test_update_records_propagated_to_backends(
            "*.sub", "SPF", ["\"v=spf1; a -all\""])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('c310b94b-f3a5-4d26-bab6-2529e6f29fbf')
    def test_update_records_propagated_to_backends_11_PTR_IPV4(self):
        self._test_update_records_propagated_to_backends(
            "PTR_Record_IPV4", "PTR", ["34.216.184.93.in-addr.arpa."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('3e31e406-621f-4f89-b401-b6f38aa63347')
    def test_update_records_propagated_to_backends_12_PTR_IPV6(self):
        self._test_update_records_propagated_to_backends(
            "PTR_Record_IPV6", "PTR",
            ["6.4.9.1.8.c.5.2.3.9.8.1.8.4.2.0.1.0.0.0.0.2.2.0.0.0.8.2.6.0.6.2"
             ".ip6.arpa."])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('6fd96280-fb62-4eaf-81f9-609cdb7c126e')
    def test_update_records_propagated_to_backends_13_CAA_Record(self):
        self._test_update_records_propagated_to_backends(
            "CAA_Record", "CAA", ["0 issue letsencrypt.org"])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('45a11efe-bee3-4896-ab7c-daee1cb5eb3a')
    def test_update_records_propagated_to_backends_14_NAPTR_Record(self):
        self._test_update_records_propagated_to_backends(
            "NAPTR_Record", "NAPTR",
            ["0 0 S SIP+D2U !^.*$!sip:customer-service@example.com! "
             "_sip._udp.example.com."])
