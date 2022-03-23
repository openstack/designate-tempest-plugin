# Copyright 2021 Red Hat, Inc. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy

from oslo_log import log as logging
from tempest import config
from tempest.lib import exceptions
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class RBACTestsMixin(test.BaseTestCase):

    def _get_client_method(self, cred_obj, client_str, method_str):
        """Get requested method from registered clients in Tempest."""
        dns_clients = getattr(cred_obj, 'dns_v2')
        client = getattr(dns_clients, client_str)
        client_obj = client()
        method = getattr(client_obj, method_str)
        return method

    def _get_client_project_id(self, cred_obj, client_str):
        """Get project ID for the credential."""
        dns_clients = getattr(cred_obj, 'dns_v2')
        client = getattr(dns_clients, client_str)
        client_obj = client()
        return client_obj.project_id

    def _check_allowed(self, client_str, method_str, allowed_list,
                       with_project, *args, **kwargs):
        """Test an API call allowed RBAC enforcement.

        :param client_str: The service client to use for the test, without the
                           credential.  Example: 'ZonesClient'
        :param method_str: The method on the client to call for the test.
                           Example: 'list_zones'
        :param allowed_list: The list of credentials expected to be
                             allowed.  Example: ['primary'].
        :param with_project: When true, pass the project ID to the call.
        :param args: Any positional parameters needed by the method.
        :param kwargs: Any named parameters needed by the method.
        :raises AssertionError: Raised if the RBAC tests fail.
        :raises Forbidden: Raised if a credential that should have access does
                           not and is denied.
        :raises InvalidScope: Raised if a credential that should have the
                              correct scope for access is denied.
        :returns: None on success
        """
        for cred in allowed_list:
            try:
                cred_obj = getattr(self, cred)
            except AttributeError:
                # TODO(johnsom) Remove once scoped tokens is the default.
                if ((cred == 'os_system_admin' or
                     cred == 'os_system_reader') and
                        not CONF.enforce_scope.designate):
                    LOG.info('Skipping %s allowed RBAC test because '
                             'enforce_scope.designate is not True', cred)
                    continue
                else:
                    self.fail('Credential {} "expected_allowed" for RBAC '
                              'testing was not created by tempest '
                              'credentials setup. This is likely a bug in the '
                              'test.'.format(cred))
            method = self._get_client_method(cred_obj, client_str, method_str)
            project_id = self._get_client_project_id(cred_obj, client_str)
            try:
                if with_project:
                    method(project_id, *args, **kwargs)
                else:
                    method(*args, **kwargs)
            except exceptions.Forbidden as e:
                self.fail('Method {}.{} failed to allow access via RBAC using '
                          'credential {}. Error: {}'.format(
                              client_str, method_str, cred, str(e)))
            except exceptions.NotFound as e:
                self.fail('Method {}.{} failed to allow access via RBAC using '
                          'credential {}. Error: {}'.format(
                              client_str, method_str, cred, str(e)))

    def _check_disallowed(self, client_str, method_str, allowed_list,
                          expect_404, with_project, *args, **kwargs):
        """Test an API call disallowed RBAC enforcement.

        :param client_str: The service client to use for the test, without the
                           credential.  Example: 'ZonesClient'
        :param method_str: The method on the client to call for the test.
                           Example: 'list_zones'
        :param allowed_list: The list of credentials expected to be
                             allowed.  Example: ['primary'].
        :param expect_404: When True, 404 responses are considered ok.
        :param with_project: When true, pass the project ID to the call.
        :param args: Any positional parameters needed by the method.
        :param kwargs: Any named parameters needed by the method.
        :raises AssertionError: Raised if the RBAC tests fail.
        :raises Forbidden: Raised if a credential that should have access does
                           not and is denied.
        :raises InvalidScope: Raised if a credential that should have the
                              correct scope for access is denied.
        :returns: None on success
        """
        expected_disallowed = (set(self.allocated_credentials) -
                               set(allowed_list))
        for cred in expected_disallowed:
            cred_obj = getattr(self, cred)
            method = self._get_client_method(cred_obj, client_str, method_str)
            project_id = self._get_client_project_id(cred_obj, client_str)

            # Unfortunately tempest uses testtools assertRaises[1] which means
            # we cannot use the unittest assertRaises context[2] with msg= to
            # give a useful error.
            # Also, testtools doesn't work with subTest[3], so we can't use
            # that to expose the failing credential.
            # This all means the exception raised testtools assertRaises
            # is less than useful.
            # TODO(johnsom) Remove this try block once testtools is useful.
            # [1] https://testtools.readthedocs.io/en/latest/
            #     api.html#testtools.TestCase.assertRaises
            # [2] https://docs.python.org/3/library/
            #     unittest.html#unittest.TestCase.assertRaises
            # [3] https://github.com/testing-cabal/testtools/issues/235
            try:
                if with_project:
                    method(project_id, *args, **kwargs)
                else:
                    method(*args, **kwargs)
            except exceptions.Forbidden:
                continue
            except exceptions.NotFound:
                # Some APIs hide that the resource exists by returning 404
                # on permission denied.
                if expect_404:
                    continue
                raise
            self.fail('Method {}.{} failed to deny access via RBAC using '
                      'credential {}.'.format(client_str, method_str, cred))

    def check_list_show_RBAC_enforcement(self, client_str, method_str,
                                         expected_allowed, expect_404,
                                         *args, **kwargs):
        """Test list or show API call RBAC enforcement.

        :param client_str: The service client to use for the test, without the
                           credential.  Example: 'ZonesClient'
        :param method_str: The method on the client to call for the test.
                           Example: 'list_zones'
        :param expected_allowed: The list of credentials expected to be
                                 allowed.  Example: ['primary'].
        :param expect_404: When True, 404 responses are considered ok.
        :param args: Any positional parameters needed by the method.
        :param kwargs: Any named parameters needed by the method.
        :raises AssertionError: Raised if the RBAC tests fail.
        :raises Forbidden: Raised if a credential that should have access does
                           not and is denied.
        :raises InvalidScope: Raised if a credential that should have the
                              correct scope for access is denied.
        :returns: None on success
        """

        allowed_list = copy.deepcopy(expected_allowed)

        # #### Test that disallowed credentials cannot access the API.
        self._check_disallowed(client_str, method_str, allowed_list,
                               expect_404, False, *args, **kwargs)

        # #### Test that allowed credentials can access the API.
        self._check_allowed(client_str, method_str, allowed_list, False,
                            *args, **kwargs)

    def check_list_show_with_ID_RBAC_enforcement(self, client_str, method_str,
                                                 expected_allowed, expect_404,
                                                 *args, **kwargs):
        """Test list or show API call passing the project ID RBAC enforcement.

        :param client_str: The service client to use for the test, without the
                           credential.  Example: 'ZonesClient'
        :param method_str: The method on the client to call for the test.
                           Example: 'list_zones'
        :param expected_allowed: The list of credentials expected to be
                                 allowed.  Example: ['primary'].
        :param expect_404: When True, 404 responses are considered ok.
        :param args: Any positional parameters needed by the method.
        :param kwargs: Any named parameters needed by the method.
        :raises AssertionError: Raised if the RBAC tests fail.
        :raises Forbidden: Raised if a credential that should have access does
                           not and is denied.
        :raises InvalidScope: Raised if a credential that should have the
                              correct scope for access is denied.
        :returns: None on success
        """

        allowed_list = copy.deepcopy(expected_allowed)

        # #### Test that disallowed credentials cannot access the API.
        self._check_disallowed(client_str, method_str, allowed_list,
                               expect_404, True, *args, **kwargs)

        # #### Test that allowed credentials can access the API.
        self._check_allowed(client_str, method_str, allowed_list, True,
                            *args, **kwargs)

    def check_CUD_RBAC_enforcement(self, client_str, method_str,
                                   expected_allowed, expect_404,
                                   *args, **kwargs):
        """Test an API create/update/delete call RBAC enforcement.

        :param client_str: The service client to use for the test, without the
                           credential.  Example: 'ZonesClient'
        :param method_str: The method on the client to call for the test.
                           Example: 'list_zones'
        :param expected_allowed: The list of credentials expected to be
                                 allowed.  Example: ['primary'].
        :param expect_404: When True, 404 responses are considered ok.
        :param args: Any positional parameters needed by the method.
        :param kwargs: Any named parameters needed by the method.
        :raises AssertionError: Raised if the RBAC tests fail.
        :raises Forbidden: Raised if a credential that should have access does
                           not and is denied.
        :raises InvalidScope: Raised if a credential that should have the
                              correct scope for access is denied.
        :returns: None on success
        """

        allowed_list = copy.deepcopy(expected_allowed)

        # #### Test that disallowed credentials cannot access the API.
        self._check_disallowed(client_str, method_str, allowed_list,
                               expect_404, False, *args, **kwargs)

    def check_list_RBAC_enforcement_count(
            self, client_str, method_str, expected_allowed, expected_count,
            *args, **kwargs):
        """Test an API list call RBAC enforcement result count.

        List APIs will return the object list for the project associated
        with the token used to access the API. This means most credentials
        will have access, but will get differing results.

        This test will query the list API using a list of credentials and
        will validate that only the expected count of results are returned.

        :param client_str: The service client to use for the test, without the
                           credential.  Example: 'ZonesClient'
        :param method_str: The method on the client to call for the test.
                           Example: 'list_zones'
        :param expected_allowed: The list of credentials expected to be
                                 allowed.  Example: ['primary'].
        :param expected_count: The number of results expected in the list
                               returned from the API.
        :param args: Any positional parameters needed by the method.
        :param kwargs: Any named parameters needed by the method.
        :raises AssertionError: Raised if the RBAC tests fail.
        :raises Forbidden: Raised if a credential that should have access does
                           not and is denied.
        :raises InvalidScope: Raised if a credential that should have the
                              correct scope for access is denied.
        :returns: None on success
        """

        allowed_list = copy.deepcopy(expected_allowed)

        for cred in allowed_list:
            try:
                cred_obj = getattr(self, cred)
            except AttributeError:
                # TODO(johnsom) Remove once scoped tokens is the default.
                if ((cred == 'os_system_admin' or
                     cred == 'os_system_reader') and
                        not CONF.enforce_scope.designate):
                    LOG.info('Skipping %s allowed RBAC test because '
                             'enforce_scope.designate is not True', cred)
                    continue
                else:
                    self.fail('Credential {} "expected_allowed" for RBAC '
                              'testing was not created by tempest '
                              'credentials setup. This is likely a bug in the '
                              'test.'.format(cred))
            method = self._get_client_method(cred_obj, client_str, method_str)
            try:
                # Get the result body
                result = method(*args, **kwargs)[1]
            except exceptions.Forbidden as e:
                self.fail('Method {}.{} failed to allow access via RBAC using '
                          'credential {}. Error: {}'.format(
                              client_str, method_str, cred, str(e)))
            # Remove the root element
            result_objs = next(iter(result.values()))

            self.assertEqual(expected_count, len(result_objs),
                             message='Credential {} saw {} objects when {} '
                             'was expected.'.format(cred, len(result),
                                                    expected_count))

    def check_list_IDs_RBAC_enforcement(
            self, client_str, method_str, expected_allowed, expected_ids,
            *args, **kwargs):
        """Test an API list call RBAC enforcement result contains IDs.

        List APIs will return the object list for the project associated
        with the token used to access the API. This means most credentials
        will have access, but will get differing results.

        This test will query the list API using a list of credentials and
        will validate that the expected object Ids in included in the results.

        :param client_str: The service client to use for the test, without the
                           credential.  Example: 'ZonesClient'
        :param method_str: The method on the client to call for the test.
                           Example: 'list_zones'
        :param expected_allowed: The list of credentials expected to be
                                 allowed.  Example: ['primary'].
        :param expected_ids: The list of object IDs to validate are included
                             in the returned list from the API.
        :param args: Any positional parameters needed by the method.
        :param kwargs: Any named parameters needed by the method.
        :raises AssertionError: Raised if the RBAC tests fail.
        :raises Forbidden: Raised if a credential that should have access does
                           not and is denied.
        :raises InvalidScope: Raised if a credential that should have the
                              correct scope for access is denied.
        :returns: None on success
        """

        allowed_list = copy.deepcopy(expected_allowed)

        for cred in allowed_list:
            try:
                cred_obj = getattr(self, cred)
            except AttributeError:
                # TODO(johnsom) Remove once scoped tokens is the default.
                if ((cred == 'os_system_admin' or
                     cred == 'os_system_reader') and
                        not CONF.enforce_scope.designate):
                    LOG.info('Skipping %s allowed RBAC test because '
                             'enforce_scope.designate is not True', cred)
                    continue
                else:
                    self.fail('Credential {} "expected_allowed" for RBAC '
                              'testing was not created by tempest '
                              'credentials setup. This is likely a bug in the '
                              'test.'.format(cred))
            method = self._get_client_method(cred_obj, client_str, method_str)
            try:
                # Get the result body
                result = method(*args, **kwargs)[1]
            except exceptions.Forbidden as e:
                self.fail('Method {}.{} failed to allow access via RBAC using '
                          'credential {}. Error: {}'.format(
                              client_str, method_str, cred, str(e)))
            # Remove the root element
            result_objs = next(iter(result.values()))

            result_ids = [result_obj["id"] for result_obj in result_objs]
            self.assertTrue(set(expected_ids).issubset(set(result_ids)))
