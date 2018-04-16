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

import time

from oslo_log import log as logging
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions as lib_exc

LOG = logging.getLogger(__name__)


def wait_for_zone_404(client, zone_id):
    """Waits for a zone to 404."""
    LOG.info('Waiting for zone %s to 404', zone_id)
    start = int(time.time())

    while True:
        time.sleep(client.build_interval)

        try:
            _, zone = client.show_zone(zone_id)
        except lib_exc.NotFound:
            LOG.info('Zone %s is 404ing', zone_id)
            return

        if int(time.time()) - start >= client.build_timeout:
            message = ('Zone %(zone_id)s failed to 404 within the required '
                       'time (%(timeout)s s). Current status: '
                       '%(status_curr)s' %
                       {'zone_id': zone_id,
                        'status_curr': zone['status'],
                        'timeout': client.build_timeout})

            caller = test_utils.find_test_caller()

            if caller:
                message = '(%s) %s' % (caller, message)

            raise lib_exc.TimeoutException(message)


def wait_for_zone_status(client, zone_id, status):
    """Waits for a zone to reach given status."""
    LOG.info('Waiting for zone %s to reach %s', zone_id, status)

    _, zone = client.show_zone(zone_id)
    start = int(time.time())

    while zone['status'] != status:
        time.sleep(client.build_interval)
        _, zone = client.show_zone(zone_id)
        status_curr = zone['status']
        if status_curr == status:
            LOG.info('Zone %s reached %s', zone_id, status)
            return

        if int(time.time()) - start >= client.build_timeout:
            message = ('Zone %(zone_id)s failed to reach status=%(status)s '
                       'within the required time (%(timeout)s s). Current '
                       'status: %(status_curr)s' %
                       {'zone_id': zone_id,
                        'status': status,
                        'status_curr': status_curr,
                        'timeout': client.build_timeout})

            caller = test_utils.find_test_caller()

            if caller:
                message = '(%s) %s' % (caller, message)

            raise lib_exc.TimeoutException(message)


def wait_for_zone_import_status(client, zone_import_id, status):
    """Waits for an imported zone to reach the given status."""
    LOG.info('Waiting for zone import %s to reach %s', zone_import_id, status)

    _, zone_import = client.show_zone_import(zone_import_id)
    start = int(time.time())

    while zone_import['status'] != status:
        time.sleep(client.build_interval)
        _, zone_import = client.show_zone_import(zone_import_id)
        status_curr = zone_import['status']
        if status_curr == status:
            LOG.info('Zone import %s reached %s', zone_import_id, status)
            return

        if int(time.time()) - start >= client.build_timeout:
            message = ('Zone import %(zone_import_id)s failed to reach '
                       'status=%(status)s within the required time '
                       '(%(timeout)s s). Current '
                       'status: %(status_curr)s' %
                       {'zone_import_id': zone_import_id,
                        'status': status,
                        'status_curr': status_curr,
                        'timeout': client.build_timeout})

            caller = test_utils.find_test_caller()

            if caller:
                message = '(%s) %s' % (caller, message)

            raise lib_exc.TimeoutException(message)


def wait_for_zone_export_status(client, zone_export_id, status):
    """Waits for an exported zone to reach the given status."""
    LOG.info('Waiting for zone export %s to reach %s', zone_export_id, status)

    _, zone_export = client.show_zone_export(zone_export_id)
    start = int(time.time())

    while zone_export['status'] != status:
        time.sleep(client.build_interval)
        _, zone_export = client.show_zone_export(zone_export_id)
        status_curr = zone_export['status']
        if status_curr == status:
            LOG.info('Zone export %s reached %s', zone_export_id, status)
            return

        if int(time.time()) - start >= client.build_timeout:
            message = ('Zone export %(zone_export_id)s failed to reach '
                       'status=%(status)s within the required time '
                       '(%(timeout)s s). Current '
                       'status: %(status_curr)s' %
                       {'zone_export_id': zone_export_id,
                        'status': status,
                        'status_curr': status_curr,
                        'timeout': client.build_timeout})

            caller = test_utils.find_test_caller()

            if caller:
                message = '(%s) %s' % (caller, message)

            raise lib_exc.TimeoutException(message)


def wait_for_recordset_status(client, zone_id, recordset_id, status):
    """Waits for a recordset to reach the given status."""
    LOG.info('Waiting for recordset %s to reach %s',
             recordset_id, status)

    _, recordset = client.show_recordset(zone_id, recordset_id)
    start = int(time.time())

    while recordset['status'] != status:
        time.sleep(client.build_interval)
        _, recordset = client.show_recordset(zone_id, recordset_id)
        status_curr = recordset['status']
        if status_curr == status:
            LOG.info('Recordset %s reached %s', recordset_id, status)
            return

        if int(time.time()) - start >= client.build_timeout:
            message = ('Recordset %(recordset_id)s failed to reach '
                       'status=%(status)s within the required time '
                       '(%(timeout)s s). Current '
                       'status: %(status_curr)s' %
                       {'recordset_id': recordset_id,
                        'status': status,
                        'status_curr': status_curr,
                        'timeout': client.build_timeout})

            caller = test_utils.find_test_caller()

            if caller:
                message = '(%s) %s' % (caller, message)

            raise lib_exc.TimeoutException(message)


def wait_for_query(client, name, rdatatype, found=True):
    """Query nameservers until the record of the given name and type is found.

    :param client: A QueryClient
    :param name: The record name for which to query
    :param rdatatype: The record type for which to query
    :param found: If True, wait until the record is found. Else, wait until the
        record disappears.
    """
    state = "found" if found else "removed"
    LOG.info("Waiting for record %s of type %s to be %s on nameservers %s",
             name, rdatatype, state, client.nameservers)
    start = int(time.time())

    while True:
        time.sleep(client.build_interval)

        responses = client.query(name, rdatatype)
        if found:
            all_answers_good = all(r.answer for r in responses)
        else:
            all_answers_good = all(not r.answer for r in responses)

        if not client.nameservers or all_answers_good:
            LOG.info("Record %s of type %s was successfully %s on nameservers "
                     "%s", name, rdatatype, state, client.nameservers)
            return

        if int(time.time()) - start >= client.build_timeout:
            message = ('Record %(name)s of type %(rdatatype)s not %(state)s '
                       'on nameservers %(nameservers)s within the required '
                       'time (%(timeout)s s)' %
                       {'name': name,
                        'rdatatype': rdatatype,
                        'state': state,
                        'nameservers': client.nameservers,
                        'timeout': client.build_timeout})

            caller = test_utils.find_test_caller()
            if caller:
                message = "(%s) %s" % (caller, message)

            raise lib_exc.TimeoutException(message)
