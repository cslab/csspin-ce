# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# https://www.contact-software.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Spin wrapper plugin for the localization tool.
"""

import os

from csspin import (
    Path,
    config,
    die,
    option,
    setenv,
    sh,
    task,
)

defaults = config(
    xliff_dir="xliff_export",
    target_langs=["ja", "zh"],
    requires=config(
        python=["localization"],
        spin=["csspin_ce.contact_elements", "csspin_ce.mkinstance"],
    ),
)


@task(when="localize")
def localize_ce(
    cfg,
    instance: option(
        "-i",  # noqa: F821
        "--instance",  # noqa: F821
        help="Directory of the CONTACT Elements instance.",  # noqa: F722
    ),
    check_only: option(
        "--check-only",  # noqa: F821
        is_flag=True,
        help="Check if the project is fully localized.",  # noqa: F722
    ),
):
    """Exports xliffs with cdbpkg and runs 'l10n sync' against them."""

    if instance:
        setenv(CADDOK_BASE=instance)
    if not os.getenv("CADDOK_BASE") or not Path(os.getenv("CADDOK_BASE")).is_dir():
        die("Can't find the CE instance.")

    sh(
        "cdbpkg",
        "xliff",
        "--export",
        cfg.spin.project_name,
        "--exportdir",
        cfg.localization.xliff_dir,
        "--sourcelang",
        "en",
        "--targetlang",
        "ja",  # We can export any lang, since we don't need source XLIFFs to contain translations
        check=False,
    )

    sh(
        "localization",
        ("check" if check_only else "sync"),
        "--source",
        cfg.localization.xliff_dir,
        *cfg.localization.target_langs,
    )
