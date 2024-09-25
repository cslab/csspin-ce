# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/
# pylint: disable=too-many-lines

"""
Provides a wrapper around the CLI tool of ce_services and
provisions all tool necessary for these ce_services.
"""

import filecmp
import os
import shutil
import sys

from path import Path
from spin import (
    config,
    copy,
    debug,
    die,
    exists,
    mkdir,
    option,
    rmtree,
    setenv,
    sh,
    task,
)

defaults = config(
    requires=config(
        spin=[
            "spin_ce.mkinstance",
        ],
        python=[
            "ce_services",
            "requests",
            "psutil",
        ],
    ),
    hivemq=config(
        enabled=False,
        install_dir="{spin.cache}/hivemq",
        version="2024.4",
        elements_integration=config(
            version="1.0",
            user="csiot_integrator",
            password="",  # nosec: hardcoded_password_funcarg
            install_dir="{spin.cache}/hivemq-elements-integration",
        ),
    ),
    influxdb=config(
        enabled=False,
        version="1.8.10",
        install_dir="{spin.cache}/influxdb",
    ),
    traefik=config(
        version="2.11.2",
        dashboard_port="",
        install_dir="{spin.cache}/traefik",
    ),
    solr=config(
        version="9.7.0",
        install_dir="{spin.cache}/solr",
        version_postfix="-slim",
    ),
    redis=config(
        version="7.2.4",
        install_dir="{spin.cache}/redis",
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
        additional_cfg["instance_admpwd"] = cfg.mkinstance.instance_admpwd
    # "--loglevel": None, # TODO: Set it depending on the verbosity level of spin
    if cfg.ce_services.influxdb.enabled:
        additional_cfg["influxd"] = True
    if cfg.ce_services.hivemq.enabled:
        additional_cfg["hivemq"] = True
        hivemq_options = {
            "hivemq_bin_path": cfg.ce_services.hivemq.install_dir
            / cfg.ce_services.hivemq.version,
            "hivemq_elements_integration_install_dir": (
                cfg.ce_services.hivemq.elements_integration.install_dir
            ),
            "hivemq_elements_integration_password": cfg.ce_services.hivemq.elements_integration.password,
            "hivemq_elements_integration_user": cfg.ce_services.hivemq.elements_integration.user,
            "hivemq_elements_integration_version": cfg.ce_services.hivemq.elements_integration.version,
        }
        for key, value in hivemq_options.items():
            if value:
                additional_cfg[key] = value

    return additional_cfg


@task(aliases=["ce_services"])
def ce_services(cfg, instance: option("-i", "--instance"), args):  # noqa: F821
    """
    Start the ce services synchronously.
    """
    inst = (
        os.path.abspath(instance) if instance else cfg.mkinstance.base.instance_location
    )
    if not os.path.isdir(inst):
        die(f"Cannot find the CE instance '{inst}'.")
    setenv(CADDOK_BASE=inst)

    # Now set the relevant CLI options from cfg, making sure to only add those
    # from cfg that haven't already been set by the CLI.
    all_cli_args = list(args)
    for key, value in extract_service_config(cfg).items():
        cli_option_name = f"--{key}"
        if cli_option_name not in args:
            if cli_option_name in ("--influxd", "--hivemq"):
                all_cli_args.append(cli_option_name)
            else:
                all_cli_args.append(f"{cli_option_name}={value}")

    sh("ce_services", *all_cli_args)


def provision(cfg):  # pylint: disable=too-many-statements
    """
    Provision tools necessary to startup all ce_services.
    """
    import tarfile
    import zipfile
    from tempfile import TemporaryDirectory

    from spin import download

    def extract(archive, extract_to, member=""):
        """Unpacks archives"""
        member = member.replace("\\", "/")

        if tarfile.is_tarfile(archive):
            extractor = tarfile.open
            mode = "r:gz"
        elif zipfile.is_zipfile(archive):
            extractor = zipfile.ZipFile
            mode = "r"
        else:
            raise KeyError("Unsupported archive type...")

        with extractor(archive, mode=mode) as arc:
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
        mkdir(traefik_install_dir)

        traefik = traefik_install_dir / f"traefik{cfg.platform.exe}"

        if not traefik.exists():
            debug("Installing Traefik")

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

        venv_traefik = cfg.python.scriptdir / f"traefik{cfg.platform.exe}"
        if not exists(venv_traefik) or not filecmp.cmp(traefik, venv_traefik):
            copy(traefik, venv_traefik)

    def install_solr(cfg):
        version = cfg.ce_services.solr.version
        install_dir = cfg.ce_services.solr.install_dir
        postfix = cfg.ce_services.solr.version_postfix
        mkdir(install_dir)

        solr_name = Path(f"solr-{version}{postfix}")
        solr_path = install_dir / solr_name

        if not solr_path.exists():
            debug("Installing Apache Solr")
            archive = f"{solr_name}.tgz"
            with TemporaryDirectory() as tmp_dir:
                archive_path = Path(tmp_dir) / archive
                download(
                    f"https://archive.apache.org/dist/solr/solr/{version}/{archive}",
                    archive_path,
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
                    ).rename(redis_install_dir)
            else:
                debug(f"Using cached redis-server ({redis})")
            venv_redis = cfg.python.scriptdir / "redis-server.exe"
            if not exists(venv_redis) or not filecmp.cmp(redis, venv_redis):
                copy(redis, cfg.python.scriptdir / "redis-server.exe")

        elif not shutil.which("redis-server"):
            die(
                "Cannot provision redis on linux. Install it yourself and make sure its available in PATH!"  # noqa: E501
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

        integration_version = cfg.ce_services.hivemq.elements_integration.version
        hivemq_elements_integration_dir = (
            cfg.ce_services.hivemq.elements_integration.install_dir
            / integration_version
            / "hivemq-elements-integration"
        )  # HiveMQ expects plugins to be in a subfolder
        if exists(hivemq_elements_integration_dir):
            debug(
                "Using cached HiveMQ Elements Integration"
                f" ({hivemq_elements_integration_dir})"
            )
        else:
            debug(f"Installing HiveMQ Elements Integration {integration_version}")
            elements_integration_zipfile = (
                "hivemq-elements-integration-" f"{integration_version}-distribution.zip"
            )
            _download(
                url="https://code.contact.de/api/v4/projects/566/packages/"
                "generic/hivemq-elements-integration/"
                f"{integration_version}/{elements_integration_zipfile}",
                zipfile_name=elements_integration_zipfile,
                unpacked_source_directory="hivemq-elements-integration",
                target_directory=hivemq_elements_integration_dir,
                ignore={elements_integration_zipfile},
            )

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
                        debug("Moving" f" {(source := sources / f)} -> {influxdb_dir}")
                        shutil.move(source, influxdb_dir)
                        os.chmod((f := influxdb_dir / f), os.stat(f).st_mode | S_IEXEC)
        else:
            debug(f"Using cached InfluxDB ({influxdb_dir})")

        influxd = influxdb_dir / f"influxd{cfg.platform.exe}"
        venv_influxd = cfg.python.scriptdir / f"influxd{cfg.platform.exe}"
        if not exists(venv_influxd) or not filecmp.cmp(influxd, venv_influxd):
            copy(influxd, venv_influxd)

    install_traefik(cfg)
    install_redis(cfg)
    install_solr(cfg)

    if cfg.ce_services.hivemq.enabled:
        install_hivemq(cfg)

    if cfg.ce_services.influxdb.enabled:
        install_influxdb(cfg)


def init(cfg):
    """Sets some environment variables"""
    setenv(
        PATH=cfg.ce_services.solr.install_dir
        / f"solr-{cfg.ce_services.solr.version}{cfg.ce_services.solr.version_postfix}"
        / "bin"
        + os.pathsep
        + "{PATH}"
    )
