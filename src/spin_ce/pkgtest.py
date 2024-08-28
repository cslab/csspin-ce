# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""
Provides a wrapper around the CLI tool pkgtest.
"""

from glob import glob

from spin import config, die, sh, task

defaults = config(
    requires=config(
        spin=["spin_ce.ce_services"],  # For the tool provisioning
        python=["pkgtest"],
    ),
    additional_packages=[],
    opts=[],
    caddok_package_server_index_url=None,
    caddok_package_server="packages.contact.de",
    name=None,
    package=None,
    tests="tests/accepttests",
    test_command=None,
)


@task()
def pkgtest(cfg, args):
    """
    Run the CLI took 'pkgtest'.
    """
    opts = cfg.pkgtest.opts

    if cfg.pkgtest.additional_packages:
        opts.extend(
            ["--additional-packages", ",".join(cfg.pkgtest.additional_packages)]
        )
    if cfg.pkgtest.caddok_package_server_index_url:
        opts.extend(
            [
                "--caddok-package-server-index-url",
                cfg.pkgtest.caddok_package_server_index_url,
            ]
        )
    if cfg.pkgtest.caddok_package_server:
        opts.extend(["--caddok-package-server", cfg.pkgtest.caddok_package_server])
    if cfg.pkgtest.tests:
        opts.extend(["--tests", cfg.pkgtest.tests])
    if cfg.pkgtest.test_command:
        opts.extend(["--test-command", cfg.pkgtest.test_command])

    if not cfg.pkgtest.package:
        die(
            "'pkgtest.package' must be set in the spinfile.yaml to a path/glob to the package."
        )
    wheel = glob(cfg.pkgtest.package)
    if not wheel:
        die(f"The package {cfg.pkgtest.package} does not exist.")
    elif len(wheel) > 1:
        die(f"Found multiple packages for {cfg.pkgtest.package}.")
    else:
        wheel = wheel[0]

    sh(
        "pkgtest",
        "whl",
        cfg.pkgtest.name,
        wheel,
        "--python",
        f"{cfg.python.python}{cfg.platform.exe}",
        *cfg.pkgtest.opts,
        *args,
    )
