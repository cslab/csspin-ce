# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# http://www.contact.de/
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

"""
Create a fresh instance based on spinfile.yaml configuration.

- Auto generates values for some options like a non-colliding dbname
- Provides sensible defaults for other options
"""

import getpass
import os
import platform
import socket
import zlib

from click import Choice
from csspin import (
    argument,
    config,
    die,
    info,
    mkdir,
    option,
    rmtree,
    setenv,
    sh,
    task,
    warn,
)
from csspin.tree import ConfigTree
from path import Path


def default_id(cfg):
    """Compute a default id used as value for many mkinstance options."""

    # The instance location is per default a callable
    inst_location = cfg.mkinstance.base.instance_location
    if callable(inst_location):
        inst_location = inst_location(cfg)

    vstr = f"{platform.node()}:{inst_location}".encode()
    return f"{getpass.getuser()}_bo{abs(zlib.adler32(vstr))}"


def default_location(cfg):
    """Compute a default location for the instance."""
    return Path(cfg.spin.project_root) / cfg.mkinstance.dbms


defaults = config(
    # Fixed options, should not change.
    opts=[
        "--unsafe",  # Drop existing databases
        "--batchmode",  # Non interactive
    ],
    dbms="sqlite",  # Default backend for development
    webmake=True,  # Developers mostly want to run webmake, too
    tls=config(
        cert="{mkinstance.base.instance_location}/certs/localhost.crt",
        cert_key="{mkinstance.base.instance_location}/certs/localhost.key",
        dns_names=["localhost", socket.gethostname()],
        enabled=False,
    ),
    # DBMS-agnostic options
    base=config(
        namespace="cs",  # Application namespace
        instance_admpwd="",  # Empty password for caddok
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
        mssql_dbpasswd=default_id,
        mssql_catalog=default_id,
        mssql_pyodbc="0",
        mssql_odbc_driver=None,
        mssql_odbc_encrypt="no",
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
    ),
    azure_blobstore=config(
        azure_container=None,
        azure_endpoint_url=None,
        azure_account_name=None,
    ),
    requires=config(
        python=["cs.platform"],
        npm=["sass", "yarn"],
        spin=[
            "csspin_java.java",
            "csspin_frontend.node",
            "csspin_python.python",
            "csspin_ce.contact_elements",
        ],
        system=config(
            debian=config(
                apt=[
                    "libaio1",
                ],
            ),
            windows=config(
                choco=["vcredist140"],
            ),
        ),
    ),
)


def configure(cfg):
    """Configure the mkinstance plugin and resolve the plugins subtree."""

    def compute_values(conftree):
        for k, v in conftree.items():
            if callable(v):
                conftree[k] = v(cfg)
            elif isinstance(v, ConfigTree):
                compute_values(v)

    compute_values(cfg.mkinstance)


def init(cfg):
    """Init hook of the mkinstance plugin"""
    if "CADDOK_BASE" in os.environ:
        warn(
            "CADDOK_BASE should not be set, consider using"
            + " 'mkinstance.base.instance_location'!"
        )
    if cfg.mkinstance.base.instance_location.is_dir():
        setenv(CADDOK_BASE=cfg.mkinstance.base.instance_location)


def _create_tls_cert(cfg: ConfigTree, cert_dir: Path) -> None:
    """Create a self-signed SSL/TLS certificate and private key."""
    # pylint: disable=too-many-locals
    import datetime
    import ipaddress

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])

    alt_names = [
        x509.DNSName(dns_name) for dns_name in cfg.mkinstance.tls.dns_names
    ] + [x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))]

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        )
        .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
        .sign(key, hashes.SHA256())
    )

    with open(tls_cert := cert_dir / "localhost.key", "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(tls_key := cert_dir / "localhost.crt", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    info(f"Generated '{tls_key}' and '{tls_cert}'.")


@task()
def mkinstance(
    cfg,
    rebuild: option(
        "--rebuild",  # noqa: F821
        is_flag=True,
        help="Remove an existing instance prior creating the new one.",  # noqa: F722
    ),
    dbms: argument(  # noqa: F821
        type=Choice(
            (
                "azure_blobstore",  # noqa: F821
                "mssql_sspi",  # noqa: F821
                "mysql",  # noqa: F821
                "oracle",  # noqa: F821
                "postgres",  # noqa: F821
                "s3_blobstore",  # noqa: F821
                "sqlite",  # noqa: F821
            ),
        ),
        nargs=1,
        required=False,
    ),
):
    """
    Run the 'mkinstance' command for development.

    If webmake is enabled, the JS bundles are built as well, followed by a
    cdbpkg sync.
    """
    instancedir = cfg.mkinstance.base.instance_location
    instance_default_location = default_location(cfg)
    if dbms and instancedir == instance_default_location:
        # If 'dbms' was passed and the instance location is the default (not
        # custom like './inst'), we need to update the default location based on
        # the dbms passed. Same for the TLS certificate.
        instancedir = cfg.spin.project_root / dbms

    if cfg.mkinstance.tls.enabled and (
        cfg.mkinstance.tls.cert == instance_default_location / "certs" / "localhost.crt"
    ):
        tls_cert = instancedir / "certs" / "localhost.crt"
    else:
        tls_cert = cfg.mkinstance.tls.cert

    def to_cli_options(cfgtree):
        return [f"--{k}={v}" for k, v in cfgtree.items() if v is not None]

    opts = (
        cfg.mkinstance.opts
        + to_cli_options(cfg.mkinstance.base | {"instance_location": instancedir})
        + to_cli_options(cfg.mkinstance.s3_blobstore)
        + to_cli_options(cfg.mkinstance.azure_blobstore)
    )

    if rebuild and instancedir.is_dir():
        rmtree(instancedir)
        setenv(CADDOK_BASE=None)

    if not instancedir.is_dir() and os.getenv("CADDOK_BASE", None) is not None:
        setenv(CADDOK_BASE=None)

    setenv(
        CADDOK_GENERATE_STD_CALENDAR_PROFILE_RANGE=cfg.mkinstance.std_calendar_profile_range
    )

    dbms = dbms or cfg.mkinstance.dbms
    if not instancedir.is_dir():
        if cfg.mkinstance.tls.enabled:
            if tls_cert.parent == instancedir / "certs":
                mkdir(tls_cert.parent)
                _create_tls_cert(cfg, tls_cert.parent)
            opts.append(f"--sslca={tls_cert}")

        dbms_opts = to_cli_options(cfg.mkinstance.get(dbms, {}))
        sh("mkinstance", *opts, dbms, *dbms_opts, shell=False)

        if cfg.mkinstance.webmake:
            sh("webmake", "--instancedir", instancedir, "devupdate")
            sh("webmake", "--instancedir", instancedir, "buildall", "--parallel")

        # Run cdbpkg sync on the new install
        sh("cdbpkg", "--instancedir", instancedir, "sync")
    else:
        die(
            "There already exists an instance, if you want to rebuild, try the '--rebuild' option"
        )
