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

import os
import shutil
import sys
from pathlib import Path

from spin import (
    config,
    die,
    exists,
    info,
    interpolate1,
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
    redis_install_dir="{spin.cache}/redis",
    redis_version="7.2.4",
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
        os.path.abspath(instance)
        if instance
        else interpolate1(cfg.mkinstance.base.instance_location)
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

    def install_traefik(cfg):
        # TODO: Download into tempdir (like for hivemq)
        traefik_install_base = Path(interpolate1(cfg.ce_services.traefik.install_dir))
        version = interpolate1(cfg.ce_services.traefik.version)
        traefik_install_dir = traefik_install_base / version

        if not traefik_install_base.exists():
            traefik_install_base.mkdir()
        if not traefik_install_dir.exists():
            traefik_install_dir.mkdir()

        if not any(
            x in os.listdir(traefik_install_dir) for x in ["traefik", "traefik.exe"]
        ):
            info("Installing Traefik")
            if sys.platform == "win32":
                traefik_url = f"https://github.com/traefik/traefik/releases/download/v{version}/traefik_v{version}_windows_amd64.zip"  # noqa: E501
                traefik_installer_archive = (
                    traefik_install_dir / f"traefik_v{version}_windows_amd64.zip"
                )
                download(traefik_url, traefik_installer_archive)
                with zipfile.ZipFile(traefik_installer_archive, "r") as zipped:
                    zipped.extractall(
                        members=["traefik.exe"], path=traefik_install_dir
                    )  # nosec: tarfile_unsafe_members
                traefik_installer_archive.unlink()
            else:
                traefik_url = f"https://github.com/traefik/traefik/releases/download/v{version}/traefik_v{version}_linux_amd64.tar.gz"  # noqa: E501
                traefik_installer_archive = (
                    traefik_install_dir / f"traefik_v{version}_linux_amd64.tar.gz"
                )
                download(traefik_url, traefik_installer_archive)
                with tarfile.open(traefik_installer_archive, "r:gz") as tgz:
                    tgz.extractall(
                        members=["traefik"], path=traefik_install_dir
                    )  # nosec: tarfile_unsafe_members
                traefik_installer_archive.unlink()

    def install_redis(cfg):
        # TODO: Download into tempdir (like for hivemq)
        if sys.platform == "win32":
            redis_install_base = Path(interpolate1(cfg.ce_services.redis_install_dir))
            redis_install_dir = redis_install_base / cfg.ce_services.redis_version
            if not redis_install_base.exists():
                redis_install_base.mkdir()

            info("Installing redis-server")
            if not redis_install_dir.exists() or "redis-server.exe" not in os.listdir(
                redis_install_dir
            ):
                redis_installer_archive = (
                    redis_install_base
                    / f"redis-windows-{cfg.ce_services.redis_version}.zip"
                )
                download(
                    f"https://github.com/zkteco-home/redis-windows/archive/refs/tags/{cfg.ce_services.redis_version}.zip",  # noqa: E501
                    redis_installer_archive,
                )
                with zipfile.ZipFile(redis_installer_archive, "r") as zipped:
                    zipped.extractall(
                        path=redis_install_base
                    )  # nosec: tarfile_unsafe_members
                    (
                        redis_install_base
                        / f"redis-windows-{cfg.ce_services.redis_version}"
                    ).rename(redis_install_dir)
                redis_installer_archive.unlink()
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
                with zipfile.ZipFile(download_file, "r") as zippy:
                    zippy.extractall(path=tmp_dir)  # nosec: tarfile_unsafe_members

                for f in os.listdir(
                    (
                        unpacked_source_directory := Path(tmp_dir)
                        / unpacked_source_directory
                    )
                ):
                    if f not in ignore:
                        info(
                            "Moving"
                            f" {(source := str(unpacked_source_directory / f))}"
                            f" -> {(target := str(target_directory))}"
                        )
                        shutil.move(source, target)

        hivemq_version = cfg.ce_services.hivemq.version
        hivemq_base_dir = (
            Path(
                interpolate1(cfg.ce_services.hivemq.install_dir),
            )
            / hivemq_version
        )
        if exists(hivemq_base_dir):
            info(f"Using cached HiveMQ ({hivemq_base_dir})")
        else:
            info(f"Installing HiveMQ {hivemq_version}")
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
            Path(
                interpolate1(cfg.ce_services.hivemq.elements_integration.install_dir),
            )
            / integration_version
            / "hivemq-elements-integration"  # HiveMQ expects plugins to be in a subfolder
        )
        if exists(hivemq_elements_integration_dir):
            info(
                "Using cached HiveMQ Elements Integration"
                f" ({hivemq_elements_integration_dir})"
            )
        else:
            info(f"Installing HiveMQ Elements Integration {integration_version}")
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
        if exists(
            (
                influxdb_dir := Path(interpolate1(cfg.ce_services.influxdb.install_dir))
                / version
            )
        ):
            info(f"Using cached InfluxDB ({influxdb_dir})")
            return
        mkdir(influxdb_dir)

        info(f"Installing InfluxDB {version}")
        archive = f"influxdb-{version}_"
        if sys.platform == "win32":
            archive += "windows_amd64.zip"
            extractor = zipfile.ZipFile
            mode = "r"
        else:
            archive += "linux_amd64.tar.gz"
            extractor = tarfile.open
            mode = "r:gz"

        with TemporaryDirectory() as tmp_dir:
            download(
                f"https://dl.influxdata.com/influxdb/releases/{archive}",
                (archive_path := Path(tmp_dir) / archive),
            )
            with extractor(archive_path, mode=mode) as arc:
                arc.extractall(path=tmp_dir)  # nosec: tarfile_unsafe_members

            if (
                sources := Path(tmp_dir) / f"influxdb-{version}-1"
            ) and sys.platform == "win32":
                for f in os.listdir(sources):
                    info("Moving" f" {(source := sources / f)}" f" -> {influxdb_dir}")
                    shutil.move(source, influxdb_dir)
            else:
                from stat import S_IEXEC

                for f in os.listdir((sources := sources / "usr" / "bin")):
                    info("Moving" f" {(source := sources / f)} -> {influxdb_dir}")
                    shutil.move(source, influxdb_dir)
                    os.chmod((f := influxdb_dir / f), os.stat(f).st_mode | S_IEXEC)

    install_traefik(cfg)
    install_redis(cfg)

    if cfg.ce_services.hivemq.enabled:
        install_hivemq(cfg)

    if cfg.ce_services.influxdb.enabled:
        install_influxdb(cfg)


def init(cfg):
    """
    Set all provisioned tools into the PATH variable.
    """
    path_extensions = {
        Path(interpolate1(cfg.ce_services.traefik.install_dir))
        / interpolate1(cfg.ce_services.traefik.version),
    }

    if sys.platform == "win32":
        path_extensions.add(
            Path(interpolate1(cfg.ce_services.redis_install_dir))
            / cfg.ce_services.redis_version
        )

    if cfg.ce_services.hivemq.enabled:
        path_extensions.add(
            Path(interpolate1(cfg.ce_services.hivemq.install_dir))
            / interpolate1(cfg.ce_services.hivemq.version)
        )

    if cfg.ce_services.influxdb.enabled:
        path_extensions.add(
            Path(interpolate1(cfg.ce_services.influxdb.install_dir))
            / interpolate1(cfg.ce_services.influxdb.version)
        )

    setenv(
        PATH=f"{os.pathsep.join([str(e) for e in path_extensions])}{os.pathsep}{os.environ.get('PATH', '')}"
    )
