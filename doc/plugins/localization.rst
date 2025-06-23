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

``DEEPL_AUTH_KEY`` environment variable is required so that plugin can translate new
strings with `DeepL <https://developers.deepl.com/docs>`_.

Configuration in ``spinfile.yaml`` is optional for this plugin.
In most cases you can rely on defaults. However, it's worth mentioning,
that you can configure the languages you want the component
to be localized into with ``target_languages`` parameter.

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to automate localization with csspin_ce.localize?
#####################################################

Except for the ``-D`` / ``--instancedir`` option, all additional flags and
options are ignored.

Execute ``spin localize`` command and lean back in your chair.

``csspin_ce.localization`` schema reference
###########################################

.. include:: localization_schemaref.rst
