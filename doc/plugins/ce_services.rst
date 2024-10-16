.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_ce.ce_services:

===================
spin_ce.ce_services
===================

The ``spin_ce.ce_services`` plugin provides a way to start and stop services
required by CONTACT Elements instances by using the `ce_services`_ command-line
tool.

The plugin also provisions the necessary tools to run the services, like
`traefik`_, `Apache Solr`_, and others.

How to setup the ``spin_ce.ce_services`` plugin?
################################################

For using the ``spin_ce.ce_services`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` for ``spin_ce.ce_services``

    plugin_packages:
        - spin_ce
        - spin_frontend # required by spin_ce
        - spin_python
    plugins:
        - spin_ce.ce_services
    python:
        version: '3.11.9'
        index_url: <package server index url to retrieve CE wheels from>
    node:
        version: '18.17.1'

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to start the services for a local CE instance?
##################################################

To start the services required to run a local CE instance, the ``spin ce_services
start`` command can be used. The command will start the services required by the
instance specified in the ``spinfile.yaml``.

.. code-block:: bash
    :caption: Start

    spin ce_services -i <path to instance>

How to use the `HiveMQ`_ service and CE Elements integration?
#######################################################################################

The ``hivemq`` service as well as the CONZTACT Elements HiveMQ integration can
be activated by enabling it within the configuration of ``ce_services``.

.. code-block:: yaml
    :caption: Enable HiveMQ service within ``spinfile.yaml``

    ce_services:
        hivemq:
            enabled: true

(Re-)provision may be required to apply the changes.

How to enable the `InfluxDB`_ service?
####################################################################

The ``influxdb`` service can be enabled by setting the ``enabled`` property to
``true`` within the configuration of ``ce_services``.

.. code-block:: yaml
    :caption: Enable InfluxDB service within ``spinfile.yaml``

    ce_services:
        influxdb:
            enabled: true

(Re-)provision may be required to apply the changes.

How to pass additional options and flags to the `ce_services`_?
###############################################################

Except for the ``-i`` / ``--instance`` option, a additional flags and options
passed to the ``ce_services`` task are passed to the `ce_services`_ command-line
tool as shown below:

.. code-block:: bash
    :caption: Pass additional flags and options to ``ce_services``

    spin ce_services -i <path to instance> --<flag> <value>

How to configure services and their options?
############################################

Since the ``spin_ce.ce_services`` plugin is based on the `ce_services`_ tool,
the configuration of the services and their options is done via the
``setup.cfg`` or ``pyproject.toml`` file of the project. For more information
about the configuration of the services, please refer to `ce_services`_.

``spin_ce.ce_services`` schema reference
########################################

.. include:: ce_services_schemaref.rst
