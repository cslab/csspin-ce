# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Fixtures for the integration testsuite"""

import hashlib
import os
import shlex
import subprocess
import sys

import pytest


@pytest.fixture
def short_tmp_path(tmp_path_factory, request):
    """
    Create a temporary path with a short prefix to avoid long paths on
    Windows. The directory is removed after the test finishes.
    """
    test_hash = hashlib.sha256(request.node.name.encode()).hexdigest()[:8]
    base = tmp_path_factory.getbasetemp() / test_hash
    base.mkdir(parents=True, exist_ok=True)
    return base


@pytest.fixture
def execute_spin():
    """Fixture to execute spin commands in integration tests."""

    def _execute_spin(yaml, env, path="tests/integration/yamls", cmd=""):
        """Helper function to execute spin and return the output"""
        cmd = f"spin -p spin.data={env} -C {path} --env {str(env)} -f {yaml} " + cmd
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

    return _execute_spin


@pytest.fixture(scope="session", autouse=True)
def disable_global_yaml():
    "Fixture to let spin ignore the global yaml."
    if not os.environ.get("CI"):
        os.environ["SPIN_DISABLE_GLOBAL_YAML"] = "True"
