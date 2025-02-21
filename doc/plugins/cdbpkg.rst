.. -*- coding: utf-8 -*-
   Copyright (C) 2025 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_ce.cdbpkg:

==============
spin_ce.cdbpkg
==============

The ``spin_ce.cdbpkg`` plugin provides a wrapper for the cdbpkg command.

How to setup the ``spin_ce.cdbpkg`` plugin?
###########################################

For using the ``spin_ce.cdbpkg`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Configuring ``spin_ce.cdbpkg`` in ``spinfile.yaml``

    plugin_packages:
        - spin_ce
    plugins:
        - spin_ce:
            - mkinstance  # Required for instance location
            - cdbpkg
    # ... other configurations depending on spin_ce.mkinstance's requirements.

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to pass additional options and arguments to the ``spin_ce.cdbpkg`` command?
###############################################################################

Except for the ``-D`` / ``--instancedir`` option, all additional flags and
options are passed to the ``cdbpkg`` command-line tool.

.. code-block:: console
    :caption: Pass additional flags and options to ``cdbpkg``

    spin cdbpkg [-D <path to instance> | options] <cmd> <cmd-options>

Examples
########

Check a specific package:

.. code-block:: console
    :caption: Check the configuration of cs.template

    spin cdbpkg check cs.template

Build package with force flag:

.. code-block:: console
    :caption: Force-build

    spin cdbpkg build --force


``spin_ce.cdbpkg`` schema reference
###################################

.. include:: cdbpkg_schemaref.rst
