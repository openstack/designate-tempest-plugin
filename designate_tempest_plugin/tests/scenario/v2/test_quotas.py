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

from oslo_log import log as logging
from tempest import config
from tempest.lib import decorators

from designate_tempest_plugin.tests import base
from designate_tempest_plugin import data_utils as dns_data_utils

LOG = logging.getLogger(__name__)


CONF = config.CONF


class QuotasV2Test(base.BaseDnsV2Test):

    credentials = ['primary', 'admin', 'system_admin', 'alt']

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
        cls.alt_zone_client = cls.os_alt.dns_v2.ZonesClient()

    @decorators.idempotent_id('6987953a-dccf-11eb-903e-74e5f9e2a801')
    def test_alt_reaches_zones_quota(self):

        alt_project_id = self.alt_client.project_id
        http_header = {'x-auth-sudo-project-id': alt_project_id}
        limit_zones_quota = 3

        LOG.info('As Admin user set Zones quota for Alt user '
                 'to:{} '.format(limit_zones_quota))
        quotas = dns_data_utils.rand_quotas()
        quotas['zones'] = limit_zones_quota
        self.admin_client.set_quotas(
            project_id=alt_project_id, quotas=quotas, headers=http_header)
        self.addCleanup(
            self.admin_client.delete_quotas, project_id=alt_project_id)

        LOG.info('As Alt user try to create zones, up untill'
                 ' "zones" quota (status code 413) is reached')
        attempt_number = 0
        while attempt_number <= limit_zones_quota + 1:
            attempt_number += 1
            LOG.info('Attempt No:{} '.format(attempt_number))
            try:
                zone = self.alt_zone_client.create_zone()[1]
                self.addCleanup(
                    self.wait_zone_delete, self.alt_zone_client, zone['id'])
            except Exception as err:
                raised_error = str(err).replace(' ', '')
                if not "'code':413" and "'type':'over_quota'" in raised_error \
                        and attempt_number == limit_zones_quota + 1:
                    raise (
                        "Failed, expected status code 413 (type:over_quota) "
                        "was not raised or maybe it has been raised mistakenly"
                        "(bug) before the quota was actually reached."
                        " Test failed with: {} ".format(err))
