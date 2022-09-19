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
import random
from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc
from tempest.lib.common.utils import data_utils

import tempest.test

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils
from designate_tempest_plugin.common import constants as const
from designate_tempest_plugin.common import exceptions


LOG = logging.getLogger(__name__)


CONF = config.CONF


class QuotasV2Test(base.BaseDnsV2Test):

    credentials = ['primary', 'admin', 'system_admin', 'alt']
    test_quota_limit = 3

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(QuotasV2Test, cls).setup_credentials()

    @classmethod
    def skip_checks(cls):
        super(QuotasV2Test, cls).skip_checks()

        if not CONF.dns_feature_enabled.api_v2_quotas:
            skip_msg = ("%s skipped as designate V2 Quotas API is not "
                        "available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(QuotasV2Test, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.QuotasClient()
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.QuotasClient()
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()
        cls.quotas_client = cls.os_primary.dns_v2.QuotasClient()
        cls.alt_client = cls.os_alt.dns_v2.QuotasClient()
        cls.zone_client = cls.os_primary.dns_v2.ZonesClient()
        cls.alt_zone_client = cls.os_alt.dns_v2.ZonesClient()
        cls.recordset_client = cls.os_primary.dns_v2.RecordsetClient()

    @classmethod
    def resource_setup(cls):
        super(QuotasV2Test, cls).resource_setup()

        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="QuotasV2Test")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(QuotasV2Test, cls).resource_cleanup()

    def _set_quota_for_project(self, project_id, quotas):
        http_header = {'x-auth-sudo-project-id': project_id}
        self.admin_client.set_quotas(
            project_id=project_id, quotas=quotas, headers=http_header)
        self.addCleanup(
            self.admin_client.delete_quotas,
            project_id=project_id, headers=http_header)

    def _reach_quota_limit(
            self, limit_threshold, quota_type, zone=None):
        attempt_number = 0
        not_raised_msg = "Failed, expected '413 over_quota' response of " \
                         "type:{} wasn't received.".format(quota_type)
        while attempt_number <= limit_threshold + 1:
            try:
                attempt_number += 1
                LOG.info('Attempt No:{} '.format(attempt_number))
                if quota_type == 'zones_quota':
                    zone_name = dns_data_utils.rand_zone_name(
                        name="_reach_quota_limit", suffix=self.tld_name)
                    zone = self.zone_client.create_zone(
                        name=zone_name,
                        description='Test zone for:{}'.format(quota_type))[1]
                    self.addCleanup(
                        self.wait_zone_delete,
                        self.zone_client, zone['id'])
                else:
                    if quota_type == 'zone_recordsets':
                        max_number_of_records = 10
                        prj_quota = self.admin_client.show_quotas(
                            project_id=self.zone_client.project_id,
                            headers=self.all_projects_header)[1][
                            'zone_records']
                        if max_number_of_records > prj_quota:
                            max_number_of_records = prj_quota
                        recordset_data = dns_data_utils.rand_recordset_data(
                            record_type='A', zone_name=zone['name'],
                            number_of_records=random.randint(
                                1, max_number_of_records))
                    else:
                        recordset_data = dns_data_utils.rand_recordset_data(
                            record_type='A', zone_name=zone['name'])
                    recordset = self.recordset_client.create_recordset(
                        zone['id'], recordset_data=recordset_data,
                        wait_until=const.ACTIVE)[1]
                    self.addCleanup(
                        self.wait_recordset_delete,
                        self.recordset_client,
                        zone['id'], recordset['id'])
                self.assertLess(
                    attempt_number, limit_threshold + 1, not_raised_msg)
            except Exception as e:
                raised_err = str(e).replace(' ', '')
                if not_raised_msg in str(e):
                    raise AssertionError(not_raised_msg)
                elif "'code':413" in raised_err and \
                        "'type':'over_quota'" in raised_err:
                    LOG.info("OK, type':'over_quota' was raised")
                    break
                else:
                    raise

    @decorators.attr(type='slow')
    @decorators.idempotent_id('41d9cf2c-866a-11ec-8ccb-201e8823901f')
    @decorators.skip_because(bug="1960495")
    def test_api_export_size_quota(self):
        LOG.info('Admin sets "api_export_size:{}" quota for Primary'
                 ' user'.format(self.test_quota_limit))
        quotas = dns_data_utils.rand_quotas()
        quotas['api_export_size'] = self.test_quota_limit
        self._set_quota_for_project(
            self.zone_client.project_id, quotas)
        LOG.info('Create a Zone, wait until ACTIVE and add:{}'
                 ' Recordsets'.format(self.test_quota_limit + 1))
        zone = self.zone_client.create_zone(
            description='Zone for test_api_export_size_quota',
            wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete,
            self.zone_client, zone['id'])
        for i in range(self.test_quota_limit + 1):
            recordset_data = dns_data_utils.rand_recordset_data(
                record_type='A', zone_name=zone['name'])
            LOG.info('Try to create a recordset No:{}'.format(i))
            recordset = self.recordset_client.create_recordset(
                zone['id'], recordset_data=recordset_data,
                wait_until=const.ACTIVE)[1]
            self.addCleanup(
                self.wait_recordset_delete,
                self.recordset_client,
                zone['id'], recordset['id'])
        LOG.info(
            'Ensure that the Number of Recordsets is bigger than configured'
            ' api_export_size:{}'.format(self.test_quota_limit))
        number_of_recordsets = len(self.recordset_client.list_recordset(
            zone['id'])[1]['recordsets'])
        self.assertGreater(
            number_of_recordsets, self.test_quota_limit,
            'Failed, the number of recordsets within a Zone is not enough to'
            ' trigger "413 over quota" on Zone Export')
        LOG.info('Try to export Zone. Expected:"413 over_quota"')
        with self.assertRaisesDns(
                lib_exc.OverLimit, 'over_quota', 413):
            self.export_zone_client.create_zone_export(zone['id'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('2513cb6e-85ec-11ec-bf7f-201e8823901f')
    def test_recordset_records_quota(self):
        LOG.info('Admin sets "recordset_records:{}" quota for Primary'
                 ' user'.format(self.test_quota_limit))
        quotas = dns_data_utils.rand_quotas()
        quotas['recordset_records'] = self.test_quota_limit
        self._set_quota_for_project(
            self.zone_client.project_id, quotas)
        LOG.info('Create a Zone and wait until ACTIVE')
        zone_name = dns_data_utils.rand_zone_name(
            name="test_recordset_records_quota", suffix=self.tld_name)
        zone = self.zone_client.create_zone(
            name=zone_name,
            description='Zone for test_recordset_records_quota',
            wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete,
            self.zone_client, zone['id'])
        LOG.info(
            'Create recordset data with:{} records and try to create'
            ' a recordset. Expected:"413 over_quota"'.format(
                self.test_quota_limit + 1))
        recordset_data = dns_data_utils.rand_recordset_data(
            record_type='A', zone_name=zone['name'],
            number_of_records=self.test_quota_limit + 1)
        LOG.info('Try to create a recordset. Expected:"413 over_quota"')
        with self.assertRaisesDns(
                lib_exc.OverLimit, 'over_quota', 413):
            self.recordset_client.create_recordset(
                zone['id'], recordset_data=recordset_data)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('893dc648-868d-11ec-8ccb-201e8823901f')
    def test_zone_records_quota(self):
        LOG.info('Create a Zone and wait until ACTIVE')
        zone_name = dns_data_utils.rand_zone_name(
            name="test_zone_records_quota", suffix=self.tld_name)
        zone = self.zone_client.create_zone(
            name=zone_name,
            description='Zone for test_zone_records_quota',
            wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete,
            self.zone_client, zone['id'])
        LOG.info('Admin sets "zone_records:{}" quota for Primary '
                 'user'.format(self.test_quota_limit))
        quotas = dns_data_utils.rand_quotas()
        quotas['zone_records'] = self.test_quota_limit
        self._set_quota_for_project(
            self.zone_client.project_id, quotas)
        LOG.info(
            'Try to add:{} recordsets (with a single record) to the Zone in'
            ' loop. Expected:"413 over_quota"'.format(
                self.test_quota_limit + 1))
        self._reach_quota_limit(
            self.test_quota_limit + 1, 'zone_records', zone)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('f567bdda-86b3-11ec-8ccb-201e8823901f')
    def test_zone_recordsets_quota(self):
        LOG.info('Create a Zone and wait until ACTIVE')
        zone_name = dns_data_utils.rand_zone_name(
            name="test_zone_recordsets_quota", suffix=self.tld_name)
        zone = self.zone_client.create_zone(
            name=zone_name,
            description='Zone for test_zone_recordsets_quota',
            wait_until=const.ACTIVE)[1]
        self.addCleanup(
            self.wait_zone_delete,
            self.zone_client, zone['id'])
        LOG.info('Admin sets "zone_recordsets:{}" quota for Primary '
                 'user'.format(self.test_quota_limit))
        quotas = dns_data_utils.rand_quotas()
        quotas['zone_recordsets'] = self.test_quota_limit
        self._set_quota_for_project(
            self.zone_client.project_id, quotas)
        LOG.info(
            'Try to add:{} recordsets (with a random number of records) to a'
            ' Zone in loop. Expected:"413 over_quota"'.format(
                self.test_quota_limit + 1))
        self._reach_quota_limit(
            self.test_quota_limit + 1,
            'zone_recordsets', zone)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('6987953a-dccf-11eb-903e-74e5f9e2a801')
    def test_zones_quota(self):
        LOG.info('Admin sets "zones" quota for Primary user')
        quotas = dns_data_utils.rand_quotas()
        quotas['zones'] = self.test_quota_limit
        self._set_quota_for_project(
            self.zone_client.project_id, quotas)
        LOG.info('Try to create Zones. Expected:"413 over_quota"')
        self._reach_quota_limit(self.test_quota_limit, 'zones_quota')


class QuotasBoundary(base.BaseDnsV2Test, tempest.test.BaseTestCase):

    credentials = ['admin', 'system_admin']

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(QuotasBoundary, cls).setup_credentials()

    @classmethod
    def skip_checks(cls):
        super(QuotasBoundary, cls).skip_checks()
        if not CONF.dns_feature_enabled.api_v2_quotas:
            skip_msg = ("%s skipped as designate V2 Quotas API is not "
                        "available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(QuotasBoundary, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_tld_client = cls.os_system_admin.dns_v2.TldClient()
            cls.quota_client = cls.os_system_admin.dns_v2.QuotasClient()
            cls.project_client = cls.os_system_admin.projects_client
            cls.zone_client = cls.os_system_admin.dns_v2.ZonesClient()
            cls.recordset_client = \
                cls.os_system_admin.dns_v2.RecordsetClient()
            cls.export_zone_client = \
                cls.os_system_admin.dns_v2.ZoneExportsClient()
        else:
            cls.quota_client = cls.os_admin.dns_v2.QuotasClient()
            cls.project_client = cls.os_admin.projects_client
            cls.zone_client = cls.os_admin.dns_v2.ZonesClient()
            cls.recordset_client = cls.os_admin.dns_v2.RecordsetClient()
            cls.export_zone_client = cls.os_admin.dns_v2.ZoneExportsClient()
            cls.admin_tld_client = cls.os_admin.dns_v2.TldClient()

    @classmethod
    def resource_setup(cls):
        super(QuotasBoundary, cls).resource_setup()
        # Make sure we have an allowed TLD available
        tld_name = dns_data_utils.rand_zone_name(name="QuotasBoundary")
        cls.tld_name = f".{tld_name}"
        cls.class_tld = cls.admin_tld_client.create_tld(tld_name=tld_name[:-1])

    @classmethod
    def resource_cleanup(cls):
        cls.admin_tld_client.delete_tld(cls.class_tld[1]['id'])
        super(QuotasBoundary, cls).resource_cleanup()

    @decorators.attr(type='slow')
    @decorators.idempotent_id('e4981eb2-3803-11ed-9d3c-201e8823901f')
    def test_zone_quota_boundary(self):
        # Create a dedicated Project for Boundary tests
        tenant_id = self.project_client.create_project(
            name=data_utils.rand_name(name='BoundaryZone'))['project']['id']
        self.addCleanup(self.project_client.delete_project, tenant_id)

        # Set Quotas (zones:1) for tested project
        sudo_header = {'x-auth-sudo-project-id': tenant_id}
        quotas = {
            'zones': 1, 'zone_recordsets': 2, 'zone_records': 3,
            'recordset_records': 2, 'api_export_size': 3}
        self.quota_client.set_quotas(
            project_id=tenant_id, quotas=quotas,
            headers=sudo_header)

        # Create a first Zone --> Should PASS
        zone_name = dns_data_utils.rand_zone_name(
            name="test_zone_quota_boundary_attempt_1", suffix=self.tld_name)
        zone = self.zone_client.create_zone(
            name=zone_name, project_id=tenant_id)[1]
        self.addCleanup(self.wait_zone_delete, self.zone_client, zone['id'])

        # Create a second zone --> should FAIL on: 413 over_quota
        zone_name = dns_data_utils.rand_zone_name(
            name="test_zone_quota_boundary_attempt_2", suffix=self.tld_name)
        try:
            response_headers, zone = self.zone_client.create_zone(
                name=zone_name, project_id=tenant_id)
            if response_headers['status'] != 413:
                raise exceptions.InvalidStatusError(
                    'Zone', zone['id'], zone['status'])
        except Exception as e:
            self.assertIn('over_quota', str(e),
                          'Failed, over_quota for a zone was not raised')
        finally:
            self.addCleanup(
                self.wait_zone_delete,
                self.zone_client, zone['id'],
                headers=sudo_header,
                ignore_errors=lib_exc.NotFound)
