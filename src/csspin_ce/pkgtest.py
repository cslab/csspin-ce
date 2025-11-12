# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
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

"""Provides a wrapper around the CLI tool pkgtest."""

from glob import glob

from csspin import config, die, option, setenv, sh, task

defaults = config(
    name="{spin.project_name}",
    package=None,
    tests="tests/accepttests",
    test_command=None,
    additional_packages=[],
    opts=[],
    caddok_package_server_index_url=None,
    caddok_package_server="",
    dbms="sqlite",  # Default backend for development
    requires=config(
        spin=[
            "csspin_ce.contact_elements",
            "csspin_ce.ce_services",  # For the tool provisioning
        ],
        python=["pkgtest"],
    ),
)


@task()
def pkgtest(
    cfg,
    args,
    dbms: option(
        "--dbms", is_flag=False, help="Override default dbms"  # noqa: F821, F722
    ),
):
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

    if cfg.python.constraints:
        setenv(PIP_CONSTRAINT=" ".join(cfg.python.constraints))

    setenv(
        CADDOK_BASE=None
    )  # Unset CADDOK_BASE here so mkinstance call in pkgtest script doesn't fail

    sh(
        "pkgtest",
        "whl",
        cfg.pkgtest.name,
        wheel,
        "--python",
        cfg.python.python,
        "--dbms",
        dbms or cfg.pkgtest.dbms,
        *cfg.pkgtest.opts,
        *args,
    )
