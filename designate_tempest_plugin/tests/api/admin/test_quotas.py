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

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseQuotasTest(base.BaseDnsAdminTest):

    excluded_keys = []

    def setUp(self):
        if CONF.dns_feature_enabled.bug_1573141_fixed:
            self.excluded_keys = ['api_export_size']
        super(BaseQuotasTest, self).setUp()


class QuotasAdminTest(BaseQuotasTest):

    credentials = ["admin", "primary", "system_admin"]

    def setUp(self):
        super(QuotasAdminTest, self).setUp()
        _, original_quotas = self.admin_client.show_quotas(
            project_id=self.quotas_client.project_id)
        self.addCleanup(self.admin_client.update_quotas,
                        project_id=self.quotas_client.project_id,
                        **original_quotas['quota'])

    @classmethod
    def setup_credentials(cls):
        # Do not create network resources for these test.
        cls.set_network_resources()
        super(QuotasAdminTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(QuotasAdminTest, cls).setup_clients()
        if CONF.enforce_scope.designate:
            cls.admin_client = cls.os_system_admin.dns_admin.QuotasClient()
        else:
            cls.admin_client = cls.os_admin.dns_admin.QuotasClient()
        cls.quotas_client = cls.os_primary.dns_v2.QuotasClient()

    @decorators.idempotent_id('ed42f367-e5ba-40d7-a08d-366ad787d21c')
    def test_show_quotas(self):
        LOG.info("Updating quotas")
        quotas = dns_data_utils.rand_quotas()
        _, body = self.admin_client.update_quotas(
            project_id=self.quotas_client.project_id, **quotas)
        self.addCleanup(self.admin_client.delete_quotas,
                        project_id=self.quotas_client.project_id)

        LOG.info("Fetching quotas")
        _, body = self.admin_client.show_quotas(
            project_id=self.quotas_client.project_id)

        LOG.info("Ensuring the response has all quota types")
        self.assertExpected(quotas, body['quota'], self.excluded_keys)

    @decorators.idempotent_id('33e0affb-5d66-4216-881c-f101a779851a')
    def test_delete_quotas(self):
        LOG.info("Deleting quotas")
        _, body = self.admin_client.delete_quotas(
            project_id=self.quotas_client.project_id)

        LOG.info("Ensuring an empty response body")
        self.assertEqual(body.strip(), b"")

    @decorators.idempotent_id('4f2b65b7-c4e1-489c-9047-755e42ba0985')
    def test_update_quotas(self):
        LOG.info("Updating quotas")
        quotas = dns_data_utils.rand_quotas()
        _, body = self.admin_client.update_quotas(
            project_id=self.quotas_client.project_id,
            **quotas)
        self.addCleanup(self.admin_client.delete_quotas,
                        project_id=self.quotas_client.project_id)

        LOG.info("Ensuring the response has all quota types")
        self.assertExpected(quotas, body['quota'], self.excluded_keys)
