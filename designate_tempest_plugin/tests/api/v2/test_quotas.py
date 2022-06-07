# Copyright 2016 Rackspace
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
from tempest.lib.common.utils import data_utils

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)

quotas_types = ["api_export_size", "recordset_records",
                "zone_records", "zone_recordsets", "zones"]


class QuotasV2Test(base.BaseDnsV2Test):

    credentials = ["primary", "admin", "system_admin", "system_reader", "alt",
                   "project_member", "project_reader"]

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
        else:
            cls.admin_client = cls.os_admin.dns_v2.QuotasClient()
        cls.quotas_client = cls.os_primary.dns_v2.QuotasClient()
        cls.alt_client = cls.os_alt.dns_v2.QuotasClient()

    def _store_quotas(self, project_id, cleanup=True):
        """Remember current quotas and reset them after the test"""
        params = {'project_id': project_id,
                  'headers': self.all_projects_header}

        _r, original_quotas = self.admin_client.show_quotas(**params)
        params.update(original_quotas)
        if cleanup:
            self.addCleanup(self.admin_client.update_quotas, **params)
        return original_quotas

    @decorators.idempotent_id('1dac991a-9e2e-452c-a47a-26ac37381ec5')
    def test_show_quotas(self):
        LOG.info("Show default quotas, validate all quota types exists and "
                 "their values are integers.")
        for user in ['primary', 'admin']:
            if user == 'primary':
                body = self.quotas_client.show_quotas()[1]
            if user == 'admin':
                body = self.admin_client.show_quotas(
                    project_id=self.quotas_client.project_id,
                    headers=self.all_projects_header)[1]
            for quota_type in quotas_types:
                self.assertIn(
                    quota_type, body.keys(),
                    'Failed, expected quota type:{} was not found '
                    'in received quota body'.format(quota_type))
            for quota_type, quota_value in body.items():
                self.assertTrue(
                    isinstance(quota_value, int),
                    'Failed, the value of:{} is:{}, expected integer'.format(
                        quota_type, quota_value))

        expected_allowed = ['os_admin', 'os_primary', 'os_alt']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.extend(['os_system_admin', 'os_system_reader',
                                     'os_project_member', 'os_project_reader'])

        self.check_list_show_with_ID_RBAC_enforcement(
            'QuotasClient', 'show_quotas', expected_allowed, False)

    @decorators.idempotent_id('0448b089-5803-4ce3-8a6c-5c15ff75a2cc')
    def test_reset_quotas(self):
        self._store_quotas(project_id=self.quotas_client.project_id)

        LOG.info("Deleting (reset) quotas")

        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.extend(['os_system_admin'])

        self.check_CUD_RBAC_enforcement(
            'QuotasClient', 'delete_quotas', expected_allowed, False,
            project_id=self.quotas_client.project_id)

        body = self.admin_client.delete_quotas(
            project_id=self.quotas_client.project_id,
            headers=self.all_projects_header)[1]

        LOG.info("Ensuring an empty response body")
        self.assertEqual(body.strip(), b"")

    @decorators.idempotent_id('76d24c87-1b39-4e19-947c-c08e1380dc61')
    def test_update_quotas(self):
        self._store_quotas(project_id=self.quotas_client.project_id)
        LOG.info("Updating quotas")
        quotas = dns_data_utils.rand_quotas()
        body = self.admin_client.update_quotas(
            project_id=self.quotas_client.project_id,
            **quotas, headers=self.all_projects_header)[1]

        expected_allowed = ['os_admin']
        if CONF.dns_feature_enabled.enforce_new_defaults:
            expected_allowed.extend(['os_system_admin'])

        self.check_CUD_RBAC_enforcement(
            'QuotasClient', 'update_quotas', expected_allowed, False,
            project_id=self.quotas_client.project_id,
            **quotas, headers=self.all_projects_header)

        LOG.info("Ensuring the response has all quota types")
        self.assertExpected(quotas, body, [])

    @decorators.idempotent_id('9b09b3e2-7e88-4569-bce3-9be2f7ac70c3')
    def test_update_quotas_other_project(self):

        project_id = self.quotas_client.project_id
        self._store_quotas(project_id=project_id)

        LOG.info("Updating quotas for %s ", project_id)

        quotas = dns_data_utils.rand_quotas()
        request = quotas.copy()
        body = self.admin_client.update_quotas(
            project_id=project_id,
            headers=self.all_projects_header,
            **request)[1]

        LOG.info("Ensuring the response has all quota types")
        self.assertExpected(quotas, body, [])

        client_body = self.quotas_client.show_quotas(project_id=project_id)[1]

        self.assertExpected(quotas, client_body, [])

    @decorators.idempotent_id('21e45d30-dbc1-4173-9d6b-9b6813ef514b')
    def test_reset_quotas_other_project(self):

        LOG.info("Using 'alt' project id to set quotas on.")
        project_id = self.alt_client.tenant_id
        self._store_quotas(project_id=project_id)

        LOG.info("Resetting quotas to default for %s ", project_id)
        self.admin_client.delete_quotas(
            project_id=project_id,
            headers=self.all_projects_header)

        default_quotas = self.admin_client.show_quotas(
            project_id=project_id,
            headers=self.all_projects_header)[1]

        LOG.info("Updating quotas for %s ", project_id)

        quotas = dns_data_utils.rand_quotas()
        request = quotas.copy()
        self.admin_client.update_quotas(
            project_id=project_id,
            headers=self.all_projects_header,
            **request)

        self.admin_client.delete_quotas(
            project_id=project_id,
            headers=self.all_projects_header)

        final_quotas = self.admin_client.show_quotas(
            project_id=project_id,
            headers=self.all_projects_header)[1]

        self.assertExpected(default_quotas, final_quotas, [])

    @decorators.idempotent_id('9b09b3e2-7e88-4569-bce3-9be2f7ac70c4')
    def test_update_quotas_invalid_project(self):

        if not CONF.dns_feature_enabled.api_v2_quotas_verify_project:
            raise self.skipException("Project ID in quotas "
                                     "is not being verified.")
        original_quotas = self.quotas_client.show_quotas(
            project_id=self.quotas_client.project_id)[1]
        project_id = 'project-that-does-not-exist'

        LOG.info("Updating quotas for non-existing %s ", project_id)
        quotas = dns_data_utils.rand_quotas()
        request = quotas.copy()
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_project', 400):
            self.admin_client.update_quotas(
                project_id=project_id,
                headers=self.all_projects_header,
                **request)

        LOG.info("Make sure that the quotas weren't changed")
        client_body = self.quotas_client.show_quotas(
            project_id=self.quotas_client.project_id)[1]
        self.assertExpected(original_quotas, client_body, [])


class QuotasV2TestNegative(base.BaseDnsV2Test):

    credentials = ["primary", "admin", "system_admin"]

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(QuotasV2TestNegative, cls).setup_credentials()

    @classmethod
    def skip_checks(cls):
        super(QuotasV2TestNegative, cls).skip_checks()

        if not CONF.dns_feature_enabled.api_v2_quotas:
            skip_msg = ("%s skipped as designate V2 Quotas API is not "
                        "available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(QuotasV2TestNegative, cls).setup_clients()

        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_v2.QuotasClient()
        else:
            cls.admin_client = cls.os_admin.dns_v2.QuotasClient()
        cls.quotas_client = cls.os_primary.dns_v2.QuotasClient()

    @decorators.idempotent_id('ae82a0ba-da60-11eb-bf12-74e5f9e2a801')
    def test_admin_sets_quota_for_a_project(self):

        primary_project_id = self.quotas_client.project_id
        http_headers_to_use = [self.all_projects_header,
            {'x-auth-sudo-project-id': primary_project_id}]

        for http_header in http_headers_to_use:
            LOG.info('As Admin user set Zones quota for a Primary user and {} '
                     'HTTP header'.format(http_header))
            quotas = dns_data_utils.rand_quotas()
            self.admin_client.set_quotas(
                project_id=primary_project_id,
                quotas=quotas, headers=http_header)
            self.addCleanup(self.admin_client.delete_quotas,
                            project_id=primary_project_id)

            LOG.info("As Admin fetch the quotas for a Primary user")
            body = self.admin_client.show_quotas(
                project_id=primary_project_id, headers=http_header)[1]
            LOG.info('Ensuring that the "set" and "shown" quotas are same')
            self.assertExpected(quotas, body, [])

    @decorators.idempotent_id('40b9d7ac-da5f-11eb-bf12-74e5f9e2a801')
    def test_primary_fails_to_set_quota(self):

        primary_project_id = self.quotas_client.project_id
        LOG.info('Try to set quota as Primary user')
        self.assertRaises(
            lib_exc.Forbidden, self.quotas_client.set_quotas,
            project_id=primary_project_id,
            quotas=dns_data_utils.rand_quotas())

        LOG.info('Try to set quota as Primary user using '
                 '"x-auth-sudo-project-id" HTTP header')
        self.assertRaises(
            lib_exc.Forbidden, self.quotas_client.set_quotas,
            project_id=self.quotas_client.project_id,
            quotas=dns_data_utils.rand_quotas(),
            headers={'x-auth-sudo-project-id': primary_project_id})

        LOG.info('Try to set quota as Primary user using '
                 '"x-auth-all-projects" HTTP header')
        self.assertRaises(
            lib_exc.Forbidden, self.quotas_client.set_quotas,
            project_id=self.quotas_client.project_id,
            quotas=dns_data_utils.rand_quotas(),
            headers=self.all_projects_header)

    @decorators.idempotent_id('a6ce5b46-dcce-11eb-903e-74e5f9e2a801')
    def test_admin_sets_invalid_quota_values(self):

        primary_project_id = self.quotas_client.project_id

        for item in quotas_types:
            quota = dns_data_utils.rand_quotas()
            quota[item] = data_utils.rand_name()
            self.assertRaises(
                lib_exc.BadRequest, self.admin_client.set_quotas,
                project_id=primary_project_id,
                quotas=quota,
                headers=self.all_projects_header)

    @decorators.idempotent_id('ac212fd8-c602-11ec-b042-201e8823901f')
    def test_admin_sets_not_existing_quota_type(self):

        LOG.info('Try to set quota using not existing quota type in its body')
        primary_project_id = self.quotas_client.project_id
        quota = dns_data_utils.rand_quotas()
        quota[data_utils.rand_name()] = 777

        with self.assertRaisesDns(
                lib_exc.BadRequest, 'invalid_object', 400):
            self.admin_client.set_quotas(
                project_id=primary_project_id,
                quotas=quota, headers=self.all_projects_header)
