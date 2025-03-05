.. -*- coding: utf-8 -*-
   Copyright (C) 2025 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_ce.ce_support_tools:

========================
spin_ce.ce_support_tools
========================

The ``spin_ce.ce_support_tools`` plugin provides a wrapper for the ce_support_tools package.

How to setup the ``spin_ce.ce_support_tools`` plugin?
#####################################################

For using the ``spin_ce.ce_support_tools`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Configuring ``spin_ce.ce_support_tools`` in ``spinfile.yaml``

    plugin_packages:
        - spin_ce
    plugins:
        - spin_ce:
            - mkinstance  # Required for instance location
            - ce_support_tools
    # ... other configurations depending on spin_ce.mkinstance's requirements.

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to pass additional options and arguments to the ``pyperf`` task?
####################################################################

Except for the ``-D`` / ``--instancedir`` option, all additional flags and
options are passed to the ``pyperf`` command-line tool.

.. code-block:: console
    :caption: Pass additional flags and options to ``pyperf``

    spin pyperf [-D <path to instance> | options] <cmd> <cmd-options>

Examples
########

Run performance tests:

.. code-block:: console
    :caption: Check the configuration of cs.template

    spin pyperf run
