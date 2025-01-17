# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the integration tests for spin_ce"""

import shlex
import shutil
import subprocess
import sys

import pytest


def execute_spin(yaml, env, path="tests/integration/yamls", cmd=""):
    """Helper function to execute spin and return the output"""
    cmd = f"spin -p spin.cache={env} -C {path} --env {str(env)} -f {yaml} " + cmd
    try:
        return subprocess.check_output(
            shlex.split(cmd, posix=sys.platform != "win32"),
            encoding="utf-8",
            stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as ex:
        print(ex.stdout)
        print(ex.stderr)
        raise


@pytest.mark.integration()
def test_mkinstance_provision(tmp_path):
    """Provision the mkinstance plugin"""
    yaml = "mkinstance.yaml"
    execute_spin(yaml=yaml, env=tmp_path, cmd="cleanup")
    execute_spin(yaml=yaml, env=tmp_path, cmd="provision")
    execute_spin(yaml=yaml, env=tmp_path, cmd="mkinstance --help")


@pytest.mark.skipif(
    sys.platform != "win32" and shutil.which("redis-server") is None,
    reason="ce_services needs redis-server, which must be preinstalled on Linux",
)
@pytest.mark.integration()
def test_ce_services_provision(tmp_path):
    """Provision the ce_services plugin"""
    yaml = "ce_services.yaml"
    execute_spin(yaml=yaml, env=tmp_path, cmd="cleanup")
    execute_spin(yaml=yaml, env=tmp_path, cmd="provision")
    execute_spin(yaml=yaml, env=tmp_path, cmd="ce-services --help")


@pytest.mark.integration()
def test_pkgtest_provision(tmp_path):
    """Provision the pgktest plugin"""
    yaml = "pkgtest.yaml"
    execute_spin(yaml=yaml, env=tmp_path, cmd="cleanup")
    execute_spin(yaml=yaml, env=tmp_path, cmd="provision")
    execute_spin(yaml=yaml, env=tmp_path, cmd="pkgtest --help")
