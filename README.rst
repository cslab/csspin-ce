|Latest Version| |Python| |License|

`csspin-ce` is maintained and published by `CONTACT Software GmbH`_ and
serves plugins for building and developing CONTACT Elements-based applications
using the `csspin`_ task runner.

The following plugins are available:

- `csspin_ce.ce_services`: Plugin for provisioning and running services required
  by CONTACT Elements applications.
- `csspin_ce.ce_support_tools`: Plugin for supporting tools used in
  CONTACT Elements applications.
- `csspin_ce.localization`: Plugin for localization of CONTACT Elements
  applications.
- `csspin_ce.mkinstance`: Plugin for creating and managing instances of
  CONTACT Elements applications.
- `csspin_ce.pkgtest`:  Plugin for testing Python wheels containing CONTACT
  Elements components.

Prerequisites
-------------

`csspin` is available on PyPI and can be installed using pip, pipx, or any other
Python package manager, e.g.:

.. code-block:: console

   python -m pip install csspin

Using csspin-ce
---------------

The `csspin-ce` package and its plugins can be installed by defining those
within the `spinfile.yaml` configuration file of your project.

.. code-block:: yaml

    spin:
      project_name: my_project

    # To develop plugins comfortably, install the packages editable as
    # follows and add the relevant plugins to the list 'plugins' below
    plugin_packages:
      - csspin-ce

    # The list of plugins to be used for this project.
    plugins:
      - csspin_ce.mkinstance

    python:
      version: 3.9.8

.. NOTE:: Assuming that `my_project` is a component based on CONTACT Elements CE16+.

If the `spinfile.yaml` is configured correctly, you can provision the project
using `spin provision`, that will automatically create a Python virtual
environment and install the required dependencies. After that, you can create a
CONTACT Elements instance using `spin mkinstance` and do other great things.

.. _`CONTACT Software GmbH`: https://contact-software.com
.. |Python| image:: https://img.shields.io/pypi/pyversions/csspin-ce.svg?style=flat
    :target: https://pypi.python.org/pypi/csspin-ce/
    :alt: Supported Python Versions
.. |Latest Version| image:: http://img.shields.io/pypi/v/csspin-ce.svg?style=flat
    :target: https://pypi.python.org/pypi/csspin-ce/
    :alt: Latest Package Version
.. |License| image:: http://img.shields.io/pypi/l/csspin-ce.svg?style=flat
    :target: https://www.apache.org/licenses/LICENSE-2.0.txt
    :alt: License
.. _`csspin`: https://pypi.org/project/csspin
