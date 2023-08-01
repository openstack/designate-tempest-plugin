# Copyright 2022 Red Hat.
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
import time

from oslo_utils import versionutils
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

from designate_tempest_plugin.tests import base
from designate_tempest_plugin.services.dns.query.query_client import (
    SingleQueryClient)

CONF = config.CONF


# This test suite is intended to test RFC 2317 classless in-addr.arpa
# delegation scenarios.
class ClasslessPTRTest(base.BaseDnsV2Test):

    credentials = ['primary', 'admin', 'system_admin', 'alt']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these tests.
        cls.set_network_resources()
        super(ClasslessPTRTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ClasslessPTRTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()
        cls.alt_rec_client = cls.os_alt.dns_v2.RecordsetClient()
        cls.share_zone_client = cls.os_primary.dns_v2.SharedZonesClient()

    @classmethod
    def resource_setup(cls):
        super(ClasslessPTRTest, cls).resource_setup()

        # Make sure we have an allowed TLD available
        cls.tld_name = '0.192.in-addr-arpa'
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=cls.tld_name)

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(ClasslessPTRTest, cls).resource_cleanup()

    @decorators.attr(type='slow')
    @decorators.idempotent_id('f2d9596c-ce87-4dfd-9bb4-ad2430fd3fe6')
    def test_classless_ptr_delegation(self):
        # Create full subnet zone
        zone_name = f'2.{self.tld_name}.'
        zone = self.zone_client.create_zone(name=zone_name,
                                            wait_until='ACTIVE')[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        # Create the delegated zone
        delegated_zone_name = f'1-3.2.{self.tld_name}.'
        delegated_zone = self.zone_client.create_zone(
            name=delegated_zone_name, wait_until='ACTIVE')[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client,
                        delegated_zone['id'], ignore_errors=lib_exc.NotFound)

        # Create the PTR record in the delegated zone
        ptr_recordset_data = {
            'name': f'1.1-3.2.{self.tld_name}.',
            'type': 'PTR',
            'records': ['www.example.org.']
        }
        ptr_recordset = self.recordset_client.create_recordset(
            delegated_zone['id'], ptr_recordset_data, wait_until='ACTIVE')[1]
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.recordset_client.delete_recordset,
                        delegated_zone['id'], ptr_recordset['id'])

        # Create the CNAME record
        cname_recordset_data = {
            'name': f'1.2.{self.tld_name}.',
            'type': 'CNAME',
            'records': [f'1.1-3.2.{self.tld_name}.']
        }
        cname_recordset = self.recordset_client.create_recordset(
            zone['id'], cname_recordset_data, wait_until='ACTIVE')[1]
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.recordset_client.delete_recordset,
                        zone['id'], cname_recordset['id'])

        # Check for a CNAME record
        if config.CONF.dns.nameservers:
            ns = config.CONF.dns.nameservers[0]
            start = time.time()
            while True:
                ns_obj = SingleQueryClient(ns, config.CONF.dns.query_timeout)
                ns_record = ns_obj.query(
                    cname_recordset['name'],
                    rdatatype=cname_recordset_data['type'])
                if cname_recordset_data['records'][0] in str(ns_record):
                    break
                if time.time() - start >= config.CONF.dns.build_timeout:
                    raise lib_exc.TimeoutException(
                        'Failed, CNAME record was not detected on '
                        'Nameserver:{} within a timeout of:{}'
                        ' seconds.'.format(ns, config.CONF.dns.build_timeout))

        # Check for a PTR record
        if config.CONF.dns.nameservers:
            ns = config.CONF.dns.nameservers[0]
            start = time.time()
            while True:
                ns_obj = SingleQueryClient(ns, config.CONF.dns.query_timeout)
                ns_record = ns_obj.query(
                    ptr_recordset['name'],
                    rdatatype=ptr_recordset_data['type'])
                if ptr_recordset_data['records'][0] in str(ns_record):
                    break
                if time.time() - start >= config.CONF.dns.build_timeout:
                    raise lib_exc.TimeoutException(
                        'Failed, PTR record was not detected on '
                        'Nameserver:{} within a timeout of:{}'
                        ' seconds.'.format(ns, config.CONF.dns.build_timeout))

    @decorators.attr(type='slow')
    @decorators.idempotent_id('0110e7b1-9582-410e-b3d5-bd38a1265222')
    def test_classless_ptr_delegation_shared_zone(self):

        if not versionutils.is_compatible('2.1', self.api_version,
                                          same_major=False):
            raise self.skipException(
                'Zone share tests require Designate API version 2.1 or newer. '
                'Skipping test_classless_ptr_delegation_shared_zone test.')

        # Create full subnet zone
        zone_name = f'2.{self.tld_name}.'
        zone = self.zone_client.create_zone(name=zone_name,
                                            wait_until='ACTIVE')[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'],
                        ignore_errors=lib_exc.NotFound)

        # Create the delegated zone
        delegated_zone_name = f'1-3.2.{self.tld_name}.'
        delegated_zone = self.zone_client.create_zone(
            name=delegated_zone_name, wait_until='ACTIVE')[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client,
                        delegated_zone['id'], ignore_errors=lib_exc.NotFound)

        # Create the CNAME record
        cname_recordset_data = {
            'name': f'1.2.{self.tld_name}.',
            'type': 'CNAME',
            'records': [f'1.1-3.2.{self.tld_name}.']
        }
        cname_recordset = self.recordset_client.create_recordset(
            zone['id'], cname_recordset_data, wait_until='ACTIVE')[1]
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.recordset_client.delete_recordset,
                        zone['id'], cname_recordset['id'])

        # Share the zone with the alt credential
        shared_zone = self.share_zone_client.create_zone_share(
            delegated_zone['id'], self.alt_rec_client.project_id)[1]
        self.addCleanup(self.share_zone_client.delete_zone_share,
                        delegated_zone['id'], shared_zone['id'])

        # Create the PTR record in the delegated zone as the alt project
        ptr_recordset_data = {
            'name': f'1.1-3.2.{self.tld_name}.',
            'type': 'PTR',
            'records': ['www.example.org.']
        }
        ptr_recordset = self.alt_rec_client.create_recordset(
            delegated_zone['id'], ptr_recordset_data, wait_until='ACTIVE')[1]
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.alt_rec_client.delete_recordset,
                        delegated_zone['id'], ptr_recordset['id'])

        # Check for a CNAME record
        if config.CONF.dns.nameservers:
            ns = config.CONF.dns.nameservers[0]
            start = time.time()
            while True:
                ns_obj = SingleQueryClient(ns, config.CONF.dns.query_timeout)
                ns_record = ns_obj.query(
                    cname_recordset['name'],
                    rdatatype=cname_recordset_data['type'])
                if cname_recordset_data['records'][0] in str(ns_record):
                    break
                if time.time() - start >= config.CONF.dns.build_timeout:
                    raise lib_exc.TimeoutException(
                        'Failed, CNAME record was not detected on '
                        'Nameserver:{} within a timeout of:{}'
                        ' seconds.'.format(ns, config.CONF.dns.build_timeout))

        # Check for a PTR record
        if config.CONF.dns.nameservers:
            ns = config.CONF.dns.nameservers[0]
            start = time.time()
            while True:
                ns_obj = SingleQueryClient(ns, config.CONF.dns.query_timeout)
                ns_record = ns_obj.query(
                    ptr_recordset['name'],
                    rdatatype=ptr_recordset_data['type'])
                if ptr_recordset_data['records'][0] in str(ns_record):
                    break
                if time.time() - start >= config.CONF.dns.build_timeout:
                    raise lib_exc.TimeoutException(
                        'Failed, PTR record was not detected on '
                        'Nameserver:{} within a timeout of:{}'
                        ' seconds.'.format(ns, config.CONF.dns.build_timeout))
