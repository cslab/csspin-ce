.. -*- coding: utf-8 -*-
   Copyright (C) 2025 CONTACT Software GmbH
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

.. _csspin_ce.ce_support_tools:

==========================
csspin_ce.ce_support_tools
==========================

The ``csspin_ce.ce_support_tools`` plugin provides a wrapper for the
ce_support_tools package.

How to setup the ``csspin_ce.ce_support_tools`` plugin?
#######################################################

For using the ``csspin_ce.ce_support_tools`` plugin, a project's
``spinfile.yaml`` must at least contain the following configuration.

.. code-block:: yaml
    :caption: Configuring ``csspin_ce.ce_support_tools`` in ``spinfile.yaml``

    plugin_packages:
        - csspin-ce
    plugins:
        - csspin_ce:
            - mkinstance  # Required for instance location
            - ce_support_tools
    contact_elements:
        umbrella: <The umbrella to use>
    # ... other configurations depending on csspin_ce.mkinstance's requirements.

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
    :caption: Run performance tests for the current project

    spin pyperf run
