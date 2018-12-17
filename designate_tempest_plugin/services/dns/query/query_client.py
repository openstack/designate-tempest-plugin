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
import dns.query
import six
from tempest import config

CONF = config.CONF


class QueryClient(object):
    """A client which queries multiple nameservers"""

    def __init__(self, nameservers=None, query_timeout=None,
                 build_interval=None, build_timeout=None):
        self.nameservers = nameservers or []
        self.query_timeout = query_timeout or CONF.dns.query_timeout
        self.build_interval = build_interval or CONF.dns.build_interval
        self.build_timeout = build_timeout or CONF.dns.build_timeout

        self.clients = [SingleQueryClient(ns, query_timeout=query_timeout)
                        for ns in nameservers]

    def query(self, zone_name, rdatatype):
        return [c.query(zone_name, rdatatype) for c in self.clients]


class SingleQueryClient(object):
    """A client which queries a single nameserver"""

    def __init__(self, nameserver, query_timeout):
        self.nameserver = Nameserver.from_str(nameserver)
        self.query_timeout = query_timeout

    def query(self, name, rdatatype):
        return self._dig(name, rdatatype, self.nameserver.ip,
                         self.nameserver.port, timeout=self.query_timeout)

    @classmethod
    def _prepare_query(cls, zone_name, rdatatype):
        # support plain strings: "SOA", "A"
        if isinstance(rdatatype, six.string_types):
            rdatatype = dns.rdatatype.from_text(rdatatype)
        dns_message = dns.message.make_query(zone_name, rdatatype)
        dns_message.set_opcode(dns.opcode.QUERY)
        return dns_message

    @classmethod
    def _dig(cls, name, rdatatype, ip, port, timeout):
        query = cls._prepare_query(name, rdatatype)
        return dns.query.udp(query, ip, port=port, timeout=timeout)


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
        if ':' in nameserver:
            ip, port = nameserver.split(':')
            return Nameserver(ip, int(port))
        return Nameserver(nameserver)
