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
import random
from string import ascii_lowercase

import netaddr
from oslo_log import log as logging
from tempest import config
from tempest.lib.common.utils import data_utils

LOG = logging.getLogger(__name__)
CONF = config.CONF


def rand_ip():
    return ".".join(str(random.randrange(0, 256)) for _ in range(4))


def rand_ipv6():
    def hexes(n):
        return "".join(random.choice("1234567890abcdef") for _ in range(n))
    result = ":".join(hexes(4) for _ in range(8))
    an = netaddr.IPAddress(result, version=6)
    return an.format(netaddr.ipv6_compact)


def rand_zone_name(name='', prefix='rand', suffix=None):
    """Generate a random zone name
    :param str name: The name that you want to include
    :param prefix: the exact text to start the string. Defaults to "rand"
    :param suffix: the exact text to end the string
    :return: a random zone name e.g. example.org.
    :rtype: string
    """
    if suffix is None:
        suffix = '.{}.'.format(CONF.dns.tld_suffix)
    name = data_utils.rand_name(name=name, prefix=prefix)
    return name + suffix


def rand_email(domain=None):
    """Generate a random zone name
    :return: a random zone name e.g. example.org.
    :rtype: string
    """
    domain = domain or rand_zone_name()
    return 'example@%s' % domain.rstrip('.')


def rand_ttl(start=0, end=86400):
    """Generate a random TTL value
    :return: a random ttl e.g. 165
    :rtype: string
    """
    start = max(start, CONF.dns.min_ttl)
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
        ttl = rand_ttl()

    return zone_base.replace('&', name).replace('#', str(ttl))


def rand_quotas(zones=None, zone_records=None, zone_recordsets=None,
                recordset_records=None, api_export_size=None):
    quotas_dict = {
        'zones':
            zones or data_utils.rand_int_id(100, 999999),
        'zone_records':
            zone_records or data_utils.rand_int_id(100, 999999),
        'zone_recordsets':
            zone_recordsets or data_utils.rand_int_id(100, 999999),
        'recordset_records':
            recordset_records or data_utils.rand_int_id(100, 999999),
        'api_export_size':
            api_export_size or data_utils.rand_int_id(100, 999999)
    }

    return quotas_dict


def rand_zone_data(name=None, email=None, ttl=None, description=None):
    """Generate random zone data, with optional overrides
    :return: A ZoneModel
    """
    if name is None:
        name = rand_zone_name(
            prefix='testdomain', suffix='.{}.'.format(CONF.dns.tld_suffix))
    if email is None:
        email = ("admin@" + name).strip('.')
    if description is None:
        description = rand_zone_name(prefix='Description ', suffix='')
    if ttl is None:
        ttl = rand_ttl()
    return {
        'name': name,
        'email': email,
        'ttl': ttl,
        'description': description}


def rand_recordset_data(record_type, zone_name, name=None, records=None,
                        ttl=None, number_of_records=None):
    """Generate random recordset data, with optional overrides
    :return: A RecordsetModel
    """
    if name is None:
        name = rand_zone_name(prefix=record_type, suffix='.' + zone_name)
    if records is None:
        records = [rand_ip()]
    if number_of_records:
        records = [rand_ip() for r in range(number_of_records)]
    if ttl is None:
        ttl = rand_ttl()
    return {
        'type': record_type,
        'name': name,
        'records': records,
        'ttl': ttl}


def rand_a_recordset(zone_name, ips=None, **kwargs):
    if ips is None:
        return rand_recordset_data(
            'A', zone_name, records=[rand_ip()], **kwargs)
    else:
        return rand_recordset_data('A', zone_name, records=ips, **kwargs)


def rand_aaaa_recordset(zone_name, ip=None, **kwargs):
    if ip is None:
        ip = rand_ipv6()
    return rand_recordset_data('AAAA', zone_name, records=[ip], **kwargs)


def rand_cname_recordset(zone_name, cname=None, **kwargs):
    if cname is None:
        cname = zone_name
    return rand_recordset_data('CNAME', zone_name, records=[cname], **kwargs)


def rand_mx_recordset(zone_name, pref=None, host=None, **kwargs):
    if pref is None:
        pref = str(random.randint(0, 65535))
    if host is None:
        host = rand_zone_name(prefix='mail', suffix='.' + zone_name)
    data = "{0} {1}".format(pref, host)
    return rand_recordset_data('MX', zone_name, records=[data], **kwargs)


def rand_spf_recordset(zone_name, data=None, **kwargs):
    data = data or '"v=spf1 +all"'
    return rand_recordset_data('SPF', zone_name, records=[data], **kwargs)


def rand_srv_recordset(zone_name, data=None):
    data = data or "10 0 8080 %s.%s" % (rand_zone_name(suffix=''), zone_name)
    return rand_recordset_data('SRV', zone_name,
                               name="_sip._tcp.%s" % zone_name,
                               records=[data])


def rand_sshfp_recordset(zone_name, algorithm_number=None,
                         fingerprint_type=None, fingerprint=None,
                         **kwargs):
    algorithm_number = algorithm_number or 2
    fingerprint_type = fingerprint_type or 1
    fingerprint = fingerprint or "123456789abcdef67890123456789abcdef67890"

    data = "%s %s %s" % (algorithm_number, fingerprint_type, fingerprint)
    return rand_recordset_data('SSHFP', zone_name, records=[data], **kwargs)


def rand_txt_recordset(zone_name, data=None, **kwargs):
    data = data or '"v=spf1 +all"'
    return rand_recordset_data('TXT', zone_name, records=[data], **kwargs)


def wildcard_ns_recordset(zone_name):
    name = "*.{0}".format(zone_name)
    records = ["ns.example.{}.".format(CONF.dns.tld_suffix)]
    return rand_recordset_data('NS', zone_name, name, records)


def rand_ns_records():
    ns_zone = rand_zone_name()
    ns_records = []
    # Make sure we don't have equal priority here which causes test failures
    # when doing sorted comparisons
    for i in range(0, 2):
        ns_records.append({"hostname": "ns%s.%s" % (i, ns_zone),
                           "priority": (random.randint(1, 999) + i)})
    return ns_records


def rand_soa_records(number_of_records=2):
    return ['{} {} {} {} {} {}.'.format(
        '{}.{}.{}'.format(rand_string(3), rand_string(7), rand_string(3)),
        random.randint(1000000000, 2020080302), random.randint(3000, 7200),
        random.randint(1000, 3600), random.randint(1000000, 1209600),
        random.randint(1000, 3600)) for i in range(0, number_of_records)]


def rand_soa_recordset(zone_name, **kwargs):
    return rand_recordset_data(
        'SOA', zone_name, records=rand_soa_records(), **kwargs)


def rand_tld():
    data = {
        "name": rand_zone_name(prefix='tld', suffix='')
    }
    return data


def rand_transfer_request_data(description=None, target_project_id=None):
    """Generate random transfer request data, with optional overrides
    :return: A TransferRequest data
    """

    data = {}

    if description is None:
        data['description'] = data_utils.rand_name(prefix='Description ')

    if target_project_id:
        data['target_project_id'] = target_project_id

    return data


def rand_tsig_algorithm():
    algorithm = ['hmac-md5', 'hmac-sha1', 'hmac-sha224', 'hmac-sha256',
                 'hmac-sha384', 'hmac-sha512']
    return random.choice(algorithm)


def rand_tsig_scope():
    scope = ["ZONE", "POOL"]
    return random.choice(scope)


def make_rand_recordset(zone_name, record_type):
    """Create a rand recordset by type
    This essentially just dispatches to the relevant random recordset
    creation functions.
    :param str zone_name: The zone name the recordset applies to
    :param str record_type: The type of recordset (ie A, MX, NS, etc...)
    """

    func = globals()["rand_{}_recordset".format(record_type.lower())]
    return func(zone_name)


def rand_string(size):
    """Create random string of ASCII chars by size
    :param int size - length os the string to be create
    :return - random creates string of ASCII lover characters
    """
    return ''.join(random.choice(ascii_lowercase) for _ in range(size))


def rand_domain_name(tld=None):
    """Create random valid domain name
    :param tld (optional) - TLD that will be used to random domain name
    :return - valid domain name, for example: paka.zbabun.iuh
    """
    domain_tld = tld or rand_string(3)
    return rand_string(4) + '.' + rand_string(6) + '.' + domain_tld + '.'
