.. -*- coding: utf-8 -*-
   Copyright (C) 2025 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_ce.localization:

====================
spin_ce.localization
====================

The ``spin_ce.localization`` plugin provides a wrapper for the localization (l10n) tool.

How to setup the ``spin_ce.localization`` plugin?
#################################################

``DEEPL_AUTH_KEY`` environment variable is required so that plugin can translate new
strings with `DeepL <https://developers.deepl.com/docs>`_.

Configuration in ``spinfile.yaml`` is optional for this plugin.
In most cases you can rely on defaults. However, it's worth mentioning,
that you can configure the languages you want the component
to be localized into with ``target_languages`` parameter.

The provisioning of the required tools and the plugins dependencies can be done
via the well-known ``spin provision``-command.

How to automate localization with spin_ce.localize?
###################################################

Except for the ``-D`` / ``--instancedir`` option, all additional flags and
options are ignored.

Execute ``spin localize`` command and lean back in your chair.

``spin_ce.localization`` schema reference
#########################################

.. include:: localization_schemaref.rst
