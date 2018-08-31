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
from oslo_config import cfg

service_available_group = cfg.OptGroup(name="service_available",
                                       title="Available OpenStack Services")

ServiceAvailableGroup = [
    cfg.BoolOpt("designate",
                default=True,
                help="Whether or not designate is expected to be available."),
]

dns_group = cfg.OptGroup(name='dns',
                         title='DNS service options')

DnsGroup = [
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the DNS service"),
    cfg.StrOpt('catalog_type',
               default='dns',
               help="Catalog type of the DNS service"),
    cfg.IntOpt('build_interval',
               default=1,
               help="Time in seconds between build status checks."),
    cfg.IntOpt('build_timeout',
               default=360,
               help="Timeout in seconds to wait for an resource to build."),
    cfg.IntOpt('min_ttl',
               default=1,
               help="The minimum value to respect when generating ttls"),
    cfg.ListOpt('nameservers',
                default=[],
                help="The nameservers to check for change going live"),
    cfg.IntOpt('query_timeout',
               default=1,
               help="The timeout on a single dns query to a nameserver"),
    cfg.StrOpt('zone_id',
               help="The target zone to test the dns recordsets "
                    "If it is not specified, a new zone will be created ")

]

dns_feature_group = cfg.OptGroup(name='dns_feature_enabled',
                                 title='Enabled Designate Features')

DnsFeatureGroup = [
    cfg.BoolOpt('api_v1',
                default=False,
                help="Is the v1 dns API enabled."),
    cfg.BoolOpt('api_v2',
                default=True,
                help="Is the v2 dns API enabled."),
    cfg.BoolOpt('api_admin',
                default=True,
                help="Is the admin dns API enabled."),
    cfg.BoolOpt('api_v1_servers',
                default=False,
                help="Is the v1 dns servers API enabled."),
    cfg.BoolOpt('api_v2_root_recordsets',
                default=False,
                help="Is the v2 root recordsets API enabled."),
    cfg.BoolOpt('api_v2_quotas',
                default=False,
                help="Is the v2 quota API enabled."),
    cfg.BoolOpt('api_v2_quotas_verify_project',
                default=False,
                help="Is project IDs verified when setting v2 quotas. "
                "Must be set to True starting from Rocky release."),
    cfg.BoolOpt('bug_1573141_fixed',
                default=True,
                help="Is https://bugs.launchpad.net/designate/+bug/1573141 "
                "fixed"),
]
