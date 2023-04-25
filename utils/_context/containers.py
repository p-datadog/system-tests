import os
import json
from pathlib import Path
import time
import docker
from docker.models.containers import Container
import pytest

from utils._context.library_version import LibraryVersion, Version
from utils.tools import logger

_client = docker.DockerClient.from_env()

_NETWORK_NAME = "system-tests_default"


def create_network():
    for _ in _client.networks.list(names=[_NETWORK_NAME,]):
        logger.debug(f"Network {_NETWORK_NAME} still exists")
        return

    logger.debug(f"Create network {_NETWORK_NAME}")
    _client.networks.create(_NETWORK_NAME, check_duplicate=True)


class TestedContainer:

    # https://docker-py.readthedocs.io/en/stable/containers.html
    def __init__(
        self,
        name,
        image_name,
        host_log_folder,
        environment=None,
        allow_old_container=False,
        healthcheck=None,
        command=None,
        **kwargs,
    ) -> None:
        self.name = name
        self.host_log_folder = host_log_folder
        self.allow_old_container = allow_old_container

        self.stop_previous_container()

        Path(self.log_folder_path).mkdir(exist_ok=True, parents=True)
        Path(f"{self.log_folder_path}/logs").mkdir(exist_ok=True, parents=True)

        self.image = ImageInfo(image_name, dir_path=self.log_folder_path)
        self.healthcheck = healthcheck
        self.environment = self.image.env | (environment or {})
        self.command = command
        self.kwargs = kwargs
        self._container = None

    @property
    def container_name(self):
        return f"system-tests-{self.name}"

    @property
    def log_folder_path(self):
        return f"./{self.host_log_folder}/docker/{self.name}"

    def get_existing_container(self) -> Container:
        for container in _client.containers.list(all=True, filters={"name": self.container_name}):
            if container.name == self.container_name:
                logger.debug(f"Container {self.container_name} found")
                return container

    def stop_previous_container(self):
        if self.allow_old_container:
            return

        if old_container := self.get_existing_container():
            logger.debug(f"Kill old container {self.container_name}")
            old_container.remove(force=True)

    def start(self) -> Container:
        if old_container := self.get_existing_container():
            if self.allow_old_container:
                self._container = old_container
                logger.debug(f"Use old container {self.container_name}")

                old_container.restart()

                return

            raise ValueError("Old container still exists")

        self._fix_host_pwd_in_volumes()

        logger.info(f"Start container {self.container_name}")

        self._container = _client.containers.run(
            image=self.image.name,
            name=self.container_name,
            hostname=self.name,
            environment=self.environment,
            command=self.command,
            # auto_remove=True,
            detach=True,
            network=_NETWORK_NAME,
            **self.kwargs,
        )

        self.wait_for_health()

    def wait_for_health(self):
        if not self.healthcheck:
            return

        cmd = self.healthcheck["test"]

        if not isinstance(cmd, str):
            assert cmd[0] == "CMD-SHELL", "Only CMD-SHELL is supported"
            cmd = cmd[1]

        retries = self.healthcheck.get("retries", 10)
        interval = self.healthcheck.get("interval", 1 * 1_000_000_000) / 1_000_000_000
        # timeout = self.healthcheck.get("timeout", 1 * 1_000_000_000) / 1_000_000_000
        start_period = self.healthcheck.get("start_period", 0) / 1_000_000_000

        if start_period:
            time.sleep(start_period)

        logger.info(f"Executing healthcheck {cmd} for {self.name}")

        for i in range(retries + 1):
            try:
                result = self._container.exec_run(cmd)

                logger.debug(f"Healthcheck #{i}: {result}")

                if result.exit_code == 0:
                    return
            except Exception as e:
                logger.debug(f"Healthcheck #{i}: {e}")

            time.sleep(interval)

        pytest.exit(f"Healthcheck {cmd} failed for {self._container.name}", 1)

    def _fix_host_pwd_in_volumes(self):
        # on docker compose, volume host path can starts with a "."
        # it means the current path on host machine. It's not supported in bare docker
        # replicate this behavior here
        if "volumes" not in self.kwargs:
            return

        host_pwd = os.getcwd()

        result = {}
        for k, v in self.kwargs["volumes"].items():
            if k.startswith("./"):
                k = f"{host_pwd}{k[1:]}"
            result[k] = v

        self.kwargs["volumes"] = result

    def save_logs(self):
        if not self._container:
            return

        with open(f"{self.log_folder_path}/stdout.log", "wb") as f:
            f.write(self._container.logs(stdout=True, stderr=False))

        with open(f"{self.log_folder_path}/stderr.log", "wb") as f:
            f.write(self._container.logs(stdout=False, stderr=True))

    def remove(self):

        if not self._container:
            return

        try:
            self._container.remove(force=True)
        except:
            # Sometimes, the container does not exists.
            # We can safely ignore this, because if it's another issue
            # it will be killed at startup

            pass


class ImageInfo:
    """data on docker image. data comes from `docker inspect`"""

    def __init__(self, image_name, dir_path):
        self.env = {}
        self.name = image_name
        try:
            self._image = _client.images.get(image_name)
        except docker.errors.ImageNotFound:
            logger.info(f"Image {image_name} has not been found locally")
            self._image = _client.images.pull(image_name)

        for var in self._image.attrs["Config"]["Env"]:
            key, value = var.split("=", 1)
            self.env[key] = value

        with open(f"{dir_path}/image.json", encoding="utf-8", mode="w") as f:
            json.dump(self._image.attrs, f, indent=2)


class ProxyContainer(TestedContainer):
    def __init__(self, host_log_folder, proxy_state) -> None:
        super().__init__(
            image_name="mitmproxy/mitmproxy",
            name="proxy",
            host_log_folder=host_log_folder,
            environment={
                "DD_SITE": os.environ.get("DD_SITE"),
                "DD_API_KEY": os.environ.get("DD_API_KEY"),
                "HOST_LOG_FOLDER": host_log_folder,
                "PROXY_STATE": json.dumps(proxy_state or {}),
            },
            working_dir="/app",
            volumes={
                f"./{host_log_folder}/interfaces/": {"bind": f"/app/{host_log_folder}/interfaces", "mode": "rw",},
                "./utils/": {"bind": "/app/utils/", "mode": "ro"},
            },
            ports={"11111/tcp": ("127.0.0.1", 11111)},
            command="python utils/proxy/core.py",
        )


class AgentContainer(TestedContainer):
    def __init__(self, host_log_folder, use_proxy=True) -> None:

        if "DD_API_KEY" not in os.environ:
            raise ValueError("DD_API_KEY is missing in env, please add it.")

        environment = {
            "DD_API_KEY": os.environ["DD_API_KEY"],
            "DD_ENV": "system-tests",
            "DD_HOSTNAME": "test",
            "DD_SITE": self.dd_site,
            "DD_APM_RECEIVER_PORT": self.agent_port,
            "DD_DOGSTATSD_PORT": "8125",
        }

        if use_proxy:
            environment["DD_PROXY_HTTPS"] = "http://proxy:8126"
            environment["DD_PROXY_HTTP"] = "http://proxy:8126"

        super().__init__(
            image_name="system_tests/agent",
            name="agent",
            host_log_folder=host_log_folder,
            environment=environment,
            healthcheck={"test": f"curl --fail http://localhost:{self.agent_port}/info", "retries": 60},
            ports={f"{self.agent_port}/tcp": ("127.0.0.1", self.agent_port)},
        )

        agent_version = self.image.env.get("SYSTEM_TESTS_AGENT_VERSION")

        if not agent_version:
            self.agent_version = None
        else:
            self.agent_version = Version(agent_version, "agent")

    @property
    def dd_site(self):
        return os.environ.get("DD_SITE", "datad0g.com")

    @property
    def agent_port(self):
        return 8127


class WeblogContainer(TestedContainer):
    def __init__(
        self,
        host_log_folder,
        environment=None,
        tracer_sampling_rate=None,
        appsec_rules=None,
        appsec_enabled=True,
        additional_trace_header_tags=(),
        use_proxy=True,
    ) -> None:

        super().__init__(
            image_name="system_tests/weblog",
            name="weblog",
            host_log_folder=host_log_folder,
            environment=environment or {},
            volumes={f"./{host_log_folder}/docker/weblog/logs/": {"bind": "/var/log/system-tests", "mode": "rw"},},
            # ddprof's perf event open is blocked by default by docker's seccomp profile
            # This is worse than the line above though prevents mmap bugs locally
            security_opt=["seccomp=unconfined"],
            healthcheck={"test": "curl --fail http://localhost:7777", "retries": 60},
            ports={"7777/tcp": ("127.0.0.1", 7777), "7778/tcp": ("127.0.0.1", 7778)},
        )

        self.tracer_sampling_rate = tracer_sampling_rate

        self.weblog_variant = self.image.env.get("SYSTEM_TESTS_WEBLOG_VARIANT", None)

        if self.library == "php":
            self.php_appsec = Version(self.image.env.get("SYSTEM_TESTS_PHP_APPSEC_VERSION"), "php_appsec")
        else:
            self.php_appsec = None

        libddwaf_version = self.image.env.get("SYSTEM_TESTS_LIBDDWAF_VERSION", None)

        if not libddwaf_version:
            self.libddwaf_version = None
        else:
            self.libddwaf_version = Version(libddwaf_version, "libddwaf")

        appsec_rules_version = self.image.env.get("SYSTEM_TESTS_APPSEC_EVENT_RULES_VERSION", "0.0.0")
        self.appsec_rules_version = Version(appsec_rules_version, "appsec_rules")

        # Basic env set for all scenarios
        self.environment["DD_TELEMETRY_HEARTBEAT_INTERVAL"] = self.telemetry_heartbeat_interval

        if appsec_enabled:
            self.environment["DD_APPSEC_ENABLED"] = "true"

        if self.library in ("cpp", "dotnet", "java", "python"):
            self.environment["DD_TRACE_HEADER_TAGS"] = "user-agent:http.request.headers.user-agent"
        elif self.library in ("golang", "nodejs", "php", "ruby"):
            self.environment["DD_TRACE_HEADER_TAGS"] = "user-agent"
        else:
            self.environment["DD_TRACE_HEADER_TAGS"] = ""

        if len(additional_trace_header_tags) != 0:
            self.environment["DD_TRACE_HEADER_TAGS"] += ",".join(additional_trace_header_tags)

        if tracer_sampling_rate:
            self.environment["DD_TRACE_SAMPLE_RATE"] = str(tracer_sampling_rate)

        if appsec_rules:
            self.environment["DD_APPSEC_RULES"] = str(appsec_rules)
            self.appsec_rules_file = str(appsec_rules)
        else:
            self.appsec_rules_file = self.image.env.get("DD_APPSEC_RULES", None)

        if use_proxy:
            # set the tracer to send data to runner (it will forward them to the agent)
            self.environment["DD_AGENT_HOST"] = "proxy"
            self.environment["DD_TRACE_AGENT_PORT"] = 8126
        else:
            self.environment["DD_AGENT_HOST"] = "agent"
            self.environment["DD_TRACE_AGENT_PORT"] = 8127

    @property
    def library(self):
        return LibraryVersion(
            self.image.env.get("SYSTEM_TESTS_LIBRARY", None), self.image.env.get("SYSTEM_TESTS_LIBRARY_VERSION", None),
        )

    @property
    def uds_socket(self):
        return self.image.env.get("DD_APM_RECEIVER_SOCKET", None)

    @property
    def uds_mode(self):
        return self.uds_socket is not None

    @property
    def telemetry_heartbeat_interval(self):
        return 2


class PostgresContainer(TestedContainer):
    def __init__(self, host_log_folder) -> None:
        super().__init__(
            image_name="postgres:latest",
            name="postgres",
            host_log_folder=host_log_folder,
            user="postgres",
            environment={"POSTGRES_PASSWORD": "password", "PGPORT": "5433"},
            volumes={
                "./utils/build/docker/postgres-init-db.sh": {
                    "bind": "/docker-entrypoint-initdb.d/init_db.sh",
                    "mode": "ro",
                }
            },
        )


class MongoContainer(TestedContainer):
    def __init__(self, host_log_folder) -> None:
        super().__init__(
            image_name="mongo:latest", name="mongodb", host_log_folder=host_log_folder, allow_old_container=True,
        )


class KafkaContainer(TestedContainer):
    def __init__(self, host_log_folder) -> None:
        super().__init__(
            image_name="bitnami/kafka:3.1",
            name="kafka",
            host_log_folder=host_log_folder,
            environment={
                "KAFKA_LISTENERS": "PLAINTEXT://:9092",
                "KAFKA_ADVERTISED_LISTENERS": "PLAINTEXT://kafka:9092",
                "ALLOW_PLAINTEXT_LISTENER": "yes",
                "KAFKA_ADVERTISED_HOST_NAME": "kafka",
                "KAFKA_ADVERTISED_PORT": "9092",
                "KAFKA_PORT": "9092",
                "KAFKA_BROKER_ID": "1",
                "KAFKA_ZOOKEEPER_CONNECT": "zookeeper:2181",
            },
            allow_old_container=True,
        )


class ZooKeeperContainer(TestedContainer):
    def __init__(self, host_log_folder) -> None:
        super().__init__(
            image_name="bitnami/zookeeper:latest",
            name="zookeeper",
            host_log_folder=host_log_folder,
            environment={"ALLOW_ANONYMOUS_LOGIN": "yes",},
            allow_old_container=True,
        )


class CassandraContainer(TestedContainer):
    def __init__(self, host_log_folder) -> None:
        super().__init__(
            image_name="cassandra:latest",
            name="cassandra_db",
            host_log_folder=host_log_folder,
            allow_old_container=True,
        )


class RabbitMqContainer(TestedContainer):
    def __init__(self, host_log_folder) -> None:
        super().__init__(
            image_name="rabbitmq:3-management-alpine",
            name="rabbitmq",
            host_log_folder=host_log_folder,
            allow_old_container=True,
        )


class MySqlContainer(TestedContainer):
    def __init__(self, host_log_folder) -> None:
        super().__init__(
            image_name="mysql/mysql-server:latest",
            name="mysqldb",
            environment={
                "MYSQL_DATABASE": "world",
                "MYSQL_USER": "mysqldb",
                "MYSQL_ROOT_PASSWORD": "mysqldb",
                "MYSQL_PASSWORD": "mysqldb",
            },
            allow_old_container=True,
            host_log_folder=host_log_folder,
            healthcheck={"test": "/healthcheck.sh", "retries": 60},
        )


class OpenTelemetryCollectorContainer(TestedContainer):
    def __init__(self, host_log_folder) -> None:
        super().__init__(
            image_name="otel/opentelemetry-collector-contrib:latest",
            name="collector",
            command="--config=/etc/otelcol-config.yml",
            environment={
                "DD_API_KEY": os.environ.get("DD_API_KEY_3"),
                "DD_SITE": os.environ.get("DD_SITE", "datad0g.com"),
            },
            volumes={"./utils/build/docker/otelcol-config.yaml": {"bind": "/etc/otelcol-config.yml", "mode": "ro",}},
            host_log_folder=host_log_folder,
            # healthcheck={"test": "curl --fail http://localhost:13133", "retries": 60},
            ports={"13133/tcp": ("0.0.0.0", 13133)},
        )
