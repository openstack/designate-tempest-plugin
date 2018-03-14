========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/designate-tempest-plugin.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

.. Change things from this point on

================================
Tempest Integration of Designate
================================

This directory contains Tempest tests to cover the designate project, as well
as a plugin to automatically load these tests into tempest.

See the tempest plugin docs for information on using it:
https://docs.openstack.org/tempest/latest/plugin.html#using-plugins

See the designate docs for information on writing new tests etc:
https://docs.openstack.org/designate-tempest-plugin/latest/#writing-new-tests

Running the tests
-----------------

To run all tests from this plugin, install designate into your environment
and from the tempest repo, run::

    $ tox -e all-plugin -- designate

To run a single test case, run with the test case name, for example::

    $ tox -e all-plugin -- designate_tempest_plugin.tests.api.v2.test_zones.ZonesAdminTest.test_get_other_tenant_zone

To run all tempest tests including this plugin, run::

    $ tox -e all-plugin
