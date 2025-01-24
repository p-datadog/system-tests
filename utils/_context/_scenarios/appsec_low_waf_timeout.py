from .core import ScenarioGroup
from .endtoend import EndToEndScenario


class AppsecLowWafTimeout(EndToEndScenario):
    def __init__(self, name):
        super().__init__(
            name,
            doc="Appsec with a very low WAF timeout",
            scenario_groups=[ScenarioGroup.APPSEC],
        )

    def configure(self, config):
        super().configure(config)
        library = self.weblog_container.image.labels["system-tests-library"]
        # python lib use milliseconds for DD_APPSEC_WAF_TIMEOUT
        # and other libs use microseconds
        # see https://datadoghq.atlassian.net/wiki/spaces/SAAL/pages/2355333252/Environment+Variables
        self.weblog_container.environment["DD_APPSEC_WAF_TIMEOUT"] = "0.001" if library == "python" else "1"
