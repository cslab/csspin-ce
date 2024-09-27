# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the integration tests for spin_cpp"""

import shutil
import subprocess
import sys

import pytest


def execute_spin(tmpdir, what, cmd, path="tests/integration/yamls"):
    """Helper to execute spin calls via spin."""
    full_cmd = [
        "spin",
        "-p",
        f"spin.data={tmpdir}",
        "-C",
        path,
        "--env",
        tmpdir,
        "-f",
        f"tests/integration/yamls/{what}",
        "--cleanup",
        "--provision",
    ]
    full_cmd.extend(cmd)
    print(subprocess.list2cmdline(full_cmd))
    try:
        output = subprocess.check_output(full_cmd, encoding="utf-8")
    except subprocess.CalledProcessError as ex:
        print(ex.stdout.strip())
        raise
    return output.strip()


@pytest.mark.integration()
def test_mkinstance_provision(tmpdir):
    """Provision the mkinstance plugin"""
    execute_spin(tmpdir=tmpdir, what="mkinstance.yaml", cmd=["mkinstance", "--help"])


@pytest.mark.skipif(
    sys.platform != "win32" and shutil.which("redis-server") is None,
    reason="ce_services needs redis-server, which must be preinstalled on Linux",
)
@pytest.mark.integration()
def test_ce_services_provision(tmpdir):
    """Provision the ce_services plugin"""
    execute_spin(tmpdir=tmpdir, what="ce_services.yaml", cmd=["ce_services", "--help"])


@pytest.mark.integration()
def test_pkgtest_provision(tmpdir):
    """Provision the pgktest plugin"""
    execute_spin(tmpdir=tmpdir, what="pkgtest.yaml", cmd=["pkgtest", "--help"])
