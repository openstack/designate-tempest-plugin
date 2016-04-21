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
from oslo_log import log as logging
from tempest.lib.common.utils import data_utils

LOG = logging.getLogger(__name__)


def rand_zone_name(name='', prefix=None, suffix='.com.'):
    """Generate a random zone name
    :param str name: The name that you want to include
    :param prefix: the exact text to start the string. Defaults to "rand"
    :param suffix: the exact text to end the string
    :return: a random zone name e.g. example.org.
    :rtype: string
    """
    name = data_utils.rand_name(name=name, prefix=prefix)
    return name + suffix


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


def rand_zonefile_data(name=None, ttl=None):
    """Generate random zone data, with optional overrides

    :return: A ZoneModel
    """
    zone_base = ('$ORIGIN &\n& # IN SOA ns.& nsadmin.& # # # # #\n'
                 '& # IN NS ns.&\n& # IN MX 10 mail.&\nns.& 360 IN A 1.0.0.1')
    if name is None:
        name = rand_zone_name()
    if ttl is None:
        ttl = str(rand_ttl(1200, 8400))

    return zone_base.replace('&', name).replace('#', ttl)


def rand_quotas(zones=None, zone_records=None, zone_recordsets=None,
                recordset_records=None, api_export_size=None):
    LOG.warn("Leaving `api_export_size` out of quota data due to: "
             "https://bugs.launchpad.net/designate/+bug/1573141")
    return {
        'quota': {
            'zones':
                zones or data_utils.rand_int_id(100, 999999),
            'zone_records':
                zone_records or data_utils.rand_int_id(100, 999999),
            'zone_recordsets':
                zone_recordsets or data_utils.rand_int_id(100, 999999),
            'recordset_records':
                recordset_records or data_utils.rand_int_id(100, 999999),
            # https://bugs.launchpad.net/designate/+bug/1573141
            # 'api_export_size':
            #     api_export_size or data_utils.rand_int_id(100, 999999),
        }
    }
