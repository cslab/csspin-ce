# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# All rights reserved.
# http://www.contact.de/

"""
Create a fresh instance based on spinfile.yaml configuration.

- Auto generates values for some options like a non-colliding dbname
- Provides sensible defaults for other options
"""

import getpass
import os
import platform
import zlib

from spin import config, interpolate1, option, rmtree, setenv, sh, task
from spin.tree import ConfigTree


def system_requirements(
    cfg,
):  # pylint: disable=unused-argument,missing-function-docstring
    # This is our little database of system requirements for
    # provisioning Python; spin identifies platforms by a tuple
    # composed of the distro id and version e.g. ("debian", 10).
    debian_requirements = ["libaio1"]
    windows_requirements = ["vcredist140"]
    return [
        (
            lambda distro, version: distro in ("debian", "mint", "ubuntu"),
            {
                "apt": " ".join(debian_requirements),
            },
        ),
        (
            lambda distro, version: distro in ("windows"),
            {
                "choco": " ".join(windows_requirements),
            },
        ),
    ]


def default_id(cfg):
    """Compute a default id used as value for many mkinstance options"""

    # The instance location is per default a callable
    inst_location = cfg.mkinstance.base.instance_location
    if callable(inst_location):
        inst_location = inst_location(cfg)

    vstr = f"{platform.node()}:{inst_location}".encode()
    return f"{getpass.getuser()}_bo{abs(zlib.adler32(vstr))}"


def default_location(cfg):
    """Compute a default location for the instance"""
    return os.path.join(cfg.spin.project_root, cfg.mkinstance.dbms)


defaults = config(
    # Fixed options, should not change.
    opts=[
        "--unsafe",  # Drop existing databases
        "--batchmode",  # Non interactive
    ],
    dbms="sqlite",  # Default backend for development
    webmake=True,  # Developers mostly want to run webmake, too
    # DBMS-agnostic options
    base=config(
        namespace="cs",  # Application namespace
        instance_admpwd="",  # Empty password for caddok
        sslmode="0",  # TLS setup
        instance_location=default_location,
    ),
    std_calendar_profile_range="-",
    # DBMS-specific defaults
    oracle=config(
        ora_dbhost="//localhost:1521/xe",
        ora_syspwd="system",
        ora_dbuser=default_id,
        ora_dbpasswd=default_id,
    ),
    mssql=config(
        mssql_dbuser=default_id,
        mssql_dbhost="localhost\\SQLEXPRESS",
        mssql_syspwd="sa",
        mssql_dbpasswd=default_id,
        mssql_catalog=default_id,
    ),
    mssql_sspi=config(
        mssql_dbhost="localhost\\SQLEXPRESS",
        mssql_catalog=default_id,
    ),
    postgres=config(
        postgres_database="postgres",
        postgres_dbhost="localhost",
        postgres_dbpasswd=default_id,
        postgres_dbport=5432,
        postgres_dbuser=default_id,
        postgres_system_user="postgres",
        postgres_syspwd="system",
    ),
    s3_blobstore=config(
        s3_bucket=None,
        s3_region=None,
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
    ),
    azure_blobstore=config(
        azure_container=None,
        azure_endpoint_url=None,
        azure_account_name=None,
        azure_account_key=None,
    ),
    requires=config(
        python=["nodeenv", "cs.platform"],
        npm=["sass", "yarn"],
        spin=[
            "spin_frontend.node",
            "spin_python.python",
        ],
    ),
)


def configure(cfg):
    """Recursively resolve all values in the configtree"""

    def compute_values(conftree):
        for k, v in conftree.items():
            if callable(v):
                conftree[k] = v(cfg)
            elif isinstance(v, ConfigTree):
                compute_values(v)

    compute_values(cfg.mkinstance)


@task()
def mkinstance(cfg, rebuild: option("--rebuild", is_flag=True)):  # noqa: F821
    """Run the 'mkinstance' command for development."""

    def to_cli_options(cfgtree):
        return [f"--{k}={v}" for k, v in cfgtree.items() if v is not None]

    opts = (
        cfg.mkinstance.opts
        + to_cli_options(cfg.mkinstance.base)
        + to_cli_options(cfg.mkinstance.s3_blobstore)
        + to_cli_options(cfg.mkinstance.azure_blobstore)
    )
    dbms = cfg.mkinstance.dbms
    dbms_opts = to_cli_options(cfg.mkinstance.get(dbms, {}))

    instancedir = interpolate1(cfg.mkinstance.base.instance_location)
    if rebuild and os.path.isdir(instancedir):
        rmtree(instancedir)
    setenv(
        CADDOK_GENERATE_STD_CALENDAR_PROFILE_RANGE=cfg.mkinstance.std_calendar_profile_range
    )
    if not os.path.isdir(instancedir):
        sh("mkinstance", *opts, dbms, *dbms_opts, shell=False)

    if cfg.mkinstance.webmake:
        sh("webmake", "--instancedir", instancedir, "devupdate")
        sh("webmake", "--instancedir", instancedir, "buildall", "--parallel")

    # Run cdbpkg sync on the new install
    sh("cdbpkg", "--instancedir", instancedir, "sync")
