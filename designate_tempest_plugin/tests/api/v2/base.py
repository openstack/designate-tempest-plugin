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

from designate_tempest_plugin import clients


class BaseDnsTest(test.BaseTestCase):
    """Base class for DNS API v2 tests."""

    # Use the Designate Client Manager
    client_manager = clients.Manager

    # NOTE(andreaf) credentials holds a list of the credentials to be allocated
    # at class setup time. Credential types can be 'primary', 'alt', 'admin' or
    # a list of roles - the first element of the list being a label, and the
    # rest the actual roles.
    # NOTE(kiall) primary will result in a manager @ cls.os, alt will have
    # cls.os_alt, and admin will have cls.os_adm.
    credentials = ['primary']
