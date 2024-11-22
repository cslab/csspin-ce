.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

======================
Installation and setup
======================

cs.spin must be installed beforehand, this can be done as documented at
http://qs.pages.contact.de/spin/cs.spin/installation.html.

For leveraging plugins from within the ``spin_ce`` plugin-package for
``cs.spin``, the plugin-package must be added to the list of plugin-packages
within a project's ``spinfile.yaml``.

.. code-block:: yaml
    :caption: Example: ``spinfile.yaml`` setup to enable the provided plugins

    plugin_packages:
        - spin_ce
        - spin_frontend # required by spin_ce
        - spin_java     # required by spin_ce
        - spin_python   # required by spin_ce
    plugins:
        - spin_ce:
            - ce_services
            - mkinstance
            - pkgtest
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

    spin docs --help
