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

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


class QuotasV2Test(base.BaseDnsV2Test):

    credentials = ["primary", "admin", "system_admin", "alt"]

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
        self._store_quotas(project_id=self.quotas_client.project_id)
        LOG.info("Updating quotas")
        quotas = dns_data_utils.rand_quotas()
        _, body = self.admin_client.update_quotas(
            project_id=self.quotas_client.project_id,
            headers=self.all_projects_header,
            **quotas)

        LOG.info("Fetching quotas")
        _, body = self.admin_client.show_quotas(
            project_id=self.quotas_client.project_id,
            headers=self.all_projects_header)

        LOG.info("Ensuring the response has all quota types")
        self.assertExpected(quotas, body, [])

    @decorators.idempotent_id('0448b089-5803-4ce3-8a6c-5c15ff75a2cc')
    def test_delete_quotas(self):
        self._store_quotas(project_id=self.quotas_client.project_id)
        LOG.info("Deleting quotas")
        _, body = self.admin_client.delete_quotas(
            project_id=self.quotas_client.project_id,
            headers=self.all_projects_header)

        LOG.info("Ensuring an empty response body")
        self.assertEqual(body.strip(), b"")

    @decorators.idempotent_id('76d24c87-1b39-4e19-947c-c08e1380dc61')
    def test_update_quotas(self):
        if CONF.enforce_scope.designate:
            raise self.skipException(
                "System scoped tokens do not have a project_id.")

        self._store_quotas(project_id=self.admin_client.project_id)
        LOG.info("Updating quotas")
        quotas = dns_data_utils.rand_quotas()
        _, body = self.admin_client.update_quotas(
            project_id=self.admin_client.project_id,
            **quotas)

        LOG.info("Ensuring the response has all quota types")
        self.assertExpected(quotas, body, [])

    @decorators.idempotent_id('9b09b3e2-7e88-4569-bce3-9be2f7ac70c3')
    def test_update_quotas_other_project(self):

        project_id = self.quotas_client.project_id
        self._store_quotas(project_id=project_id)

        LOG.info("Updating quotas for %s ", project_id)

        quotas = dns_data_utils.rand_quotas()
        request = quotas.copy()
        _, body = self.admin_client.update_quotas(
            project_id=project_id,
            headers=self.all_projects_header,
            **request)

        LOG.info("Ensuring the response has all quota types")
        self.assertExpected(quotas, body, [])

        _, client_body = self.quotas_client.show_quotas(project_id=project_id)

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

        _, default_quotas = self.admin_client.show_quotas(
            project_id=project_id,
            headers=self.all_projects_header)

        LOG.info("Updating quotas for %s ", project_id)

        quotas = dns_data_utils.rand_quotas()
        request = quotas.copy()
        _, body = self.admin_client.update_quotas(
            project_id=project_id,
            headers=self.all_projects_header,
            **request)

        self.admin_client.delete_quotas(
            project_id=project_id,
            headers=self.all_projects_header)

        _, final_quotas = self.admin_client.show_quotas(
            project_id=project_id,
            headers=self.all_projects_header)

        self.assertExpected(default_quotas, final_quotas, [])

    @decorators.idempotent_id('9b09b3e2-7e88-4569-bce3-9be2f7ac70c4')
    def test_update_quotas_invalid_project(self):

        if not CONF.dns_feature_enabled.api_v2_quotas_verify_project:
            raise self.skipException("Project ID in quotas "
                                     "is not being verified.")

        project_id = 'project-that-does-not-exist'

        LOG.info("Updating quotas for non-existing %s ", project_id)

        quotas = dns_data_utils.rand_quotas()
        request = quotas.copy()
        with self.assertRaisesDns(lib_exc.BadRequest, 'invalid_project', 400):
            self.admin_client.update_quotas(
                project_id=project_id,
                headers=self.all_projects_header,
                **request)
