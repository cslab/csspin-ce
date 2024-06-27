# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the integration tests for spin_cpp"""

import pytest
from spin import backtick, cli


@pytest.fixture(autouse=True)
def cfg():
    """Fixture creating the configuration tree"""
    cli.load_config_tree(None)


def do_test(tmpdir, what, cmd, path="tests/integration/yamls", props=""):
    """Helper to execute spin calls via spin."""
    output = backtick(
        f"spin -p spin.cache={tmpdir} {props} -C {path} --env {tmpdir} -f"
        f" {what} --cleanup --provision {cmd}"
    )
    output = output.strip()
    return output


@pytest.mark.integration()
def test_mkinstance_provision(tmpdir):
    """Provision the mkinstnace plugin"""
    do_test(tmpdir=tmpdir, what="mkinstance.yaml", cmd="mkinstance --help")


# FIXME: Implement this properly (as soon as ce_services_lib is done)
@pytest.mark.skip("Skipped: Can't install Redis on Linux")
@pytest.mark.integration()
def test_ce_services_provision(tmpdir):
    """Provision the ce_services plugin"""
    do_test(tmpdir=tmpdir, what="ce_services.yaml", cmd="ce_services --help")
