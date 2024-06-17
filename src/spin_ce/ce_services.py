# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/
# pylint: disable=too-many-lines

import asyncio
import atexit
import contextlib
import json
import os
import shutil
import subprocess  # nosec: blacklist
import sys
import time
from importlib.util import find_spec
from pathlib import Path

from spin import (
    config,
    die,
    echo,
    exists,
    info,
    interpolate1,
    mkdir,
    option,
    rmtree,
    setenv,
    sh,
    task,
    warn,
)

defaults = config(
    requires=config(
        spin=[
            "spin_ce.mkinstance",
        ],
        python=[
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
    timeout=30,
    loglevel="WARNING",
)


@contextlib.contextmanager
def with_ce_services(
    cfg,
):  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    def _get_cdb_secret(path):
        cmdline = ["cdbwallet", "resolve", path]
        return subprocess.check_output(
            cmdline, encoding="utf-8"
        ).strip()  # nosec: subprocess_without_shell_equals_true

    required_env_dir_vars = {"CADDOK_BASE"}
    required_binaries_in_path = {
        "java",
        "python",
        "redis-server",
        "solr",
        "traefik",
    }
    if cfg.ce_services.influxdb.enabled:
        required_binaries_in_path.add("influxd")

    required_scripts_in_venv = {"blobstore", "cdbsrv", "cdbwallet", "powerscript"}

    for env_dir_var in required_env_dir_vars:
        if env_dir_var not in os.environ:
            die(f"{env_dir_var} must be set!")
        elif not Path(os.environ[env_dir_var]).exists():
            die(f"Directory/File {env_dir_var} does not exist")

    for required_binary in required_binaries_in_path:
        if not shutil.which(required_binary):
            die(f"{required_binary} is not in path")

    for required_script in required_scripts_in_venv:
        if not shutil.which(required_script):
            die(f"{required_script} is not in path")

    # Common global variables
    TMP = Path(os.environ["CADDOK_BASE"]) / "tmp"

    CADDOK_SERVICE_CONFIG = (
        Path(os.environ["CADDOK_BASE"]) / "etc" / "webdev_services.json"
    )
    LOGGING_DEFAULT_CONFIG = (
        Path(os.environ["CADDOK_BASE"]) / "etc" / "stdout_logging_config.json"
    )

    HOST = "localhost"
    JAVA_LIB_DIR = (
        Path(sys.prefix) / "lib" / "java"
    )  # might change see https://cedm.contact.de/info/spec_object/4fdd9800-3292-11ee-845b-1212fb5a4405

    # Service specific global variables
    # Traefik
    TRAEFIK_DYN_CONF_FILE = Path(interpolate1(cfg.python.venv)) / "traefik.yml"
    TRAEFIK_HTTP_PORT = 8080
    TRAEFIK_HTTP_URL = f"http://{HOST}:{TRAEFIK_HTTP_PORT}"
    TRAEFIK_DASHBOARD_PORT = interpolate1(cfg.ce_services.traefik.dashboard_port)
    if TRAEFIK_DASHBOARD_PORT:
        TRAEFIK_DASHBOARD_URL = f"http://{HOST}:{TRAEFIK_DASHBOARD_PORT}/dashboard/"
    else:
        TRAEFIK_DASHBOARD_URL = ""
    loglevel = interpolate1(cfg.ce_services.loglevel)
    if loglevel in ("DEBUG", "INFO", "ERROR"):
        TRAEFIK_LOGLEVEL = loglevel
    elif loglevel in ("WARN", "WARNING"):
        TRAEFIK_LOGLEVEL = "WARN"
    elif loglevel == "CRITICAL":
        TRAEFIK_LOGLEVEL = "FATAL"
    else:
        TRAEFIK_LOGLEVEL = "ERROR"

    # Solr
    # SOLR_HOME might change see https://cedm.contact.de/info/spec_object/6810aaa8-2a2c-11ee-b733-26ee43b009f5
    SOLR_HOME = Path(f"{os.environ['CADDOK_BASE']}/storage/index/search").resolve()
    SOLR_PORT = 54670
    SOLR_BASE_URL = f"http://{HOST}:{SOLR_PORT}"
    SOLR_URL = f"{SOLR_BASE_URL}/solr/core1"
    SOLR_CLASSIFICATION_URL = f"{SOLR_BASE_URL}/solr/classification"
    SOLR_USERNAME = _get_cdb_secret("/cs.platform/solr/auth/username")
    SOLR_PASSWORD = ""  # nosec: hardcoded_password_string
    if classification_spec := find_spec("cs.classification"):
        CLASSIFICATION_INSTALLED = True
        SOLR_CLASSIFICATION_CORE_TEMPLATE_PATH = (
            Path(os.path.dirname(Path(classification_spec.origin).resolve()))
            / "solr-core-template"
            / "classification"
        )
        CLASSIFICATION_CORE_DST_PATH = SOLR_HOME / "classification"
    else:
        CLASSIFICATION_INSTALLED = False
        SOLR_CLASSIFICATION_CORE_TEMPLATE_PATH = None
        CLASSIFICATION_CORE_DST_PATH = None

    # Tes
    TES_PORT = 54671
    TES_USERNAME = _get_cdb_secret("/cs.platform/tes/auth/username")
    TES_PASSWORD = ""  # nosec: hardcoded_password_string # TODO: Is it necessary?
    TES_URL = f"http://{HOST}:{TES_PORT}"

    # Blobstore
    BLOBSTORE_PORT = 8998
    BLOBSTORE_PASSWORD = _get_cdb_secret("/cs.platform/blobstore/admin_key")
    BLOBSTORE_URL = f"http://{HOST}:{BLOBSTORE_PORT}"

    # cdbsrv
    CDBSRV_1_PORT = 8900
    CDBSRV_2_PORT = 8901
    CDBSRV_USERNAME = "caddok"
    CDBSRV_PASSWORD = interpolate1(cfg.mkinstance.base.instance_admpwd)
    CDBSRV_1_URL = f"http://{HOST}:{CDBSRV_1_PORT}"
    CDBSRV_2_URL = f"http://{HOST}:{CDBSRV_2_PORT}"

    # Redis
    REDIS_PORT = 6379
    # Using 127.0.0.1 for the URL as Redis won't work on Windows when using localhost
    REDIS_URL = f"redis://127.0.0.1:{REDIS_PORT}/0"

    # Gatekeeper
    GATEKEEPER_PORT = 8992
    GATEKEEPER_URL = f"http://{HOST}:{GATEKEEPER_PORT}"

    # OIDC-Server
    OIDC_SERVER_PORT = 8991
    OIDC_SERVER_URL = f"http://{HOST}:{OIDC_SERVER_PORT}"
    OIDC_SERVER_ISSUER_URL = f"{TRAEFIK_HTTP_URL}/oidc"

    # ologin
    OLOGIN_PORT = 8993
    OLOGIN_URL = f"http://{HOST}:{OLOGIN_PORT}"
    OIDC_LOGIN_URL = f"{TRAEFIK_HTTP_URL}/ologin"

    # Traefik Service Conf
    TRAEFIK_CONF = {
        "http": {
            "services": {
                "ce16worker": {
                    "loadBalancer": {
                        "servers": [
                            {"url": CDBSRV_1_URL},
                            {"url": CDBSRV_2_URL},
                        ]
                    }
                },
                "ce16gatekeeper": {
                    "loadBalancer": {"servers": [{"url": GATEKEEPER_URL}]}
                },
                "ce16ologin": {"loadBalancer": {"servers": [{"url": OLOGIN_URL}]}},
                "ce16oidc": {"loadBalancer": {"servers": [{"url": OIDC_SERVER_URL}]}},
                "ce16blobs": {"loadBalancer": {"servers": [{"url": BLOBSTORE_URL}]}},
            },
            "routers": {
                "ceworker-route": {
                    "rule": "PathPrefix(`/`)",
                    "service": "ce16worker",
                    "priority": 1,
                },
                "ceologin-route": {
                    "rule": "Path(`/ologin`)",
                    "priority": 10,
                    "service": "ce16ologin",
                },
                "ceoidc-route": {
                    "rule": "PathPrefix(`/oidc`)",
                    "service": "ce16oidc",
                    "priority": 50,
                },
                "ceblobs-route": {
                    "rule": "PathPrefix(`/signedblob`)",
                    "service": "ce16blobs",
                },
            },
        },
    }

    if TRAEFIK_DASHBOARD_PORT:
        TRAEFIK_CONF["http"]["routers"]["traefik-dashboard-route"] = {
            "entryPoints": ["traefik"],
            "rule": "(PathPrefix(`/api`) || PathPrefix(`/dashboard`))",
            "service": "api@internal",
        }

    SERVICES = {
        "blobstore": {
            "cmdline": ["blobstore"],
            "env": {"CADDOK_LOGGING_CONFIG": str(LOGGING_DEFAULT_CONFIG)},
            "poll": [
                {
                    "url": BLOBSTORE_URL,
                    "auth": ("caddok", BLOBSTORE_PASSWORD),
                }
            ],
        },
        "solr": {
            "cmdline": [
                "solr",
                "start",
                "-p",
                f"{SOLR_PORT}",
                "-s",
                f"{SOLR_HOME}",
                "-v",
            ],
            "poll": [
                {
                    "url": SOLR_URL + "/admin/ping",
                    "auth": (SOLR_USERNAME, SOLR_PASSWORD),
                },
                {
                    "url": SOLR_CLASSIFICATION_URL + "/admin/ping",
                    "auth": (SOLR_USERNAME, SOLR_PASSWORD),
                    "skip": not CLASSIFICATION_INSTALLED,
                },
            ],
        },
        "tes": {
            "cmdline": [
                "java",
                "-XX:-UseGCOverheadLimit",
                "-Xmx1536M",
                "-Xms256M",
                "-Dcom.sun.management.jmxremote.authenticate=false",
                "-cp",
                f"{JAVA_LIB_DIR}/*",
                "de.contact.cdb.main.TextExtractor",
                "--port",
                f"{TES_PORT}",
                "--log-dir",
                f'{os.environ["CADDOK_BASE"]}/tmp/logs',  # nosec: hardcoded_tmp_directory
                "--log-level",
                "6",
                "--fork-max-heapspace",
                "2048",
                "--max-content-size",
                "0",
                "--max-compound-age",
                "5000",
                "--auth-user",
                TES_USERNAME,
                # '--auth-pwd', TES_PASSWORD,  # TODO: Is it never set?
                "--num-extractors",
                "4",
                "--max-compound-size",
                "20",
                "--max-jobs-in-queue",
                "5000",
                "--instance-root",
                f'{os.environ["CADDOK_BASE"]}',
                "--extensions",
                "log,txt,pdf,zip,csv",
            ],
            "env": {
                "CADDOK_BLOBSTORE_URL": BLOBSTORE_URL,
                "CADDOK_SOLR_URL": SOLR_URL,
                "CADDOK_SOLR_USERNAME": SOLR_USERNAME,
                "CADDOK_SOLR_PW": SOLR_PASSWORD,
            },
            "poll": [
                {
                    "url": f"{TES_URL}/tes/info/tes",
                    "auth": (TES_USERNAME, TES_PASSWORD),
                }
            ],
        },
        "tesjobqueue": {
            "cmdline": [
                "powerscript",
                "--user",
                "caddok",
                "-m",
                "cdb.storage.index.tesjobqueue",
            ],
            "env": {"CADDOK_LOGGING_CONFIG": str(LOGGING_DEFAULT_CONFIG)},
        },
        "cdbsrv1": {
            "cmdline": [
                "cdbsrv",
                "--endpoint",
                f"tcp:{CDBSRV_1_PORT}:interface={HOST}",
            ],
            "env": {
                "CADDOK_SERVICE_CONFIG": f"{CADDOK_SERVICE_CONFIG}",
                "CADDOK_LOGGING_CONFIG": str(LOGGING_DEFAULT_CONFIG),
            },
            "poll": [
                {
                    "url": CDBSRV_1_URL,
                    "auth": (CDBSRV_USERNAME, CDBSRV_PASSWORD),
                }
            ],
        },
        "cdbsrv2": {
            "cmdline": [
                "cdbsrv",
                "--endpoint",
                f"tcp:{CDBSRV_2_PORT}:interface={HOST}",
            ],
            "env": {
                "CADDOK_SERVICE_CONFIG": f"{CADDOK_SERVICE_CONFIG}",
                "CADDOK_LOGGING_CONFIG": str(LOGGING_DEFAULT_CONFIG),
            },
            "poll": [
                {
                    "url": CDBSRV_2_URL,
                    "auth": (CDBSRV_USERNAME, CDBSRV_PASSWORD),
                }
            ],
        },
        "redis": {
            "cmdline": ["redis-server", "--appendonly", "yes", "--dir", f"{TMP}"],
        },
        "traefik": {
            "cmdline": (
                [
                    "traefik",
                    f"--providers.file.filename={TRAEFIK_DYN_CONF_FILE}",
                    f"--log.level={TRAEFIK_LOGLEVEL}",
                    "--accesslog=true",
                    f"--entryPoints.web.address=:{TRAEFIK_HTTP_PORT}",
                    "--api=true",
                    "--api.dashboard=true",
                    f"--entryPoints.traefik.address=:{TRAEFIK_DASHBOARD_PORT}",
                ]
                if TRAEFIK_DASHBOARD_PORT
                else [
                    "traefik",
                    f"--providers.file.filename={TRAEFIK_DYN_CONF_FILE}",
                    f"--log.level={TRAEFIK_LOGLEVEL}",
                    "--accesslog=true",
                    f"--entryPoints.web.address=:{TRAEFIK_HTTP_PORT}",
                ]
            ),
            "poll": [
                {"url": TRAEFIK_HTTP_URL},
                {"url": TRAEFIK_DASHBOARD_URL, "skip": not TRAEFIK_DASHBOARD_URL},
            ],
        },
        "gatekeeper": {
            "cmdline": [
                "gatekeeper",
                "--endpoint",
                f"tcp:{GATEKEEPER_PORT}:interface={HOST}",
                "--workers",
                "2",
            ],
            "env": {
                "CADDOK_LOGGING_CONFIG": str(LOGGING_DEFAULT_CONFIG),
            },
        },
        "oidc_server": {
            "cmdline": [
                "oidc_server",
                "--endpoint",
                f"tcp:{OIDC_SERVER_PORT}:interface={HOST}",
                "--issuer",
                OIDC_SERVER_ISSUER_URL,
            ],
            "env": {
                "CADDOK_SERVICE_CONFIG": f"{CADDOK_SERVICE_CONFIG}",
                "CADDOK_LOGGING_CONFIG": str(LOGGING_DEFAULT_CONFIG),
            },
            "poll": [{"url": OIDC_SERVER_ISSUER_URL}],
        },
        "oidc_sync": {
            "cmdline": ["oidc_client_sync"],
            "env": {
                "CADDOK_SERVICE_CONFIG": f"{CADDOK_SERVICE_CONFIG}",
                "CADDOK_LOGGING_CONFIG": str(LOGGING_DEFAULT_CONFIG),
            },
        },
        "ologin": {
            "cmdline": ["ologin", "--endpoint", f"tcp:{OLOGIN_PORT}:interface={HOST}"],
            "env": {
                "CADDOK_LOGGING_CONFIG": str(LOGGING_DEFAULT_CONFIG),
            },
            "poll": [{"url": OIDC_LOGIN_URL}],
        },
    }

    if cfg.ce_services.hivemq.enabled:
        # HiveMQ Service Configuration
        HIVEMQ_EXTENSION_FOLDER = (
            Path(
                interpolate1(cfg.ce_services.hivemq.elements_integration.install_dir),
            )
            / cfg.ce_services.hivemq.elements_integration.version
        )
        HIVEMQ_WORKSPACE = Path(os.environ["CADDOK_BASE"]) / "etcd" / "hivemq-workspace"
        EXECUTABLE = (
            Path(interpolate1(cfg.ce_services.hivemq.install_dir))
            / cfg.ce_services.hivemq.version
            / "bin"
            / str("run.bat" if sys.platform == "win32" else "run.sh")
        )

        HIVEMQ_DATA_FOLDER = HIVEMQ_WORKSPACE / "data"
        HIVEMQ_BACKUP_FOLDER = HIVEMQ_WORKSPACE / "backup"
        HIVEMQ_AUDIT_FOLDER = HIVEMQ_WORKSPACE / "audit"

        for directory in (
            HIVEMQ_DATA_FOLDER,
            HIVEMQ_BACKUP_FOLDER,
            HIVEMQ_AUDIT_FOLDER,
        ):
            mkdir(directory)

        SERVICES["hivemq"] = {
            "cmdline": [str(EXECUTABLE)],
            "env": {
                "HIVEMQ_EXTENSION_FOLDER": str(HIVEMQ_EXTENSION_FOLDER),
                "HIVEMQ_DATA_FOLDER": str(HIVEMQ_DATA_FOLDER),
                "HIVEMQ_BACKUP_FOLDER": str(HIVEMQ_BACKUP_FOLDER),
                "HIVEMQ_AUDIT_FOLDER": str(HIVEMQ_AUDIT_FOLDER),
                "HIVEMQ_CONFIG_FOLDER": str(HIVEMQ_WORKSPACE),
                # Options for the hivemq-elements plugin
                "HIVEMQ_ELEMENTS_USER": cfg.ce_services.hivemq.elements_integration.user,
                "HIVEMQ_ELEMENTS_PASSWORD": cfg.ce_services.hivemq.elements_integration.password,
                "HIVEMQ_ELEMENTS_INSTANCE_URL": TRAEFIK_HTTP_URL,
                "HIVEMQ_ELEMENTS_CONNECTOR": "default-mqtt",
            },
        }

    if cfg.ce_services.influxdb.enabled:
        mkdir(
            INFLUX_WORK_DIR := Path(os.environ["CADDOK_BASE"])
            / "etcd"
            / "influx-workspace"
        )

        SERVICES["influxdb"] = {
            "cmdline": ["influxd", "run"],
            "env": {
                "INFLUXDB_REPORTING_DISABLED": "True",
                "INFLUXDB_DATA_DIR": str(INFLUX_WORK_DIR / "data"),
                "INFLUXDB_DATA_WAL_DIR": str(INFLUX_WORK_DIR / "wal"),
                "INFLUXDB_META_DIR": str(INFLUX_WORK_DIR / "meta"),
            },
        }

    def setup_logging(cfg):
        """
        Setup logging for the services.
        """
        loglevel = interpolate1(cfg.ce_services.loglevel)
        if not os.path.isfile(str(LOGGING_DEFAULT_CONFIG)):
            with open(str(LOGGING_DEFAULT_CONFIG), "w+", encoding="utf-8") as f:
                stdout_logging_config = {
                    "version": 1,
                    "disable_existing_loggers": False,
                    "formatters": {
                        "simple": {
                            "format": "[%(asctime)s] [PID %(process)d] [%(levelname)-8s] %(name)s %(message)s"
                        },
                        "standard": {
                            "format": "[%(asctime)s.%(msecs)03d] [%(levelname)-8s] %(name)s %(message)s (%(pathname)s:%(lineno)s)",  # noqa: E501
                            "datefmt": "%Y-%m-%dT%H:%M:%S",
                        },
                    },
                    "handlers": {
                        "sysstdout": {
                            "class": "logging.StreamHandler",
                            "level": loglevel,
                            "stream": "ext://sys.stdout",
                            "formatter": "simple",
                        }
                    },
                    "root": {"handlers": ["sysstdout"], "level": "NOTSET"},
                }
                json.dump(fp=f, obj=stdout_logging_config, indent=4, ensure_ascii=False)

    def run_service(name, data):
        cmdline = data["cmdline"]
        env = os.environ.update(data.get("env", {}))

        cmd = Path(cmdline[0])
        if not cmd.is_absolute():
            if abs_cmd := shutil.which(str(cmd)):
                cmdline[0] = abs_cmd
            else:
                warn(
                    f"It is recommended to use absolute paths. {cmd} might not be found."
                )

        echo(subprocess.list2cmdline(cmdline))
        # write subprocess output to separate files for each process
        out_file = open(  # pylint: disable=consider-using-with
            TMP / f"dev_{name}.log", "w", encoding="utf-8"
        )
        err_file = open(  # pylint: disable=consider-using-with
            TMP / f"dev_{name}.err", "w", encoding="utf-8"
        )
        subprocess.Popen(  # pylint: disable=consider-using-with # nosec: subprocess_without_shell_equals_true
            cmdline, env=env, stdout=out_file, stderr=err_file
        )

    def run_all(cfg):
        if (
            SOLR_CLASSIFICATION_CORE_TEMPLATE_PATH is not None
            and SOLR_CLASSIFICATION_CORE_TEMPLATE_PATH.exists()
            and CLASSIFICATION_CORE_DST_PATH is not None
            and not CLASSIFICATION_CORE_DST_PATH.exists()
        ):
            shutil.copytree(
                SOLR_CLASSIFICATION_CORE_TEMPLATE_PATH, CLASSIFICATION_CORE_DST_PATH
            )
            if sys.platform == "win32":
                echo(
                    f"Copy-Item -Recurse {SOLR_CLASSIFICATION_CORE_TEMPLATE_PATH} {CLASSIFICATION_CORE_DST_PATH}"  # noqa: E501
                )
            else:
                echo(
                    f"cp -r {SOLR_CLASSIFICATION_CORE_TEMPLATE_PATH} {CLASSIFICATION_CORE_DST_PATH}"
                )
        for service in SERVICES.items():
            run_service(*service)

        asyncio.run(wait_until_services_are_up(cfg))

    def kill_process_tree(root_pid):
        """Kill the process tree by given PID."""
        import psutil

        try:
            parent = psutil.Process(root_pid)
            children = parent.children(recursive=True)
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            warn("Failed to find or access process.")
        else:
            for child in children:
                try:
                    child.kill()
                except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                    warn("Failed to kill process child.")

    @atexit.register
    def terminate_all():
        info("Kill all sub processes")
        kill_process_tree(os.getpid())
        run_service("solr", {"cmdline": ["solr", "stop", "-p", f"{SOLR_PORT}"]})

    def write_message_cache():  # FIXME: Is it useful?
        # Static messages for OIDC parts
        info("Writing message cache")
        # Starting powerscript throws lots of warnings. We don't care about them here.
        sh(
            "powerscript --run-level 3 -m cdb.scripts.dump_messages",
            stderr=subprocess.DEVNULL,
        )

    async def wait_until_services_are_up(cfg):
        import requests

        async def poll_service(url, auth):
            if auth:
                basic_auth = requests.auth.HTTPBasicAuth(*auth)
            while True:
                try:
                    if auth:
                        requests.get(url, timeout=5, auth=basic_auth).raise_for_status()
                    else:
                        requests.get(url, timeout=5).raise_for_status()
                    break
                except (
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError,
                    requests.exceptions.ReadTimeout,
                ):
                    await asyncio.sleep(1)

        async def poll_redis():
            # Needed as Redis is somewhat special. We assume that Redis is
            # running, when a TCP connection can be established.
            import socket

            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect(("localhost", REDIS_PORT))
                    s.close()
                    break
                except ConnectionRefusedError:
                    s.close()
                    await asyncio.sleep(1)

        timeout = int(cfg.ce_services.timeout)
        jobs = []
        jobs.append(asyncio.create_task(poll_redis(), name="redis"))
        for service_name, service_poll_data in [
            (name, service_data["poll"])
            for name, service_data in SERVICES.items()
            if "poll" in service_data
        ]:
            for poll_data in service_poll_data:
                if not poll_data.get("skip"):
                    jobs.append(
                        asyncio.create_task(
                            poll_service(
                                poll_data.get("url"),
                                poll_data.get("auth", None),
                            ),
                            name=service_name,
                        )
                    )
        _, pending = await asyncio.tasks.wait(jobs, timeout=timeout)
        if pending:
            die(
                f"The following services reached the timeout of {timeout} seconds during startup:\n"
                f"    {', '.join([t.get_name() for t in pending])}"
            )

    def update_service_registry():
        if CADDOK_SERVICE_CONFIG.is_file():
            service_configs = None
            with open(CADDOK_SERVICE_CONFIG, "r+", encoding="utf-8") as f:
                service_configs = json.load(fp=f)
            update_services = [
                {"name": "cdb.index.solr", "params": {"url": SOLR_URL}},
                {"name": "cdb.index.tes", "params": {"url": TES_URL}},
                {
                    "name": "cdb.storage.blobstore/main",
                    "params": {"url": BLOBSTORE_URL},
                },
                {"name": "cdb.gatekeeper", "params": {"url": GATEKEEPER_URL}},
                {"name": "cdb.ologin", "params": {"url": OLOGIN_URL}},
                {
                    "name": "cdb.ologin.storage",
                    "params": {
                        "statestore": "memory",
                        "url": "redis://127.0.0.1:6379/0",
                    },
                },
                {
                    "name": "cdb.oidc.provider",
                    "params": {
                        "issuer": OIDC_SERVER_ISSUER_URL,
                        "url": OIDC_SERVER_URL,
                    },
                },
                {"name": "cdb.oidc.storage", "params": {"url": REDIS_URL}},
                {
                    "name": "cdb.sessionstore",
                    "params": {
                        "session_type": "ext:redis",
                        "url": "redis://127.0.0.1:6379/0",
                    },
                },
                {
                    "name": "cdb.storage.sessiondata",
                    "params": {
                        "backend": "cdb.sessiondata.RedisBackend",
                        "url": "redis://127.0.0.1:6379/0",
                    },
                },
                {"name": "ce_services.endpoint", "params": {"url": TRAEFIK_HTTP_URL}},
            ]
            if CLASSIFICATION_INSTALLED:
                update_services.append(
                    {"name": "cs.classification.solr", "params": {"url": SOLR_BASE_URL}}
                )

            for update_service in update_services:
                for service in service_configs["services"]:
                    if update_service["name"] == service["name"]:
                        service["params"] |= update_service["params"]
                        break
                else:
                    # Service not there yet
                    service_configs["services"].append(update_service)

            with open(CADDOK_SERVICE_CONFIG, "w+", encoding="utf-8") as f:
                json.dump(
                    fp=f,
                    obj=service_configs,
                    ensure_ascii=False,
                    indent=4,
                    sort_keys=True,
                )
        else:
            die("Could not find CADDOK_SERVICE_CONFIG - aborting.")

    def setup_traefik_config():
        from ruamel.yaml import YAML

        with open(TRAEFIK_DYN_CONF_FILE, "w+", encoding="utf-8") as f:
            YAML(typ="safe", pure=True).dump(TRAEFIK_CONF, f)

    def setup_hivemq_config():
        from textwrap import dedent

        with open(HIVEMQ_WORKSPACE / "config.xml", "w", encoding="utf-8") as f:
            f.write(
                dedent(
                    """<?xml version="1.0"?>
                <hivemq>
                    <mqtt>
                        <session-expiry>
                            <max-interval>3600</max-interval>
                        </session-expiry>
                        <message-expiry>
                            <max-interval>3600</max-interval>
                        </message-expiry>
                    </mqtt>
                    <listeners>
                        <tcp-listener>
                            <port>1883</port>
                            <bind-address>0.0.0.0</bind-address>
                        </tcp-listener>
                        <websocket-listener>
                            <port>8000</port>
                            <bind-address>0.0.0.0</bind-address>
                            <path>/mqtt</path>
                            <subprotocols>
                            <subprotocol>mqttv3.1</subprotocol>
                            <subprotocol>mqtt</subprotocol>
                            </subprotocols>
                            <allow-extensions>true</allow-extensions>
                        </websocket-listener>
                    </listeners>
                    <anonymous-usage-statistics>
                        <enabled>false</enabled>
                    </anonymous-usage-statistics>
                </hivemq>
                """
                )
            )

    setup_logging(cfg)
    write_message_cache()
    update_service_registry()
    setup_traefik_config()

    if cfg.ce_services.hivemq.enabled:
        setup_hivemq_config()

    setenv(
        CADDOK_OIDC_ISSUER=OIDC_SERVER_ISSUER_URL,
        CADDOK_OIDC_LOGIN=OIDC_LOGIN_URL,
        CADDOK_ACTIVE_GUI_LANGUAGES='{{"Deutsch": "de", "English": "en"}}',
        CADDOK_OIDC_APP_REQUEST_TIMEOUT="60",
    )

    run_all(cfg)
    yield TRAEFIK_HTTP_URL


@task()
def ce_services(cfg, instance: option("-i", "--instance")):  # noqa: F821
    inst = (
        os.path.abspath(instance)
        if instance
        else interpolate1(cfg.mkinstance.base.instance_location)
    )
    if not os.path.isdir(inst):
        die(f"Cannot find the CE instance '{inst}'.")
    setenv(CADDOK_BASE=inst)
    with with_ce_services(cfg) as url:
        echo("#" * 80)
        echo(f"Visit {url} to access the instance. Press CTRL+C to shutdown.")
        echo("#" * 80)
        while True:
            time.sleep(1)


def provision(cfg):  # pylint: disable=too-many-statements
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


def cleanup(cfg):
    # Cleanup not needed because:
    # - We don't want to remove the cached files, so they can be reused
    # - The traefik.yml gets cleaned up anyway when the venv directory is being cleaned up
    pass
