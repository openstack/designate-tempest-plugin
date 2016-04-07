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
from tempest.lib.common.utils import data_utils


def rand_zone_name():
    """Generate a random zone name
    :return: a random zone name e.g. example.org.
    :rtype: string
    """
    return '%s.com.' % data_utils.rand_name()


def rand_email(domain=None):
    """Generate a random zone name
    :return: a random zone name e.g. example.org.
    :rtype: string
    """
    domain = domain or rand_zone_name()
    return 'example@%s' % domain.rstrip('.')


def rand_ttl(start=1, end=86400):
    """Generate a random TTL value
    :return: a random ttl e.g. 165
    :rtype: string
    """
    return data_utils.rand_int_id(start, end)
