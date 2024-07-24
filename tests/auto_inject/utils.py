import os
import pytest
import paramiko
from utils.tools import logger
from utils.onboarding.weblog_interface import make_get_request, warmup_weblog, make_internal_get_request
from utils.onboarding.backend_interface import wait_backend_trace_id
from utils.onboarding.wait_for_tcp_port import wait_for_port
from utils.virtual_machine.vm_logger import vm_logger
from utils import context


class AutoInjectBaseTest:
    def _test_install(self, virtual_machine, profile: bool = False):
        """ We can easily install agent and lib injection software from agent installation script. Given a  sample application we can enable tracing using local environment variables.
            After starting application we can see application HTTP requests traces in the backend.
            Using the agent installation script we can install different versions of the software (release or beta) in different OS."""
        vm_ip = virtual_machine.ssh_config.hostname
        vm_port = virtual_machine.deffault_open_port
        vm_name = virtual_machine.name
        request_uuid = None
        if virtual_machine.krunvm_config is not None and virtual_machine.krunvm_config.stdin is not None:
            logger.info(
                f"We are testing on krunvm. The request to the weblog will be done using the stdin (inside the microvm)"
            )
            request_uuid = make_internal_get_request(virtual_machine.krunvm_config.stdin, vm_port)
        else:
            logger.info(f"Waiting for weblog available [{vm_ip}:{vm_port}]")
            wait_for_port(vm_port, vm_ip, 80.0)
            logger.info(f"[{vm_ip}]: Weblog app is ready!")
            warmup_weblog(f"http://{vm_ip}:{vm_port}/")
            logger.info(f"Making a request to weblog [{vm_ip}:{vm_port}]")
            request_uuid = make_get_request(f"http://{vm_ip}:{vm_port}/")

        logger.info(f"Http request done with uuid: [{request_uuid}] for ip [{vm_ip}]")
        wait_backend_trace_id(request_uuid, 120.0, profile=profile)

    def execute_command(self, virtual_machine, command):
        # Env for the command
        prefix_env = ""
        for key, value in virtual_machine.get_command_environment().items():
            prefix_env += f"export {key}={value} \n"

        command_with_env = f"{prefix_env} {command}"

        with virtual_machine.ssh_config.get_ssh_connection() as ssh:
            try:
                _, stdout, stderr = ssh.exec_command(command_with_env, timeout=120)
                stdout.channel.set_combine_stderr(True)
            except paramiko.buffered_pipe.PipeTimeout:
                if not stdout.channel.eof_received:
                    stdout.channel.close()

            # Read the output line by line
            command_output = ""
            for line in stdout.readlines():
                if not line.startswith("export"):
                    command_output += line
            header = "*****************************************************************"
            vm_logger(context.scenario.name, virtual_machine.name).info(
                f"{header} \n  - COMMAND:  \n {header} \n {command} \n\n {header} \n COMMAND OUTPUT \n\n {header} \n {command_output}"
            )

    def _test_uninstall_commands(
        self, virtual_machine, stop_weblog_command, start_weblog_command, uninstall_command, install_command
    ):
        """ We can unistall the auto injection software. We can start the app again
        The weblog app should work but no sending traces to the backend.
        We can reinstall the auto inject software. The weblog app should be instrumented
        and reporting traces to the backend."""
        logger.info(f"Launching _test_uninstall for : [{virtual_machine.name}]")

        vm_ip = virtual_machine.ssh_config.hostname
        vm_port = virtual_machine.deffault_open_port
        weblog_url = f"http://{vm_ip}:{vm_port}/"

        # Kill the app before the uninstallation
        self.execute_command(virtual_machine, stop_weblog_command)
        # Uninstall the auto inject
        self.execute_command(virtual_machine, uninstall_command)
        # Start the app again
        self.execute_command(virtual_machine, start_weblog_command)

        wait_for_port(vm_port, vm_ip, 40.0)
        warmup_weblog(weblog_url)
        request_uuid = make_get_request(weblog_url)
        logger.info(f"Http request done with uuid: [{request_uuid}] for ip [{virtual_machine.name}]")
        try:
            wait_backend_trace_id(request_uuid, 10.0)
            raise AssertionError("The weblog application is instrumented after uninstall DD software")
        except TimeoutError:
            # OK there are no traces, the weblog app is not instrumented
            pass
        # Kill the app before restore the installation
        self.execute_command(virtual_machine, stop_weblog_command)
        # reinstall the auto inject
        self.execute_command(virtual_machine, install_command)
        # Start the app again
        self.execute_command(virtual_machine, start_weblog_command)
        # The app should be instrumented and reporting traces to the backend
        self._test_install(virtual_machine)
        logger.info(f"Success _test_uninstall for : [{virtual_machine.name}]")

    def _test_uninstall(self, virtual_machine):

        if context.scenario.weblog_variant == "test-app-{}".format(context.scenario.library.library):
            # Host
            stop_weblog_command = "sudo systemctl kill -s SIGKILL test-app.service"
            start_weblog_command = "sudo systemctl start test-app.service"
            if context.scenario.library.library in ["ruby", "python", "dotnet"]:
                start_weblog_command = virtual_machine._vm_provision.weblog_installation.remote_command
        else:
            # Container
            stop_weblog_command = "sudo -E docker-compose -f docker-compose.yml down"
            start_weblog_command = virtual_machine._vm_provision.weblog_installation.remote_command

        install_command = "sudo datadog-installer apm instrument"
        uninstall_command = "sudo datadog-installer apm uninstrument"
        self._test_uninstall_commands(
            virtual_machine, stop_weblog_command, start_weblog_command, uninstall_command, install_command
        )

    @pytest.fixture(autouse=True)
    def do_before_test(self, virtual_machine):
        if virtual_machine:
            current_test = os.environ.get("PYTEST_CURRENT_TEST").split(":")[-1].split(" ")[0]
            start = current_test.find("[")
            if start != -1:
                current_test = current_test[: start + 1]
            header = "----------------------------------------------------------------------"
            vm_logger(context.scenario.name, virtual_machine.name).info(
                f"{header} \n {header}  \n  Launching the test {current_test} for VM: {virtual_machine.name}  \n {header} \n {header}"
            )
        yield
