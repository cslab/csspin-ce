.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_ce.mkinstance:

==================
spin_ce.mkinstance
==================

The ``spin_ce.mkinstance`` plugin provides a way to create a new CONTACT
Elements instance by using the ``mkinstance`` command-line tool within the
context of cs.spin.

How to setup the ``spin_ce.mkinstance`` plugin?
################################################

For using the ``spin_ce.mkinstance`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` for ``spin_ce.mkinstance``

    plugin_packages:
        - spin_ce
        - spin_frontend # required by spin_ce.mkinstance
        - spin_python
    plugins:
        - spin_ce.mkinstance
    python:
        version: '3.11.9'
        index_url: <package server index url to retrieve CE wheels from>
    node:
        version: '18.17.1'

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to create a new CONTACT Elements instance?
##############################################

To create a new CONTACT Elements instance, the ``spin mkinstance`` command can
be used. The command will create a new instance based on the configuration
specified in the ``spinfile.yaml`` and the plugin.

.. code-block:: bash
    :caption: Create a new instance

    spin mkinstance -i <path to instance>

After the command succeeds, a new instance will be created at the specified
path.

``spin_ce.mkinstance`` schema reference
########################################

.. include:: mkinstance_schemaref.rst
