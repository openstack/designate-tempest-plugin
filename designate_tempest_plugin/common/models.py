"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


class ZoneFile(object):

    def __init__(self, origin, ttl, records):
        self.origin = origin
        self.ttl = ttl
        self.records = records

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_text(cls, text):
        """Return a ZoneFile from a string containing the zone file contents"""
        # filter out empty lines and strip all leading/trailing whitespace.
        # this assumes no multiline records
        lines = [x.strip() for x in text.split('\n') if x.strip()]

        assert lines[0].startswith('$ORIGIN')

        # Handle zone files with and without $TTL directive
        if lines[1].startswith('$TTL'):
            # New format with $TTL directive
            ttl = int(lines[1].split(' ')[1])
            record_start = 2
        else:
            # Old format without $TTL directive
            ttl = None
            record_start = 1

        return ZoneFile(
            origin=lines[0].split(' ')[1],
            ttl=ttl,
            records=[ZoneFileRecord.from_text(x)
                     for x in lines[record_start:]],
        )


class ZoneFileRecord(object):

    def __init__(self, name, type, data):
        self.name = str(name)
        self.type = str(type)
        self.data = str(data)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    @classmethod
    def from_text(cls, text):
        """Create a ZoneFileRecord from a line of text of a zone file, like:

            mydomain.com. IN NS ns1.example.com.
            mydomain.com. 3600 IN NS ns1.example.com.
        """
        parts = text.split(None, 4)

        # Check if second field is numeric (inline TTL)
        if len(parts) >= 5 and parts[1].isdigit():
            name, _ttl, rclass, rtype, data = parts
        elif len(parts) >= 4:
            name = parts[0]
            rclass = parts[1]
            rtype = parts[2]
            data = parts[3] if len(parts) == 4 else ' '.join(parts[3:])
        else:
            raise ValueError(f"Unexpected record format: {text}")

        assert rclass == 'IN'
        return cls(name=name, type=rtype, data=data)
