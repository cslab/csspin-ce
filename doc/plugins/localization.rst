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


.. _csspin_ce.localization:

======================
csspin_ce.localization
======================

.. FIXME: Nobody knows what this tool is and how to install it.

The ``csspin_ce.localization`` plugin provides a wrapper for the localization
(l10n) tool.

How to setup the ``csspin_ce.localization`` plugin?
###################################################

For using the ``csspin_ce.localization`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` for ``csspin_ce.localization``

    plugin_packages:
        - csspin_ce
    plugins:
        - csspin_ce.localization
    contact_elements:
        umbrella: <The umbrella to use>
    python:
        version: '3.11.9'
        index_url: <package server index url to retrieve CE wheels from>
    java:
        version: '17'
    node:
        version: '18.17.1'

The environment variable ``DEEPL_AUTH_KEY`` is required so that plugin can translate new
strings with `DeepL <https://developers.deepl.com/docs>`_.

Further configuration in ``spinfile.yaml`` is optional for this plugin.
In most cases you can rely on defaults. However, it's worth mentioning,
that you can configure the languages you want the component
to be localized into with ``target_languages`` parameter.

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to automate localization with csspin_ce.localization?
#########################################################

``spin localize-ce`` command can be used for this purpose.

Internally, the command exports strings from the database of your CONTACT Elements instance
into XLIFF files. These files are saved at the path specified by ``localization.xliff_dir``,
which defaults to ``<project_root>/xliff_export``. It then synchronizes strings
that have been modified (added, deleted, or changed) within the instance database
and translates those lacking translations.


``csspin_ce.localization`` schema reference
###########################################

.. include:: localization_schemaref.rst
