# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""
Spin wrapper plugin for the localization tool.
"""

import os

try:
    from csspin import (
        Path,
        config,
        die,
        option,
        setenv,
        sh,
        task,
    )
except ImportError:
    from spin import (
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
    target_langs=["ja"],
    requires=config(
        python=["localization"],
        spin=["spin_ce.mkinstance"],
    ),
)


@task()
def localize(
    cfg,
    instance: option(
        "-i",  # noqa: F821
        "--instance",  # noqa: F821
        help="Directory of the CONTACT Elements instance.",  # noqa: F722
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
        "ja",
        check=False,
    )

    sh(
        "localization",
        "sync",
        "--source",
        cfg.localization.xliff_dir,
        *cfg.localization.target_langs,
    )
