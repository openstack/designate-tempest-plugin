====================
Enabling in Devstack
====================

1. Download DevStack::

    git clone https://opendev.org/openstack/devstack.git
    cd devstack

2. Add this repo as an external repository::

     > cat local.conf
     [[local|localrc]]
     enable_plugin designate-tempest-plugin https://opendev.org/openstack/designate-tempest-plugin

3. run ``stack.sh``

