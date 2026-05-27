# Copyright 2026 Red Hat
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

import subprocess
from itertools import dropwhile

import yaml
from oslo_log import log as logging
from tempest import config

CONF = config.CONF
LOG = logging.getLogger(__name__)


def get_pool_config():
    """Retrieve pool configuration via designate-manage pool show_config.

    Returns a list of pool dicts parsed from the YAML output, or None
    if the command fails or designate-manage is not configured.
    """
    manage_path = CONF.dns_feature_enabled.designate_manage_path
    if not manage_path:
        LOG.warning('designate_manage_path is not configured')
        return None
    try:
        output = subprocess.check_output(
            [manage_path, 'pool', 'show_config', '--all'],
            stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        LOG.error('designate-manage pool show_config failed: %s', e.output)
        return None

    # The output starts with a header line ("Pool Configuration:")
    # followed by a separator, then YAML pool definitions starting
    # with "- also_notifies:".  Drop everything before that.
    lines = output.split('\n\n')[0].splitlines()
    filtered_lines = list(dropwhile(
        lambda ln: ln.strip() != '- also_notifies: []', lines))
    if not filtered_lines:
        LOG.warning('No pool configuration found in designate-manage output')
        return None

    yaml_data = '\n'.join(filtered_lines)
    return yaml.safe_load(yaml_data)


def get_non_default_pool_id():
    """Return the ID of a non-default pool.

    Returns None if no non-default pool is found.
    """
    pools = get_pool_config()
    if not pools:
        return None
    for pool in pools:
        if 'default' not in pool.get('name', 'default'):
            return pool['id']
    return None
