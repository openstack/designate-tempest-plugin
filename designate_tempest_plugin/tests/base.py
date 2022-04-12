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
from tempest import test
from tempest import config
from tempest.lib.common.utils import test_utils as utils

from designate_tempest_plugin.services.dns.query.query_client import \
    QueryClient
from designate_tempest_plugin.tests import rbac_utils


CONF = config.CONF


class AssertRaisesDns(test.BaseTestCase):
    def __init__(self, test_class, exc, type_, code):
        self.test_class = test_class
        self.exc = exc
        self.type_ = type_
        self.code = code

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            try:
                exc_name = self.exc.__name__
            except AttributeError:
                exc_name = str(self.exc)
            raise self.failureException(
                "{0} not raised".format(exc_name))

        if issubclass(exc_type, self.exc):
            self.test_class.assertEqual(
                self.code, exc_value.resp_body['code'])

            self.test_class.assertEqual(
                    self.type_, exc_value.resp_body['type'])

            return True

        # Unexpected exceptions will be reraised
        return False


class BaseDnsTest(rbac_utils.RBACTestsMixin, test.BaseTestCase):
    """Base class for DNS tests."""

    # NOTE(andreaf) credentials holds a list of the credentials to be allocated
    # at class setup time. Credential types can be 'primary', 'alt', 'admin' or
    # a list of roles - the first element of the list being a label, and the
    # rest the actual roles.
    # NOTE(kiall) primary will result in a manager @ cls.os_primary, alt will
    # have cls.os_alt, and admin will have cls.os_admin.
    # NOTE(johnsom) We will allocate most credentials here so that each test
    # can test for allowed and disallowed RBAC policies.
    credentials = ['admin', 'primary', 'alt']
    if CONF.dns_feature_enabled.enforce_new_defaults:
        credentials.extend(['system_admin', 'system_reader',
                            'project_member', 'project_reader'])

    # A tuple of credentials that will be allocated by tempest using the
    # 'credentials' list above. These are used to build RBAC test lists.
    allocated_creds = []
    for cred in credentials:
        if isinstance(cred, list):
            allocated_creds.append('os_roles_' + cred[0])
        else:
            allocated_creds.append('os_' + cred)
    # Tests shall not mess with the list of allocated credentials
    allocated_credentials = tuple(allocated_creds)

    @classmethod
    def skip_checks(cls):
        super(BaseDnsTest, cls).skip_checks()

        if not CONF.service_available.designate:
            skip_msg = ("%s skipped as designate is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(BaseDnsTest, cls).setup_clients()
        # The Query Client is not an OpenStack client which means
        # we should not set it up through the tempest client manager.
        # Set it up here so all tests have access to it.
        cls.query_client = QueryClient(
            nameservers=CONF.dns.nameservers,
            query_timeout=CONF.dns.query_timeout,
            build_interval=CONF.dns.build_interval,
            build_timeout=CONF.dns.build_timeout,
        )

    def assertExpected(self, expected, actual, excluded_keys):
        for key, value in expected.items():
            if key not in excluded_keys:
                self.assertIn(key, actual)
                self.assertEqual(value, actual[key], key)

    def assertRaisesDns(self, exc, type_, code, callable_=None, *args,
                        **kwargs):
        """
        Checks the response that a api call with a exception contains the
        expected data

        Usable as both a ordinary function, and a context manager
        """
        context = AssertRaisesDns(self, exc, type_, code)

        if callable_ is None:
            return context

        with context:
            callable_(*args, **kwargs)

    def transfer_request_delete(self, transfer_client, transfer_request_id):
        return utils.call_and_ignore_notfound_exc(
            transfer_client.delete_transfer_request, transfer_request_id)

    def wait_zone_delete(self, zone_client, zone_id, **kwargs):
        self._delete_zone(zone_client, zone_id, **kwargs)
        utils.call_until_true(self._check_zone_deleted,
                              CONF.dns.build_timeout,
                              CONF.dns.build_interval,
                              zone_client,
                              zone_id)

    def wait_recordset_delete(self, recordset_client, zone_id,
                              recordset_id, **kwargs):
        self._delete_recordset(
            recordset_client, zone_id, recordset_id, **kwargs)
        utils.call_until_true(self._check_recordset_deleted,
                              CONF.dns.build_timeout,
                              CONF.dns.build_interval,
                              recordset_client,
                              zone_id,
                              recordset_id)

    def unset_ptr(self, ptr_client, fip_id, **kwargs):
        return utils.call_and_ignore_notfound_exc(
            ptr_client.unset_ptr_record, fip_id, **kwargs)

    def _delete_zone(self, zone_client, zone_id, **kwargs):
        return utils.call_and_ignore_notfound_exc(zone_client.delete_zone,
                                                  zone_id, **kwargs)

    def _check_zone_deleted(self, zone_client, zone_id):
        return utils.call_and_ignore_notfound_exc(zone_client.show_zone,
                                                  zone_id) is None

    def _delete_recordset(self, recordset_client, zone_id,
                          recordset_id, **kwargs):
        return utils.call_and_ignore_notfound_exc(
            recordset_client.delete_recordset,
            zone_id, recordset_id, **kwargs)

    def _check_recordset_deleted(
            self, recordset_client, zone_id, recordset_id):
        return utils.call_and_ignore_notfound_exc(
            recordset_client.show_recordset, zone_id, recordset_id) is None


class BaseDnsV2Test(BaseDnsTest):
    """Base class for DNS V2 API tests."""

    all_projects_header = {'X-Auth-All-Projects': True}
    managed_records = {'x-designate-edit-managed-records': True}

    @classmethod
    def skip_checks(cls):
        super(BaseDnsV2Test, cls).skip_checks()

        if not CONF.dns_feature_enabled.api_v2:
            skip_msg = ("%s skipped as designate v2 API is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)


class BaseDnsAdminTest(BaseDnsTest):
    """Base class for DNS Admin API tests."""

    @classmethod
    def skip_checks(cls):
        super(BaseDnsAdminTest, cls).skip_checks()
        if not CONF.dns_feature_enabled.api_admin:
            skip_msg = ("%s skipped as designate admin API is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)
