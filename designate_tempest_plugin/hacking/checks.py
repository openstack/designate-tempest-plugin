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

from tempest.hacking import checks


def factory(register):
    # Imported from Tempest
    register(checks.import_no_clients_in_api_and_scenario_tests)
    register(checks.scenario_tests_need_service_tags)
    register(checks.no_setup_teardown_class_for_tests)
    register(checks.no_vi_headers)
    register(checks.service_tags_not_in_module_path)
    register(checks.no_hyphen_at_end_of_rand_name)
    register(checks.no_mutable_default_args)
    register(checks.no_testtools_skip_decorator)
    register(checks.get_resources_on_service_clients)
    register(checks.delete_resources_on_service_clients)
    register(checks.dont_use_config_in_tempest_lib)
    register(checks.use_rand_uuid_instead_of_uuid4)
