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

======================
Installation and setup
======================

`csspin`_ must be installed to perform the following actions.

For leveraging plugins from within the ``csspin_ce`` plugin-package for
``csspin``, the plugin-package must be added to the list of plugin-packages
within a project's ``spinfile.yaml``.

.. code-block:: yaml
    :caption: Example: ``spinfile.yaml`` setup to enable the provided plugins

    plugin_packages:
        - csspin-ce
        - csspin-frontend   # required by csspin-ce
        - csspin-java       # required by csspin-ce
        - csspin-python     # required by csspin-ce
    plugins:
        - csspin_ce:
            - ce_services
            - mkinstance
            - pkgtest
    contact_elements:
        umbrella: <The umbrella to use>
    python:
        version: '3.11.9'
        index_url: <URL to package server to retrieve CE wheels from>
    node:
        version: '18.17.1'

After the setup is done, the plugin-package can be provisioned by executing the
following command within the project's directory:

.. code-block:: console

    spin provision

The plugins defined in the plugins section of the ``spinfile.yaml`` can now be
used, using:

.. code-block:: console

    spin ce-services --help

.. note:: Using any plugin of this package requires setting ``contact_elements.umbrella`` in the spinfile.yaml.
