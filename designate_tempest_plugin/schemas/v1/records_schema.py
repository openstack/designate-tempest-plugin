# Copyright 2014 Hewlett-Packard Development Company, L.P
# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
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
list_records = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "records": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "created_at": {"type": "string"},
                        "data": {"type": "string"},
                        "description": {"type": "null"},
                        "domain_id": {"type": "string"},
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "priority": {"type": "null"},
                        "ttl": {"type": "null"},
                        "type": {"type": "string"},
                        "updated_at": {
                            "anyOf": [{'type': 'string'}, {"type": "null"}]}
                    },
                    'required': ['id', 'name', 'type', 'data']
                }
            }
        },
        'required': ['records']
    }
}

create_record = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "record": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "data": {"type": "string"},
                    "description": {"type": "null"},
                    "domain_id": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "priority": {"type": "null"},
                    "ttl": {"type": "null"},
                    "type": {"type": "string"},
                    "updated_at": {"type": "null"}
                },
                "required": ['id', 'name', 'type', 'domain_id']
            }
        }
    },
    "required": ['record']
}

update_record = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "record": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "data": {"type": "string"},
                    "description": {"type": "null"},
                    "domain_id": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "priority": {"type": "null"},
                    "ttl": {"type": "null"},
                    "type": {"type": "string"},
                    "updated_at": {"type": "string"}
                },
                "required": ['id', 'name', 'type', 'domain_id']
            }
        }
    },
    "required": ['record']
}

get_record = {
    "status_code": [200],
    "response_body": {
        "type": "object",
        "properties": {
            "record": {
                "type": "object",
                "properties": {
                    "created_at": {"type": "string"},
                    "data": {"type": "string"},
                    "description": {"type": "null"},
                    "domain_id": {"type": "string"},
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "priority": {"type": "null"},
                    "ttl": {"type": "null"},
                    "type": {"type": "string"},
                    "updated_at": {
                        "anyOf": [{'type': 'string'}, {"type": "null"}]}
                },
                "required": ['id', 'name', 'type', 'domain_id']
            }
        }
    },
    "required": ['record']
}

delete_record = {
    'status_code': [200],
}
