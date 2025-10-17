.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _csspin_ce.pkgtest:

=================
csspin_ce.pkgtest
=================

The ``csspin_ce.pkgtest`` plugin provides a way to run package tests for CONTACT
Elements instances by using the `pkgtest`_ command-line tool.

How to setup the ``csspin_ce.pkgtest`` plugin?
##############################################

For using the ``csspin_ce.pkgtest`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` for ``csspin_ce.pkgtest``

    plugin_packages:
        - csspin-ce
        - csspin-java
        - csspin-python
    plugins:
        - csspin_ce.pkgtest
    contact_elements:
        umbrella: <The umbrella to use>
    python:
        version: '3.11.9'
    pkgtest:
        name: cs.template
        package: dist/cs.template-*.whl
        caddok_package_server_index_url: <index URL to retrieve wheels from>
    java:
        version: '17'

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to run package tests for a local CE instance?
#################################################

To run the package tests required to run a local CE instance, the ``spin
pkgtest`` command can be used.

Additional options and arguments are passed to the underlying `pkgtest`_
command-line tool.

How to install additional packages required for testing a package?
##################################################################

Additional packages required during tests can be configured as follows:

.. code-block:: yaml
    :caption: Additional packages required for testing a package

    pkgtest:
        ...
        additional_packages:
            - dist/cs.templatetest-*.whl

How to skip or configure executing the acceptance tests?
#########################################################

Some projects may not require to execute acceptance tests. To skip the execution
of acceptance tests, set the ``tests`` key to an empty string.

.. code-block:: yaml
    :caption: Skip acceptance tests

    pkgtest:
        ...
        tests: ""

Other projects may require to execute a custom command for executing the
acceptance tests. This can be achieved by modifying the ``test_command``
property.

.. code-block:: yaml
    :caption: Custom test command

    pkgtest:
        ...
        test_command: <Custom test command>

``csspin_ce.pkgtest`` schema reference
######################################

.. include:: pkgtest_schemaref.rst
