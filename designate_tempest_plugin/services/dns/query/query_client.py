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
import dns
import dns.exception
import dns.name
import dns.query
import dns.tsigkeyring
from tempest import config
from oslo_utils import netutils

CONF = config.CONF


class QueryClient(object):
    """A client which queries multiple nameservers"""

    def __init__(self, nameservers=None, query_timeout=None,
                 build_interval=None, build_timeout=None,
                 tsig_key_name=None, tsig_key_secret=None,
                 tsig_key_algorithm=None):
        self.nameservers = nameservers or CONF.dns.nameservers
        self.query_timeout = query_timeout or CONF.dns.query_timeout
        self.build_interval = build_interval or CONF.dns.build_interval
        self.build_timeout = build_timeout or CONF.dns.build_timeout
        self.clients = [SingleQueryClient(
                            ns, query_timeout=self.query_timeout,
                            tsig_key_name=tsig_key_name,
                            tsig_key_secret=tsig_key_secret,
                            tsig_key_algorithm=tsig_key_algorithm)
                        for ns in self.nameservers]

    def query(self, zone_name, rdatatype):
        if not self.nameservers:
            raise ValueError('Nameservers list cannot be empty and it should '
                             'contain DNS backend IPs to "dig" for')
        return [c.query(zone_name, rdatatype) for c in self.clients]


class SingleQueryClient(object):
    """A client which queries a single nameserver"""

    def __init__(self, nameserver, query_timeout,
                 tsig_key_name=None, tsig_key_secret=None,
                 tsig_key_algorithm=None):
        self.nameserver = Nameserver.from_str(nameserver)
        self.query_timeout = query_timeout
        self.tsig_key_name = tsig_key_name
        if tsig_key_name and tsig_key_secret:
            self.keyring = dns.tsigkeyring.from_text(
                {tsig_key_name: tsig_key_secret})
            self.tsig_algorithm = dns.name.from_text(
                tsig_key_algorithm or 'hmac-sha256')
        else:
            self.keyring = None
            self.tsig_algorithm = None

    def query(self, name, rdatatype):
        return self._dig(name, rdatatype, self.nameserver.ip,
                         self.nameserver.port, timeout=self.query_timeout)

    def _prepare_query(self, zone_name, rdatatype):
        if isinstance(rdatatype, str):
            rdatatype = dns.rdatatype.from_text(rdatatype)
        dns_message = dns.message.make_query(zone_name, rdatatype)
        dns_message.set_opcode(dns.opcode.QUERY)
        if self.keyring:
            dns_message.use_tsig(
                keyring=self.keyring, keyname=self.tsig_key_name,
                algorithm=self.tsig_algorithm)
        return dns_message

    def _dig(self, name, rdatatype, ip, port, timeout):
        query = self._prepare_query(name, rdatatype)
        return dns.query.udp(query, ip.strip('[]'), port=port, timeout=timeout)


class Nameserver(object):

    def __init__(self, ip, port=53):
        self.ip = ip
        self.port = port

    def __str__(self):
        return "%s:%s" % (self.ip, self.port)

    def __repr__(self):
        return str(self)

    @classmethod
    def from_str(self, nameserver):
        ip, port = netutils.parse_host_port(nameserver)
        if port:
            return Nameserver(ip, port)
        return Nameserver(nameserver)
