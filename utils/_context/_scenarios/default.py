from .core import ScenarioGroup
from .endtoend import EndToEndScenario


# When Security Controls configuration is set, tracers must instrument all the designated methods in the
# configuration as security controls.
# RFC(https://docs.google.com/document/d/1j1hp87-2wJnXUGADZxzLnvKJmaF_Gd6ZR1hPS3LVguQ/edit?pli=1&tab=t.0)

_iast_security_controls_map = {
    "cpp": "TODO",
    "dotnet": "TODO",
    "golang": "TODO",
    "java": (
        "SANITIZER:COMMAND_INJECTION:com.datadoghq.system_tests.iast.utils.SecurityControlUtil:sanitize;"
        "SANITIZER:*:com.datadoghq.system_tests.iast.utils.SecurityControlUtil:sanitizeForAllVulns;"
        "SANITIZER:*:com.datadoghq.system_tests.iast.utils.SecurityControlUtil:overloadedSanitize:java.lang.String;"
        "INPUT_VALIDATOR:COMMAND_INJECTION:com.datadoghq.system_tests.iast.utils.SecurityControlUtil:validate;"
        "INPUT_VALIDATOR:*:com.datadoghq.system_tests.iast.utils.SecurityControlUtil:validateForAllVulns;"
        "INPUT_VALIDATOR:*:com.datadoghq.system_tests.iast.utils.SecurityControlUtil:"
        "overloadedValidation:java.lang.Object,java.lang.String,java.lang.String:1,2"
    ),
    "nodejs": "TODO",
    "php": "TODO",
    "python": "TODO",
    "ruby": "TODO",
}


class DefaultScenario(EndToEndScenario):
    def __init__(self, name: str):
        super().__init__(
            name,
            weblog_env={
                "DD_DBM_PROPAGATION_MODE": "service",
                "DD_TRACE_STATS_COMPUTATION_ENABLED": "1",
                "DD_TRACE_FEATURES": "discovery",
                "DD_TRACE_COMPUTE_STATS": "true",
                "SOME_SECRET_ENV": "leaked-env-var",  # used for test that env var are not leaked
            },
            agent_env={"SOME_SECRET_ENV": "leaked-env-var"},
            include_postgres_db=True,
            scenario_groups=[ScenarioGroup.ESSENTIALS],
            doc="Default scenario, spawn tracer, the Postgres databases and agent, and run most of exisiting tests",
        )

    def configure(self, config):
        super().configure(config)
        library = self.weblog_container.image.labels["system-tests-library"]
        value = _iast_security_controls_map[library]
        self.weblog_container.environment["DD_IAST_SECURITY_CONTROLS_CONFIGURATION"] = value
