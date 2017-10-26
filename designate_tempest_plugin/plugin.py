# Copyright 2016 NEC Corporation.  All rights reserved.
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

import os

from tempest import config
from tempest.test_discover import plugins

from designate_tempest_plugin import config as project_config


class DesignateTempestPlugin(plugins.TempestPlugin):
    """
    A DesignateTempestPlugin class provides the basic hooks for an external
    plugin to provide tempest the necessary information to run the plugin.
    """
    def load_tests(self):
        """
        Method to return the information necessary to load the tests in the
        plugin.

        :return: a tuple with the first value being the test_dir and the second
                 being the top_level
        :return type: tuple
        """
        base_path = os.path.split(os.path.dirname(
            os.path.abspath(__file__)))[0]
        test_dir = "designate_tempest_plugin/tests"
        full_test_dir = os.path.join(base_path, test_dir)
        return full_test_dir, base_path

    def register_opts(self, conf):
        """
        Add additional configuration options to tempest.

        This method will be run for the plugin during the register_opts()
        function in tempest.config

        Parameters:
        conf (ConfigOpts): The conf object that can be used to register
        additional options on.
        """
        config.register_opt_group(conf, project_config.service_available_group,
                                  project_config.ServiceAvailableGroup)
        config.register_opt_group(conf, project_config.dns_group,
                                  project_config.DnsGroup)
        config.register_opt_group(conf, project_config.dns_feature_group,
                                  project_config.DnsFeatureGroup)

    def get_opt_lists(self):
        """
        Get a list of options for sample config generation

        Return option_list: A list of tuples with the group name
                            and options in that group.
        Return type: list
        """
        return [
            (project_config.service_available_group.name,
             project_config.ServiceAvailableGroup),
            (project_config.dns_group.name,
             project_config.DnsGroup),
            (project_config.dns_feature_group.name,
             project_config.DnsFeatureGroup),
        ]

    def get_service_clients(self):
        dns_config = config.service_client_config('dns')
        admin_params = {
            'name': 'dns_admin',
            'service_version': 'dns.admin',
            'module_path': 'designate_tempest_plugin.services.dns.admin',
            'client_names': ['QuotasClient']
        }
        v2_params = {
            'name': 'dns_v2',
            'service_version': 'dns.v2',
            'module_path': 'designate_tempest_plugin.services.dns.v2',
            'client_names': ['BlacklistsClient', 'PoolClient', 'QuotasClient',
                             'RecordsetClient', 'TldClient',
                             'TransferAcceptClient', 'TransferRequestClient',
                             'TsigkeyClient', 'ZoneExportsClient',
                             'ZoneImportsClient', 'ZonesClient']
        }
        admin_params.update(dns_config)
        v2_params.update(dns_config)
        return [admin_params, v2_params]
