# Copyright 2021 Red Hat.
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


class InvalidStatusError(Exception):
    """
    Exception raised when an entity changes to an unexpected status.
    """

    def __init__(self, entity, entity_id, status, expected_status=None):
        if expected_status:
            message = ("{0} with ID {1} returned status {2} when {3} was "
                       "expected.".format(entity, entity_id,
                                          status, expected_status))
        else:
            message = ("{0} with ID {1} returned unexpected status {2}".format(
                entity, entity_id, status))
        super(InvalidStatusError, self).__init__(message)
