# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Fixtures for the integration testsuite"""

import hashlib
import os

import pytest


@pytest.fixture
def short_tmp_path(tmp_path_factory, request):
    """
    Create a temporary path with a short prefix to avoid long paths on
    Windows.
    """
    test_hash = hashlib.sha256(request.node.name.encode()).hexdigest()[:8]
    base = tmp_path_factory.getbasetemp() / test_hash
    base.mkdir(parents=True, exist_ok=True)
    return base


@pytest.fixture(scope="session", autouse=True)
def disable_global_yaml():
    "Fixture to let spin ignore the global yaml."
    if not os.environ.get("CI"):
        os.environ["SPIN_DISABLE_GLOBAL_YAML"] = "True"
