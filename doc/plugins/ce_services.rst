.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   https://www.contact-software.com/

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

.. _csspin_ce.ce_services:

=====================
csspin_ce.ce_services
=====================

The ``csspin_ce.ce_services`` plugin provides a way to start and stop services
required by CONTACT Elements instances by using the `ce_services`_ command-line
tool.

The plugin also provisions the necessary tools to run the services, like
`traefik`_, `Apache Solr`_, and others.

How to setup the ``csspin_ce.ce_services`` plugin?
##################################################

For using the ``csspin_ce.ce_services`` plugin, a project's ``spinfile.yaml``
must at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` for ``csspin_ce.ce_services``

    plugin_packages:
        - csspin-ce
        - csspin-frontend
        - csspin-java
        - csspin-python
    plugins:
        - csspin_ce.ce_services
    python:
        version: '3.11.9'
        index_url: <package server index url to retrieve CE wheels from>
    node:
        version: '18.17.1'
    java:
        version: '17'

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to start the services for a local CE instance?
##################################################

To start the services required to run a local CE instance, the ``spin ce-services
start`` command can be used. The command will start the services required by the
instance specified in the ``spinfile.yaml``.

.. code-block:: bash
    :caption: Start

    spin ce-services -i <path to instance>

How to configure services and their options?
############################################

Since the ``csspin_ce.ce_services`` plugin is based on the `ce_services`_ tool,
the configuration of the services and their options is done via the
``setup.cfg`` or ``pyproject.toml`` file of the project. For more information
about the configuration of the services, please refer to `ce_services`_.

SSL/TLS support
###############

Some use cases require accessing the CONTACT Elements instances via TLS/SSL. To
enable this feature, an instance must be built with the ``--sslca`` option
pointing to a valid TLS certificate file. This can be achieved by running the
``mkinstance`` task with enabled ``mkinstance.tls.enabled``. This automatically
generates a new certificate and key and sets ``--sslca`` accordingly.

To now run the services with TLS/SSL enabled,
``ce_services.traefik.tls.enabled`` must be set,
``ce_services.traefik.tls.cert`` and ``ce_services.traefik.tls.cert_key``
pointing per default to the certificate and key file generated during the
``mkinstance`` task execution. The services can be started as usual.

.. code-block:: yaml
    :caption: Sample ``spinfile.yaml`` for starting services with enabled SSL/TLS

    ...
    ce_services:
        traefik:
            tls:
                enabled: true
    mkinstance:
        tls:
            enabled: true

How to use the `HiveMQ`_ service and CE Elements integration?
#############################################################

The ``hivemq`` service as well as the CONTACT Elements HiveMQ integration can be
used by enabling it within the configuration of ``ce_services``. While HiveMQ
can be provisioned using ``spin provision``, the CONTACT Elements HiveMQ
integration must be installed manually, e.g. by downloading it from the customer
portal.

.. code-block:: yaml
    :caption: Enable HiveMQ service within ``spinfile.yaml``

    ce_services:
        hivemq:
            enabled: true
            elements_integration:
                install_dir: <path to CONTACT Elements HiveMQ integration installation directory>


(Re-) provision may be required to apply the changes.

How to enable the `InfluxDB`_ service?
######################################

The ``influxdb`` service can be enabled by setting the ``enabled`` property to
``true`` within the configuration of ``ce_services``.

.. code-block:: yaml
    :caption: Enable InfluxDB service within ``spinfile.yaml``

    ce_services:
        influxdb:
            enabled: true

(Re-) provision may be required to apply the changes.

How to pass additional options and flags to the `ce_services`_?
###############################################################

Except for the ``-i`` / ``--instance`` option, a additional flags and options
passed to the ``ce_services`` task are passed to the `ce_services`_ command-line
tool as shown below:

.. code-block:: bash
    :caption: Pass additional flags and options to ``ce_services``

    spin ce-services -i <path to instance> --<flag> <value>

How to configure and use the RabbitMQ service?
##############################################

The RabbitMQ service can be provisioned by enabling it in the ``spinfile.yaml``
as follows:

.. code-block:: yaml
   :caption: ``spinfile.yaml`` with enabled RabbitMQ service

   ce_services:
       rabbitmq:
           enabled: true

When provisioning a project with RabbitMQ enabled, the plugin will download and
install rabbitmq-server on Windows, and if executed on Linux, additionally
installing and compiling the Erlang OTP. Both can be further configured via the
``ce_services.rabbitmq`` subtree.

The service can be started, e.g. via ``spin ce-services`` or manually via
``spin run rabbitmq-server``.

``csspin_ce.ce_services`` schema reference
##########################################

.. include:: ce_services_schemaref.rst
