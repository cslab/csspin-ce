.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
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
    :caption: Minimal configuration of ``spinfile.yaml`` for ``spin_ce.cdbpkg``

    plugin_packages:
        - spin_ce
    plugins:
        - spin_ce.cdbpkg

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to pass additional options and arguments to the ``spin_ce.cdbpkg`` command?
###########################################################################

Except for the ``-D`` / ``--instance_dir`` option, all additional flags and options
are passed to the ``cdbpkg`` command-line tool.

.. code-block:: bash
    :caption: Pass additional flags and options to ``cdbpkg``

    spin cdbpkg -D <path to instance> <subcommand> <arguments or options>

``spin_ce.cdbpkg`` schema reference
###################################

.. include:: cdbpkg_schemaref.rst
