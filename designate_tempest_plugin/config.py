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
               default=0,
               help="The minimum value to respect when generating ttl"),
    cfg.ListOpt('nameservers',
                default=[],
                help="The nameservers to check for change going live"),
    cfg.IntOpt('query_timeout',
               default=3,
               help="The timeout on a single dns query to a nameserver"),
    cfg.StrOpt('zone_id',
               help="The target zone to test the dns recordsets "
                    "If it is not specified, a new zone will be created "),
    cfg.StrOpt('tld_suffix',
               default='test',
               help="TLD suffix that used in all tests (if not overridden).")
]

dns_feature_group = cfg.OptGroup(name='dns_feature_enabled',
                                 title='Enabled Designate Features')

DnsFeatureGroup = [
    cfg.BoolOpt('api_v2',
                default=True,
                help="Is the v2 dns API enabled."),
    cfg.BoolOpt('api_admin',
                default=False,
                help="Is the admin dns API enabled."),
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
                deprecated_for_removal=True,
                deprecated_reason='This bug was fixed in 3.0.0',
                help="Is https://bugs.launchpad.net/designate/+bug/1573141 "
                "fixed"),
    cfg.BoolOpt('bug_1932026_fixed',
                default=False,
                help="Is https://bugs.launchpad.net/designate/+bug/1932026 "
                     "fixed"),
    cfg.StrOpt('designate_manage_path',
               default=None,
               help="The designate-manage command path"),
    # Note: Also see the enforce_scope section (from tempest) for Designate API
    #       scope checking setting.
    cfg.BoolOpt('enforce_new_defaults',
                default=False,
                help='Does the dns service API policies enforce '
                     'the new keystone default roles? This configuration '
                     'value should be same as designate.conf: '
                     '[oslo_policy].enforce_new_defaults option.'),
    cfg.BoolOpt('test_multipool_with_delete_opt',
                default=False,
                help="Is multipool feature being tested with --delete option?"
                     "If it is, it might delete pools that were created in "
                     "other tests."),
]

# Extending this enforce_scope group defined in tempest
enforce_scope_group = cfg.OptGroup(name="enforce_scope",
                                   title="OpenStack Services with "
                                         "enforce scope")
EnforceScopeGroup = [
    cfg.BoolOpt('designate',
                default=False,
                help='Does the dns service API policies enforce '
                     'scope? This configuration value should be same as '
                     'designate.conf: [oslo_policy].enforce_scope option.'),
]
