# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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
import six
from tempest import test
from tempest import config

from designate_tempest_plugin import clients


CONF = config.CONF


class BaseDnsTest(test.BaseTestCase):
    """Base class for DNS tests."""

    # NOTE(andreaf) credentials holds a list of the credentials to be allocated
    # at class setup time. Credential types can be 'primary', 'alt', 'admin' or
    # a list of roles - the first element of the list being a label, and the
    # rest the actual roles.
    # NOTE(kiall) primary will result in a manager @ cls.os, alt will have
    # cls.os_alt, and admin will have cls.os_adm.
    # NOTE(kiall) We should default to only primary, and request additional
    # credentials in the tests that require them.
    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(BaseDnsTest, cls).skip_checks()

        if not CONF.service_available.designate:
            skip_msg = ("%s skipped as designate is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

    def assertExpected(self, expected, actual, excluded_keys):
        for key, value in six.iteritems(expected):
            if key not in excluded_keys:
                self.assertIn(key, actual)
                self.assertEqual(value, actual[key], key)


class BaseDnsV1Test(BaseDnsTest):
    """Base class for DNS V1 API tests."""

    # Use the Designate V1 Client Manager
    client_manager = clients.ManagerV1

    @classmethod
    def skip_checks(cls):
        super(BaseDnsV1Test, cls).skip_checks()

        if not CONF.dns_feature_enabled.api_v1:
            skip_msg = ("%s skipped as designate v1 API is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)


class BaseDnsV2Test(BaseDnsTest):
    """Base class for DNS V2 API tests."""

    # Use the Designate V2 Client Manager
    client_manager = clients.ManagerV2

    @classmethod
    def skip_checks(cls):
        super(BaseDnsV2Test, cls).skip_checks()

        if not CONF.dns_feature_enabled.api_v2:
            skip_msg = ("%s skipped as designate v2 API is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)


class BaseDnsAdminTest(BaseDnsTest):
    """Base class for DNS Admin API tests."""

    # Use the Designate V2 Client Manager
    client_manager = clients.ManagerV2

    @classmethod
    def skip_checks(cls):
        super(BaseDnsAdminTest, cls).skip_checks()
        if not CONF.dns_feature_enabled.api_admin:
            skip_msg = ("%s skipped as designate admin API is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)
