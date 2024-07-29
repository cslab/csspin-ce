# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the integration tests for spin_cpp"""

import subprocess

import pytest


def execute_spin(tmpdir, what, cmd, path="tests/integration/yamls"):
    """Helper to execute spin calls via spin."""
    full_cmd = [
        "spin",
        "-p",
        f"spin.cache={tmpdir}",
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
    """Provision the mkinstnace plugin"""
    execute_spin(tmpdir=tmpdir, what="mkinstance.yaml", cmd=["mkinstance", "--help"])


@pytest.mark.integration()
@pytest.mark.xfail(reason="Latest plugin-package states may fail")
def test_mkinstance_latest_provision(tmpdir):
    """Provision the mkinstnace plugin"""
    execute_spin(
        tmpdir=tmpdir, what="mkinstance-latest.yaml", cmd=["mkinstance", "--help"]
    )


# FIXME: Implement this properly (as soon as ce_services_lib is done)
@pytest.mark.skip("Skipped: Can't install Redis on Linux")
@pytest.mark.integration()
def test_ce_services_provision(tmpdir):
    """Provision the ce_services plugin"""
    execute_spin(tmpdir=tmpdir, what="ce_services.yaml", cmd=["ce_services", "--help"])


# FIXME: Implement this properly (as soon as ce_services_lib is done)
@pytest.mark.skip("Skipped: Can't install Redis on Linux")
@pytest.mark.integration()
@pytest.mark.xfail(reason="Latest plugin-package states may fail")
def test_ce_services_latest_provision(tmpdir):
    """Provision the ce_services plugin"""
    execute_spin(
        tmpdir=tmpdir, what="ce_services-latest.yaml", cmd=["ce_services", "--help"]
    )
