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
#
# pylint: disable=too-many-lines

"""
Provides a wrapper around the CLI tool of ce_services and
provisions all tool necessary for these ce_services.
"""

import os
import shutil
import sys
import tarfile
import zipfile
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError

from csspin import (
    Verbosity,
    cd,
    config,
    debug,
    die,
    download,
    echo,
    exists,
    mkdir,
    mv,
    option,
    rmtree,
    setenv,
    sh,
    task,
    warn,
)
from path import Path

defaults = config(
    hivemq=config(
        enabled=False,
        install_dir="{spin.data}/hivemq",
        version="2024.4",
        elements_integration=config(
            user="csiot_integrator",
            password="",  # nosec: hardcoded_password_funcarg
            install_dir="",
        ),
    ),
    influxdb=config(
        enabled=False,
        version="1.8.10",
        install_dir="{spin.data}/influxdb",
    ),
    traefik=config(
        version="2.11.2",
        dashboard_port="",
        install_dir="{spin.data}/traefik",
        tls=config(
            enabled=False,
        ),
    ),
    solr=config(
        version="9.8.1",
        install_dir="{spin.data}/solr",
        version_postfix="-slim",
        mirrors=["https://downloads.apache.org/", "https://archive.apache.org/dist/"],
    ),
    rabbitmq=config(
        enabled=False,
        version="4.1.0",
        install_dir="{spin.data}/rabbitmq",
        erlang=config(
            version="28.0",
            install_dir="{spin.data}/erlang",
        ),
    ),
    redis=config(
        version="7.2.4",
        install_dir="{spin.data}/redis",
    ),
    tika=config(
        version="3.2.3",
        install_dir="{spin.data}/tika",
        mirrors=["https://downloads.apache.org/", "https://archive.apache.org/dist/"],
    ),
    loglevel="",
    requires=config(
        spin=["csspin_ce.contact_elements", "csspin_ce.mkinstance", "csspin_java.java"],
        python=[
            "ce_services>=1.5.0",
            "psutil",
            "requests",
        ],
        system=config(
            debian=config(
                apt=[
                    "redis-server",
                    "build-essential",  # For building Erlang via make
                ],
            ),
        ),
    ),
)


def extract_service_config(cfg):
    """
    Helper to match the config of the plugin into the config of the ce_services
    command-line tool.

    Returns a dict to feed directly into
    ce_services.RequireAllServices/ce_services.Require.

    :param cfg: The spin config tree
    :type cfg: ConfigTree
    :return: A dict with the ce_services config from the config_tree
    :rtype: dict
    """
    additional_cfg = {}
    if cfg.mkinstance.base.instance_admpwd:
        additional_cfg["instance_admpwd"] = cfg.mkinstance.base.instance_admpwd
    if cfg.ce_services.loglevel:
        additional_cfg["loglevel"] = cfg.ce_services.loglevel
    if cfg.ce_services.traefik.tls.enabled:
        additional_cfg |= {
            "traefik_tls": True,
            "traefik_tls_cert": cfg.mkinstance.tls.cert,
            "traefik_tls_cert_key": cfg.mkinstance.tls.cert_key,
        }
    if cfg.ce_services.influxdb.enabled:
        additional_cfg["influxd"] = True
    if cfg.ce_services.hivemq.enabled:
        additional_cfg["hivemq"] = True
        hivemq_options = {
            "hivemq_elements_integration_password": cfg.ce_services.hivemq.elements_integration.password,
            "hivemq_elements_integration_user": cfg.ce_services.hivemq.elements_integration.user,
        }
        for key, value in hivemq_options.items():
            if value:
                additional_cfg[key] = value
    if cfg.ce_services.rabbitmq.enabled:
        additional_cfg["rabbitmq"] = True

    return additional_cfg


@task(aliases=["ce_services"])
def ce_services(
    cfg,
    instance: option(
        "-i",  # noqa: F821
        "--instance",  # noqa: F821
        help="Directory of the CONTACT Elements instance.",  # noqa: F722
    ),
    args,
):
    """Start the CE services synchronously."""

    if not Path(os.getenv("CADDOK_BASE", "")).is_dir() and not (
        instance and Path(instance).is_dir()
    ):
        die("Can't find the CE instance.")
    if instance:
        setenv(CADDOK_BASE=instance)

    # Now set the relevant CLI options from cfg, making sure to only add those
    # from cfg that haven't already been set by the CLI.
    all_cli_args = list(args)
    for key, value in extract_service_config(cfg).items():
        cli_option_name = f"--{key}"
        if cli_option_name not in args:
            if cli_option_name in (
                "--influxd",
                "--hivemq",
                "--rabbitmq",
                "--traefik_tls",
            ):
                all_cli_args.append(cli_option_name)
            else:
                all_cli_args.append(f"{cli_option_name}={value}")

    if cfg.verbosity == Verbosity.QUIET:
        verbosity_arg = "-q"
    elif cfg.verbosity == Verbosity.INFO:
        verbosity_arg = "-v"
    elif cfg.verbosity == Verbosity.DEBUG:
        verbosity_arg = "-vv"
    else:
        verbosity_arg = None

    sh("ce_services", verbosity_arg, *all_cli_args)


def provision(cfg):  # pylint: disable=too-many-statements
    """
    Provision tools necessary to startup all ce_services.

    FIXME: This function is too long and should be split into smaller functions.
    """

    def extract(archive, extract_to, member=""):
        """Unpacks archives"""
        echo(f"Extracting {archive} to {extract_to}")
        member = member.replace("\\", "/")

        mode = None
        if tarfile.is_tarfile(archive):
            extractor = tarfile.open
            if archive.endswith(".tar.gz") or archive.endswith(".tgz"):
                mode = "r:gz"
            elif archive.endswith(".tar.xz"):
                mode = "r:xz"
        elif zipfile.is_zipfile(archive):
            extractor = zipfile.ZipFile
            mode = "r"
        if not mode:
            die(f"Unsupported archive type {archive}")

        with extractor(  # pylint: disable=possibly-used-before-assignment
            archive, mode=mode  # pylint: disable=possibly-used-before-assignment
        ) as arc:
            if isinstance(arc, tarfile.TarFile):
                members = (
                    entity
                    for entity in arc.getmembers()  # pylint: disable=maybe-no-member
                    if entity.name.startswith(member)
                )
            elif isinstance(arc, zipfile.ZipFile):
                members = (
                    entity
                    for entity in arc.namelist()  # pylint: disable=maybe-no-member
                    if entity.startswith(member)
                )
            else:
                members = ()

            arc.extractall(
                members=members,
                path=extract_to,
            )  # nosec: tarfile_unsafe_members

    def install_traefik(cfg):
        version = cfg.ce_services.traefik.version
        traefik_install_dir = cfg.ce_services.traefik.install_dir / version

        traefik = traefik_install_dir / f"traefik{cfg.platform.exe}"

        if not traefik.exists():
            debug("Installing Traefik")
            mkdir(traefik_install_dir)

            archive = (
                f"traefik_v{version}_windows_amd64.zip"
                if sys.platform == "win32"
                else f"traefik_v{version}_linux_amd64.tar.gz"
            )

            with TemporaryDirectory() as tmp_dir:
                archive_path = Path(tmp_dir) / archive
                download(
                    f"https://github.com/traefik/traefik/releases/download/v{version}/{archive}",
                    archive_path,
                )
                extract(archive_path, traefik_install_dir, f"traefik{cfg.platform.exe}")
        else:
            debug(f"Using cached traefik ({traefik})")

    def install_solr(cfg):
        version = cfg.ce_services.solr.version
        install_dir = cfg.ce_services.solr.install_dir
        postfix = cfg.ce_services.solr.version_postfix

        solr_name = Path(f"solr-{version}{postfix}")
        solr_path = install_dir / solr_name

        if not solr_path.exists():
            debug("Installing Apache Solr")
            mkdir(install_dir)
            archive = f"{solr_name}.tgz"

            with TemporaryDirectory() as tmp_dir:
                archive_path = Path(tmp_dir) / archive
                url_path = f"solr/solr/{version}/{archive}"
                for mirror in cfg.ce_services.solr.mirrors:
                    if mirror[-1] == "/":
                        url = f"{mirror}{url_path}"
                    else:
                        url = f"{mirror}/{url_path}"
                    try:
                        download(url, archive_path)
                        break
                    except HTTPError:
                        warn(f"Solr {version} not found at {url}")
                        continue
                    except URLError:
                        warn(f"{mirror} currently not reachable")
                        continue
                else:
                    die(  # pylint: disable=broad-exception-raised
                        "Could not download Apache Solr from any of the mirrors."
                    )

                extract(archive_path, install_dir, solr_name)
        else:
            debug(f"Using cached Apache Solr ({solr_path})")

    def install_redis(cfg):
        if sys.platform == "win32":
            redis_install_dir = (
                cfg.ce_services.redis.install_dir / cfg.ce_services.redis.version
            )
            redis = redis_install_dir / "redis-server.exe"
            if not redis.exists():
                mkdir(cfg.ce_services.redis.install_dir)
                debug("Installing redis-server")
                with TemporaryDirectory() as tmp_dir:
                    redis_installer_archive = (
                        Path(tmp_dir)
                        / f"redis-windows-{cfg.ce_services.redis.version}.zip"
                    )
                    download(
                        f"https://github.com/zkteco-home/redis-windows/archive/refs/tags/{cfg.ce_services.redis.version}.zip",  # noqa: E501
                        redis_installer_archive,
                    )
                    extract(redis_installer_archive, cfg.ce_services.redis.install_dir)
                    (
                        cfg.ce_services.redis.install_dir
                        / f"redis-windows-{cfg.ce_services.redis.version}"
                    ).rename(
                        redis_install_dir
                    )  # FIXME: Why not using spin.mv?
            else:
                debug(f"Using cached redis-server ({redis})")

        elif not shutil.which("redis-server"):
            die(
                "Cannot provision redis-server on linux. Please run 'spin system-provision'."  # noqa: E501
            )

    def install_hivemq(cfg):
        def _download(
            url,
            zipfile_name,
            target_directory,
            ignore,
            unpacked_source_directory,
        ):
            """
            Downloads the zip from provided URL and moves the desired content
            into the target directory.
            """
            if exists(target_directory):
                rmtree(target_directory)
            mkdir(target_directory)

            with TemporaryDirectory() as tmp_dir:
                download(
                    url=url,
                    location=(download_file := Path(tmp_dir) / zipfile_name),
                )
                extract(download_file, tmp_dir)

                for f in os.listdir(
                    (
                        unpacked_source_directory := Path(tmp_dir)
                        / unpacked_source_directory
                    )
                ):
                    if f not in ignore:
                        # FIXME: Why not using spin.mv?
                        debug(
                            "Moving"
                            f" {(source := str(unpacked_source_directory / f))}"
                            f" -> {(target := str(target_directory))}"
                        )
                        shutil.move(source, target)

        hivemq_version = cfg.ce_services.hivemq.version
        hivemq_base_dir = cfg.ce_services.hivemq.install_dir / hivemq_version
        if exists(hivemq_base_dir):
            debug(f"Using cached HiveMQ ({hivemq_base_dir})")
        else:
            debug(f"Installing HiveMQ {hivemq_version}")
            hivemq_zipfile = f"hivemq-ce-{hivemq_version}.zip"
            _download(
                url="https://github.com/hivemq/hivemq-community-edition/releases"
                f"/download/{hivemq_version}/{hivemq_zipfile}",
                zipfile_name=hivemq_zipfile,
                unpacked_source_directory=f"hivemq-ce-{hivemq_version}",
                target_directory=hivemq_base_dir,
                ignore={"data", "log", hivemq_zipfile},
            )
            if sys.platform != "win32":
                from stat import S_IEXEC

                for f in ("run.sh", "diagnostics.sh"):
                    os.chmod(
                        (f := hivemq_base_dir / "bin" / f),
                        os.stat(f).st_mode | S_IEXEC,
                    )
                for f in os.listdir((path := hivemq_base_dir / "bin" / "init-script")):
                    os.chmod((f := path / f), os.stat(f).st_mode | S_IEXEC)

            rmtree(hivemq_base_dir / "extensions" / "hivemq-allow-all-extension")

    def install_influxdb(cfg):
        version = cfg.ce_services.influxdb.version
        if not (
            influxdb_dir := cfg.ce_services.influxdb.install_dir / version
        ).exists():
            mkdir(influxdb_dir)
            debug(f"Installing InfluxDB {version}")
            archive = (
                f"influxdb-{version}_windows_amd64.zip"
                if sys.platform == "win32"
                else f"influxdb-{version}_linux_amd64.tar.gz"
            )

            with TemporaryDirectory() as tmp_dir:
                download(
                    f"https://dl.influxdata.com/influxdb/releases/{archive}",
                    (archive_path := Path(tmp_dir) / archive),
                )
                extract(archive_path, tmp_dir)

                if (
                    sources := Path(tmp_dir) / f"influxdb-{version}-1"
                ) and sys.platform == "win32":
                    for f in os.listdir(sources):
                        debug(
                            "Moving" f" {(source := sources / f)}" f" -> {influxdb_dir}"
                        )
                        shutil.move(source, influxdb_dir)
                else:
                    from stat import S_IEXEC

                    for f in os.listdir((sources := sources / "usr" / "bin")):
                        # FIXME: Why not using spin.mv?
                        debug("Moving" f" {(source := sources / f)} -> {influxdb_dir}")
                        shutil.move(source, influxdb_dir)
                        os.chmod((f := influxdb_dir / f), os.stat(f).st_mode | S_IEXEC)
        else:
            debug(f"Using cached InfluxDB ({influxdb_dir})")

    def install_rabbitmq(cfg):
        """Install RabbitMQ server from GitHub."""
        version = str(cfg.ce_services.rabbitmq.version)
        rabbitmq_install_dir = Path(cfg.ce_services.rabbitmq.install_dir)

        if not (rabbitmq_install_dir / version).exists():
            debug("Installing RabbitMQ")
            mkdir(rabbitmq_install_dir)

            rabbitmq_name = f"rabbitmq_server-{version}"
            base_url = "https://github.com/rabbitmq/rabbitmq-server/releases/download"
            if sys.platform == "win32":
                archive = f"rabbitmq-server-windows-{version}.zip"
            else:
                archive = f"rabbitmq-server-generic-unix-{version}.tar.xz"

            with TemporaryDirectory() as tmp_dir:
                download(
                    f"{base_url}/v{version}/{archive}",
                    (archive_path := Path(tmp_dir) / archive),
                )
                extract(archive_path, rabbitmq_install_dir, rabbitmq_name)
            mv(rabbitmq_install_dir / rabbitmq_name, rabbitmq_install_dir / version)

        else:
            debug(f"Using cached rabbitmq-server ({rabbitmq_install_dir / version})")

    def install_erlang(cfg):
        """Installation of the Erlang programming language"""
        version = str(cfg.ce_services.rabbitmq.erlang.version)
        erlang_install_dir = Path(cfg.ce_services.rabbitmq.erlang.install_dir)

        if not (erlang_install_dir / version).exists():
            debug(f"Installing Erlang {version}")
            mkdir(erlang_install_dir)
            base_url = f"https://github.com/erlang/otp/releases/download/OTP-{version}"
            if sys.platform == "win32":
                erlang_name = f"otp_win64_{version}"
                file_extension = ".zip"
            else:
                erlang_name = f"otp_src_{version}"
                file_extension = ".tar.gz"

            with TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                archive = erlang_name + file_extension
                archive_path = tmp_path / archive
                download(f"{base_url}/{archive}", archive_path)

                if sys.platform == "win32":
                    extract(archive_path, erlang_install_dir / version)
                else:
                    extract(archive_path, tmp_dir, erlang_name)
                    debug(f"Compiling Erlang {version}")
                    with cd(tmp_path / erlang_name):

                        from subprocess import DEVNULL  # noqa: F401 # nosec

                        stdout = DEVNULL if cfg.verbosity <= Verbosity.NORMAL else None
                        sh(
                            "./configure",
                            f"--prefix={erlang_install_dir / version}",
                            "--without-wx",  # no wxWidgets support
                            "--without-odbc",  # no ODBC support
                            stdout=stdout,
                        )
                        sh("make", stdout=stdout)
                        sh("make", "install", stdout=stdout)

    def install_tika(cfg):
        debug(f"Installing apache tika {cfg.ce_services.tika.version}")
        tika_path = (
            cfg.ce_services.tika.install_dir
            / f"tika-server-standard-{cfg.ce_services.tika.version}.jar"
        )
        if exists(tika_path):
            return

        mkdir(cfg.ce_services.tika.install_dir)
        url_path = f"tika/{cfg.ce_services.tika.version}/tika-server-standard-{cfg.ce_services.tika.version}.jar"  # noqa: E501
        for mirror in cfg.ce_services.tika.mirrors:
            if mirror[-1] == "/":
                url = f"{mirror}{url_path}"
            else:
                url = f"{mirror}/{url_path}"
            try:
                download(url, tika_path)
                break
            except HTTPError:
                warn(f"Tika {cfg.ce_services.tika.version} not found at {url}")
                continue
            except URLError:
                warn(f"{mirror} currently not reachable")
                continue
        else:
            die(  # pylint: disable=broad-exception-raised
                "Could not download Apache Tika from any of the mirrors."
            )

    install_traefik(cfg)
    install_redis(cfg)

    if cfg.ce_services.solr.use:
        if cfg.ce_services.solr.version:
            warn(
                "ce_services.solr.version will be ignored, using '{ce_services.solr.use}' instead."
            )

    if not cfg.ce_services.solr.use:
        install_solr(cfg)

    if cfg.ce_services.hivemq.enabled:
        install_hivemq(cfg)

    if cfg.ce_services.influxdb.enabled:
        install_influxdb(cfg)

    if cfg.ce_services.rabbitmq.enabled:
        install_rabbitmq(cfg)
        install_erlang(cfg)

    if cfg.contact_elements.umbrella not in ("16.0", "2026.1"):
        install_tika(cfg)


def init(cfg):
    """
    Set all provisioned tools into the PATH variable.
    """
    path_extensions = {
        cfg.ce_services.traefik.install_dir / cfg.ce_services.traefik.version,
    }

    if cfg.ce_services.solr.use:
        from shutil import which  # noqa: F401

        solr_path = which(cfg.ce_services.solr.use)
        if not solr_path:
            die(
                f"Cannot find Solr executable: {cfg.ce_services.solr.use}. "
                "Please check your configuration."
            )
        path_extensions.add(solr_path)

    else:
        path_extensions.add(
            cfg.ce_services.solr.install_dir
            / f"solr-{cfg.ce_services.solr.version}{cfg.ce_services.solr.version_postfix}"
            / "bin"
        )

    if sys.platform == "win32":
        path_extensions.add(
            cfg.ce_services.redis.install_dir / cfg.ce_services.redis.version
        )

    if cfg.ce_services.influxdb.enabled:
        path_extensions.add(
            cfg.ce_services.influxdb.install_dir / cfg.ce_services.influxdb.version
        )

    if cfg.ce_services.hivemq.enabled:
        hivemq_intgr_dir = cfg.ce_services.hivemq.elements_integration.install_dir

        if not hivemq_intgr_dir or not exists(hivemq_intgr_dir):
            die(
                "CONTACT Elements HiveMQ Integration installation directory"
                f" does not exist. ({hivemq_intgr_dir})"
            )

        setenv(
            HIVEMQ_HOME=cfg.ce_services.hivemq.install_dir
            / cfg.ce_services.hivemq.version
        )
        setenv(
            HIVEMQ_EXTENSION_FOLDER=cfg.ce_services.hivemq.elements_integration.install_dir
        )

    if cfg.ce_services.rabbitmq.enabled:
        path_extensions.add(
            (
                rabbitmq_home := cfg.ce_services.rabbitmq.install_dir
                / cfg.ce_services.rabbitmq.version
            )
            / "sbin"
        )
        path_extensions.add(
            cfg.ce_services.rabbitmq.erlang.install_dir
            / cfg.ce_services.rabbitmq.erlang.version
            / "bin"
        )
        setenv(
            RABBITMQ_HOME=rabbitmq_home,
            RABBITMQ_MNESIA_DIR=cfg.spin.spin_dir / "rabbitmq",
            RABBITMQ_LOG_BASE=cfg.mkinstance.base.instance_location / "tmp",
            ERLANG_HOME=cfg.ce_services.rabbitmq.erlang.install_dir
            / cfg.ce_services.rabbitmq.erlang.version,
        )
    if cfg.contact_elements.umbrella not in ("16.0", "2026.1"):
        setenv(
            TIKA_PATH=cfg.ce_services.tika.install_dir
            / f"tika-server-standard-{cfg.ce_services.tika.version}.jar"
        )

    setenv(
        PATH=f"{os.pathsep.join([str(e) for e in path_extensions])}{os.pathsep}{os.getenv('PATH', '')}"
    )
