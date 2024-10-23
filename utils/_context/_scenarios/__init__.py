import json

from utils._context.header_tag_vars import VALID_CONFIGS, INVALID_CONFIGS
from utils.proxy.ports import ProxyPorts
from utils.tools import update_environ_with_local_env

from .core import Scenario, ScenarioGroup
from .default import DefaultScenario
from .endtoend import DockerScenario, EndToEndScenario
from .integrations import CrossedTracingLibraryScenario, IntegrationsScenario, AWSIntegrationsScenario
from .open_telemetry import OpenTelemetryScenario
from .parametric import ParametricScenario
from .performance import PerformanceScenario
from .profiling import ProfilingScenario
from .test_the_test import TestTheTestScenario
from .auto_injection import InstallerAutoInjectionScenario
from .k8s_lib_injection import WeblogInjectionScenario, K8sScenario, K8sSparkScenario, K8sManualInstrumentationScenario
from .docker_ssi import DockerSSIScenario
from .external_processing import ExternalProcessingScenario
from .ipv6 import IPV6Scenario
from .appsec_low_waf_timeout import AppsecLowWafTimeout

update_environ_with_local_env()


class _Scenarios:
    todo = Scenario("TODO", doc="scenario that skips tests not yet executed", github_workflow=None)
    test_the_test = TestTheTestScenario("TEST_THE_TEST", doc="Small scenario that check system-tests internals")
    mock_the_test = TestTheTestScenario("MOCK_THE_TEST", doc="Mock scenario that check system-tests internals")

    default = DefaultScenario("DEFAULT")

    # performance scenario just spawn an agent and a weblog, and spies the CPU and mem usage
    performances = PerformanceScenario(
        "PERFORMANCES", doc="A not very used scenario : its aim is to measure CPU and MEM usage across a basic run"
    )
    integrations = IntegrationsScenario()
    integrations_aws = AWSIntegrationsScenario()
    crossed_tracing_libraries = CrossedTracingLibraryScenario()

    otel_integrations = OpenTelemetryScenario(
        "OTEL_INTEGRATIONS",
        weblog_env={
            "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
            "OTEL_EXPORTER_OTLP_ENDPOINT": f"http://proxy:{ProxyPorts.open_telemetry_weblog}",
            "OTEL_EXPORTER_OTLP_TRACES_HEADERS": "dd-protocol=otlp,dd-otlp-path=agent",
            "OTEL_INTEGRATIONS_TEST": True,
        },
        include_intake=False,
        include_collector=False,
        include_postgres_db=True,
        include_cassandra_db=True,
        include_mongo_db=True,
        include_kafka=True,
        include_rabbitmq=True,
        include_mysql_db=True,
        include_sqlserver=True,
        doc=(
            "We use the open telemetry library to automatically instrument the weblogs instead of using the DD library."
            "This scenario represents this case in the integration with different external systems, for example the "
            "interaction with sql database."
        ),
    )

    profiling = ProfilingScenario("PROFILING")

    appsec_no_stats = EndToEndScenario(
        name="APPSEC_NO_STATS",
        doc=(
            "End to end testing with default values. Default scenario has DD_TRACE_COMPUTE_STATS=true."
            "This scenario let that env to use its default"
        ),
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    sampling = EndToEndScenario(
        "SAMPLING",
        tracer_sampling_rate=0.5,
        weblog_env={"DD_TRACE_RATE_LIMIT": "10000000"},
        doc="Test sampling mechanism. Not included in default scenario because it's a little bit too flaky",
        scenario_groups=[ScenarioGroup.SAMPLING],
    )

    trace_propagation_style_w3c = EndToEndScenario(
        "TRACE_PROPAGATION_STYLE_W3C",
        weblog_env={
            "DD_TRACE_PROPAGATION_STYLE_INJECT": "tracecontext",
            "DD_TRACE_PROPAGATION_STYLE_EXTRACT": "tracecontext",
        },
        doc="Test W3C trace style",
    )

    # Telemetry scenarios
    telemetry_dependency_loaded_test_for_dependency_collection_disabled = EndToEndScenario(
        "TELEMETRY_DEPENDENCY_LOADED_TEST_FOR_DEPENDENCY_COLLECTION_DISABLED",
        weblog_env={"DD_TELEMETRY_DEPENDENCY_COLLECTION_ENABLED": "false"},
        doc="Test DD_TELEMETRY_DEPENDENCY_COLLECTION_ENABLED=false effect on tracers",
        scenario_groups=[ScenarioGroup.TELEMETRY],
    )

    telemetry_app_started_products_disabled = EndToEndScenario(
        "TELEMETRY_APP_STARTED_PRODUCTS_DISABLED",
        weblog_env={
            "DD_APPSEC_ENABLED": "false",
            "DD_PROFILING_ENABLED": "false",
            "DD_DYNAMIC_INSTRUMENTATION_ENABLED": "false",
        },
        appsec_enabled=False,
        doc="Disable all tracers products",
        scenario_groups=[ScenarioGroup.TELEMETRY],
    )

    telemetry_log_generation_disabled = EndToEndScenario(
        "TELEMETRY_LOG_GENERATION_DISABLED",
        weblog_env={"DD_TELEMETRY_LOG_COLLECTION_ENABLED": "false"},
        doc="Test env var `DD_TELEMETRY_LOG_COLLECTION_ENABLED=false`",
        scenario_groups=[ScenarioGroup.TELEMETRY],
    )
    telemetry_metric_generation_disabled = EndToEndScenario(
        "TELEMETRY_METRIC_GENERATION_DISABLED",
        weblog_env={"DD_TELEMETRY_METRICS_ENABLED": "false"},
        doc="Test env var `DD_TELEMETRY_METRICS_ENABLED=false`",
        scenario_groups=[ScenarioGroup.TELEMETRY],
    )
    telemetry_metric_generation_enabled = EndToEndScenario(
        "TELEMETRY_METRIC_GENERATION_ENABLED",
        weblog_env={"DD_TELEMETRY_METRICS_ENABLED": "true"},
        doc="Test env var `DD_TELEMETRY_METRICS_ENABLED=true`",
        scenario_groups=[ScenarioGroup.TELEMETRY],
    )

    # ASM scenarios
    appsec_missing_rules = EndToEndScenario(
        "APPSEC_MISSING_RULES",
        weblog_env={"DD_APPSEC_RULES": "/donotexists"},
        doc="Test missing appsec rules file",
        scenario_groups=[ScenarioGroup.APPSEC],
    )
    appsec_corrupted_rules = EndToEndScenario(
        "APPSEC_CORRUPTED_RULES",
        weblog_env={"DD_APPSEC_RULES": "/appsec_corrupted_rules.yml"},
        weblog_volumes={
            "./tests/appsec/appsec_corrupted_rules.json": {"bind": "/appsec_corrupted_rules.json", "mode": "ro"}
        },
        doc="Test corrupted appsec rules file",
        scenario_groups=[ScenarioGroup.APPSEC],
    )
    appsec_custom_rules = EndToEndScenario(
        "APPSEC_CUSTOM_RULES",
        weblog_env={"DD_APPSEC_RULES": "/appsec_custom_rules.json"},
        weblog_volumes={"./tests/appsec/custom_rules.json": {"bind": "/appsec_custom_rules.json", "mode": "ro"}},
        doc="Test custom appsec rules file",
        scenario_groups=[ScenarioGroup.APPSEC],
    )
    appsec_blocking = EndToEndScenario(
        "APPSEC_BLOCKING",
        weblog_env={"DD_APPSEC_RULES": "/appsec_blocking_rule.json"},
        weblog_volumes={"./tests/appsec/blocking_rule.json": {"bind": "/appsec_blocking_rule.json", "mode": "ro"}},
        doc="Misc tests for appsec blocking",
        scenario_groups=[ScenarioGroup.APPSEC, ScenarioGroup.ESSENTIALS],
    )
    # This GraphQL scenario can be used for any GraphQL testing, not just AppSec
    graphql_appsec = EndToEndScenario(
        "GRAPHQL_APPSEC",
        weblog_env={
            "DD_APPSEC_RULES": "/appsec_blocking_rule.json",
            "DD_TRACE_GRAPHQL_ERROR_EXTENSIONS": "int,float,str,bool,other",
        },
        weblog_volumes={"./tests/appsec/blocking_rule.json": {"bind": "/appsec_blocking_rule.json", "mode": "ro"}},
        doc="AppSec tests for GraphQL integrations",
        github_workflow="graphql",
        scenario_groups=[ScenarioGroup.APPSEC],
    )
    appsec_rules_monitoring_with_errors = EndToEndScenario(
        "APPSEC_RULES_MONITORING_WITH_ERRORS",
        weblog_env={"DD_APPSEC_RULES": "/appsec_custom_rules_with_errors.json"},
        weblog_volumes={
            "./tests/appsec/custom_rules_with_errors.json": {
                "bind": "/appsec_custom_rules_with_errors.json",
                "mode": "ro",
            }
        },
        doc="Appsec rule file with some errors",
        scenario_groups=[ScenarioGroup.APPSEC],
    )
    everything_disabled = EndToEndScenario(
        "EVERYTHING_DISABLED",
        weblog_env={"DD_APPSEC_ENABLED": "false", "DD_DBM_PROPAGATION_MODE": "disabled"},
        appsec_enabled=False,
        include_postgres_db=True,
        doc="Disable appsec and test DBM setting integration outcome when disabled",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_low_waf_timeout = AppsecLowWafTimeout("APPSEC_LOW_WAF_TIMEOUT")

    appsec_custom_obfuscation = EndToEndScenario(
        "APPSEC_CUSTOM_OBFUSCATION",
        weblog_env={
            "DD_APPSEC_OBFUSCATION_PARAMETER_KEY_REGEXP": "hide-key",
            "DD_APPSEC_OBFUSCATION_PARAMETER_VALUE_REGEXP": ".*hide_value",
        },
        doc="Test custom appsec obfuscation parameters",
        scenario_groups=[ScenarioGroup.APPSEC],
    )
    appsec_rate_limiter = EndToEndScenario(
        "APPSEC_RATE_LIMITER",
        weblog_env={"DD_APPSEC_TRACE_RATE_LIMIT": "1", "RAILS_MAX_THREADS": "1"},
        doc="Tests with a low rate trace limit for Appsec",
        scenario_groups=[ScenarioGroup.APPSEC],
    )
    appsec_waf_telemetry = EndToEndScenario(
        "APPSEC_WAF_TELEMETRY",
        weblog_env={
            "DD_INSTRUMENTATION_TELEMETRY_ENABLED": "true",
            "DD_TELEMETRY_METRICS_ENABLED": "true",
            "DD_TELEMETRY_METRICS_INTERVAL_SECONDS": "2.0",
        },
        doc="Enable Telemetry feature for WAF",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_blocking_full_denylist = EndToEndScenario(
        "APPSEC_BLOCKING_FULL_DENYLIST",
        rc_api_enabled=True,
        weblog_env={"DD_APPSEC_RULES": None},
        doc="""
            The spec says that if  DD_APPSEC_RULES is defined, then rules won't be loaded from remote config.
            In this scenario, we use remote config. By the spec, whem remote config is available, rules file
            embedded in the tracer will never be used (it will be the file defined in DD_APPSEC_RULES, or the
            data coming from remote config). So, we set  DD_APPSEC_RULES to None to enable loading rules from
            remote config. And it's okay not testing custom rule set for dev mode, as in this scenario, rules
            are always coming from remote config.
        """,
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_request_blocking = EndToEndScenario(
        "APPSEC_REQUEST_BLOCKING",
        rc_api_enabled=True,
        weblog_env={"DD_APPSEC_RULES": None},
        doc="",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_runtime_activation = EndToEndScenario(
        "APPSEC_RUNTIME_ACTIVATION",
        rc_api_enabled=True,
        appsec_enabled=False,
        iast_enabled=False,
        weblog_env={"DD_APPSEC_WAF_TIMEOUT": "10000000", "DD_APPSEC_TRACE_RATE_LIMIT": "10000"},  # 10 seconds
        doc="",
        scenario_groups=[ScenarioGroup.APPSEC, ScenarioGroup.APPSEC_RASP],
    )

    appsec_api_security = EndToEndScenario(
        "APPSEC_API_SECURITY",
        appsec_enabled=True,
        weblog_env={
            "DD_EXPERIMENTAL_API_SECURITY_ENABLED": "true",
            "DD_API_SECURITY_ENABLED": "true",
            "DD_API_SECURITY_REQUEST_SAMPLE_RATE": "1.0",
            "DD_API_SECURITY_SAMPLE_DELAY": "0.0",
            "DD_API_SECURITY_MAX_CONCURRENT_REQUESTS": "50",
        },
        doc="""
        Scenario for API Security feature, testing schema types sent into span tags if
        DD_API_SECURITY_ENABLED is set to true.
        """,
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_api_security_rc = EndToEndScenario(
        "APPSEC_API_SECURITY_RC",
        weblog_env={"DD_EXPERIMENTAL_API_SECURITY_ENABLED": "true", "DD_API_SECURITY_SAMPLE_DELAY": "0.0"},
        rc_api_enabled=True,
        doc="""
            Scenario to test API Security Remote config
        """,
        scenario_groups=[ScenarioGroup.APPSEC, ScenarioGroup.ESSENTIALS],
    )

    appsec_api_security_no_response_body = EndToEndScenario(
        "APPSEC_API_SECURITY_NO_RESPONSE_BODY",
        appsec_enabled=True,
        weblog_env={
            "DD_EXPERIMENTAL_API_SECURITY_ENABLED": "true",
            "DD_API_SECURITY_ENABLED": "true",
            "DD_API_SECURITY_REQUEST_SAMPLE_RATE": "1.0",
            "DD_API_SECURITY_MAX_CONCURRENT_REQUESTS": "50",
            "DD_API_SECURITY_PARSE_RESPONSE_BODY": "false",
        },
        doc="""
        Scenario for API Security feature, testing schema types sent into span tags if
        DD_API_SECURITY_ENABLED is set to true.
        """,
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_api_security_with_sampling = EndToEndScenario(
        "APPSEC_API_SECURITY_WITH_SAMPLING",
        appsec_enabled=True,
        weblog_env={
            "DD_EXPERIMENTAL_API_SECURITY_ENABLED": "true",
            "DD_API_SECURITY_ENABLED": "true",
            "DD_API_SECURITY_SAMPLE_DELAY": "3",
        },
        doc="""
        Scenario for API Security feature, testing api security sampling rate.
        """,
        scenario_groups=[ScenarioGroup.APPSEC, ScenarioGroup.ESSENTIALS],
    )

    appsec_auto_events_extended = EndToEndScenario(
        "APPSEC_AUTO_EVENTS_EXTENDED",
        weblog_env={
            "DD_APPSEC_ENABLED": "true",
            "DD_APPSEC_AUTOMATED_USER_EVENTS_TRACKING": "extended",
            "DD_APPSEC_AUTO_USER_INSTRUMENTATION_MODE": "anonymization",
        },
        appsec_enabled=True,
        doc="Scenario for checking extended mode in automatic user events",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_auto_events_rc = EndToEndScenario(
        "APPSEC_AUTO_EVENTS_RC",
        weblog_env={"DD_APPSEC_ENABLED": "true", "DD_REMOTE_CONFIG_POLL_INTERVAL_SECONDS": 0.5},
        rc_api_enabled=True,
        doc="""
            Scenario to test User ID collection config change via Remote config
        """,
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_standalone = EndToEndScenario(
        "APPSEC_STANDALONE",
        weblog_env={
            "DD_APPSEC_ENABLED": "true",
            "DD_EXPERIMENTAL_APPSEC_STANDALONE_ENABLED": "true",
            "DD_IAST_ENABLED": "false",
        },
        doc="Appsec standalone mode (APM opt out)",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_standalone_v2 = EndToEndScenario(
        "APPSEC_STANDALONE_V2",
        weblog_env={
            "DD_APPSEC_ENABLED": "true",
            "DD_APM_TRACING_ENABLED": "false",
            "DD_IAST_ENABLED": "false",
        },
        doc="Appsec standalone mode (APM opt out) V2",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    iast_standalone = EndToEndScenario(
        "IAST_STANDALONE",
        weblog_env={
            "DD_APPSEC_ENABLED": "false",
            "DD_EXPERIMENTAL_APPSEC_STANDALONE_ENABLED": "true",
            "DD_IAST_ENABLED": "true",
            "DD_IAST_DETECTION_MODE": "FULL",
            "DD_IAST_DEDUPLICATION_ENABLED": "false",
            "DD_IAST_REQUEST_SAMPLING": "100",
        },
        doc="Source code vulnerability standalone mode (APM opt out)",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    iast_standalone_v2 = EndToEndScenario(
        "IAST_STANDALONE_V2",
        weblog_env={
            "DD_APPSEC_ENABLED": "false",
            "DD_APM_TRACING_ENABLED": "false",
            "DD_IAST_ENABLED": "true",
            "DD_IAST_DETECTION_MODE": "FULL",
            "DD_IAST_DEDUPLICATION_ENABLED": "false",
            "DD_IAST_REQUEST_SAMPLING": "100",
        },
        doc="Source code vulnerability standalone mode (APM opt out)",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    sca_standalone = EndToEndScenario(
        "SCA_STANDALONE",
        weblog_env={
            "DD_APPSEC_ENABLED": "false",
            "DD_APPSEC_SCA_ENABLED": "true",
            "DD_EXPERIMENTAL_APPSEC_STANDALONE_ENABLED": "true",
            "DD_IAST_ENABLED": "false",
            "DD_TELEMETRY_DEPENDENCY_RESOLUTION_PERIOD_MILLIS": "1",
        },
        doc="SCA standalone mode (APM opt out)",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    sca_standalone_v2 = EndToEndScenario(
        "SCA_STANDALONE_V2",
        weblog_env={
            "DD_APPSEC_ENABLED": "false",
            "DD_APPSEC_SCA_ENABLED": "true",
            "DD_APM_TRACING_ENABLED": "false",
            "DD_IAST_ENABLED": "false",
            "DD_TELEMETRY_DEPENDENCY_RESOLUTION_PERIOD_MILLIS": "1",
        },
        doc="SCA standalone mode (APM opt out)",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    iast_deduplication = EndToEndScenario(
        "IAST_DEDUPLICATION",
        weblog_env={
            "DD_IAST_ENABLED": "true",
            "DD_IAST_DEDUPLICATION_ENABLED": "true",
            "DD_IAST_REQUEST_SAMPLING": "100",
        },
        doc="Iast scenario with deduplication enabled",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    appsec_meta_struct_disabled = EndToEndScenario(
        "APPSEC_META_STRUCT_DISABLED",
        weblog_env={"DD_APPSEC_ENABLED": "true", "DD_IAST_ENABLED": "true"},
        meta_structs_disabled=True,
        doc="Appsec tests with support for meta struct disabled in the agent configuration",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    remote_config_mocked_backend_asm_features = EndToEndScenario(
        "REMOTE_CONFIG_MOCKED_BACKEND_ASM_FEATURES",
        rc_api_enabled=True,
        appsec_enabled=False,
        weblog_env={"DD_REMOTE_CONFIGURATION_ENABLED": "true"},
        doc="",
        scenario_groups=[ScenarioGroup.APPSEC, ScenarioGroup.REMOTE_CONFIG, ScenarioGroup.ESSENTIALS],
    )

    remote_config_mocked_backend_live_debugging = EndToEndScenario(
        "REMOTE_CONFIG_MOCKED_BACKEND_LIVE_DEBUGGING",
        rc_api_enabled=True,
        weblog_env={
            "DD_DYNAMIC_INSTRUMENTATION_ENABLED": "1",
            "DD_DEBUGGER_ENABLED": "1",
            "DD_REMOTE_CONFIG_ENABLED": "true",
            "DD_INTERNAL_RCM_POLL_INTERVAL": "1000",
        },
        doc="",
        scenario_groups=[ScenarioGroup.REMOTE_CONFIG, ScenarioGroup.ESSENTIALS],
    )

    remote_config_mocked_backend_asm_dd = EndToEndScenario(
        "REMOTE_CONFIG_MOCKED_BACKEND_ASM_DD",
        rc_api_enabled=True,
        weblog_env={"DD_APPSEC_RULES": None},
        doc="""
            The spec says that if DD_APPSEC_RULES is defined, then rules won't be loaded from remote config.
            In this scenario, we use remote config. By the spec, whem remote config is available, rules file
            embedded in the tracer will never be used (it will be the file defined in DD_APPSEC_RULES, or the
            data coming from remote config). So, we set  DD_APPSEC_RULES to None to enable loading rules from
            remote config. And it's okay not testing custom rule set for dev mode, as in this scenario, rules
            are always coming from remote config.
        """,
        scenario_groups=[
            ScenarioGroup.APPSEC,
            ScenarioGroup.APPSEC_RASP,
            ScenarioGroup.REMOTE_CONFIG,
            ScenarioGroup.ESSENTIALS,
        ],
    )

    remote_config_mocked_backend_asm_features_nocache = EndToEndScenario(
        "REMOTE_CONFIG_MOCKED_BACKEND_ASM_FEATURES_NOCACHE",
        rc_api_enabled=True,
        weblog_env={"DD_APPSEC_ENABLED": "false", "DD_REMOTE_CONFIGURATION_ENABLED": "true"},
        doc="",
        scenario_groups=[ScenarioGroup.APPSEC, ScenarioGroup.REMOTE_CONFIG],
    )

    remote_config_mocked_backend_asm_dd_nocache = EndToEndScenario(
        "REMOTE_CONFIG_MOCKED_BACKEND_ASM_DD_NOCACHE",
        rc_api_enabled=True,
        doc="",
        scenario_groups=[ScenarioGroup.APPSEC, ScenarioGroup.REMOTE_CONFIG],
    )

    # APM tracing end-to-end scenarios

    apm_tracing_e2e = EndToEndScenario("APM_TRACING_E2E", backend_interface_timeout=5, doc="")
    apm_tracing_e2e_otel = EndToEndScenario(
        "APM_TRACING_E2E_OTEL",
        weblog_env={"DD_TRACE_OTEL_ENABLED": "true"},
        backend_interface_timeout=5,
        require_api_key=True,
        doc="",
    )
    apm_tracing_e2e_single_span = EndToEndScenario(
        "APM_TRACING_E2E_SINGLE_SPAN",
        weblog_env={
            "DD_SPAN_SAMPLING_RULES": json.dumps(
                [{"service": "weblog", "name": "*single_span_submitted", "sample_rate": 1.0, "max_per_second": 50}]
            ),
            "DD_TRACE_SAMPLE_RATE": "0",
        },
        backend_interface_timeout=5,
        require_api_key=True,
        doc="",
    )

    otel_tracing_e2e = OpenTelemetryScenario("OTEL_TRACING_E2E", require_api_key=True, doc="")
    otel_metric_e2e = OpenTelemetryScenario("OTEL_METRIC_E2E", require_api_key=True, doc="")
    otel_log_e2e = OpenTelemetryScenario("OTEL_LOG_E2E", require_api_key=True, doc="")

    library_conf_custom_header_tags = EndToEndScenario(
        "LIBRARY_CONF_CUSTOM_HEADER_TAGS",
        additional_trace_header_tags=(VALID_CONFIGS),
        rc_api_enabled=True,
        doc="Scenario with custom headers to be used with DD_TRACE_HEADER_TAGS",
    )
    library_conf_custom_header_tags_invalid = EndToEndScenario(
        "LIBRARY_CONF_CUSTOM_HEADER_TAGS_INVALID",
        additional_trace_header_tags=(INVALID_CONFIGS),
        doc="Scenario with custom headers for DD_TRACE_HEADER_TAGS that libraries should reject",
    )

    tracing_config_empty = EndToEndScenario("TRACING_CONFIG_EMPTY", weblog_env={}, doc="")

    tracing_config_nondefault = EndToEndScenario(
        "TRACING_CONFIG_NONDEFAULT",
        weblog_env={
            "DD_TRACE_HTTP_SERVER_ERROR_STATUSES": "200-201,202",
            "DD_TRACE_OBFUSCATION_QUERY_STRING_REGEXP": r"ssn=\d{3}-\d{2}-\d{4}",
            "DD_TRACE_CLIENT_IP_ENABLED": "true",
            "DD_TRACE_HTTP_CLIENT_ERROR_STATUSES": "200-201,202",
            "DD_SERVICE": "service_test",
            "DD_TRACE_KAFKA_ENABLED": "false",  # most common endpoint and integration (missing for PHP).
            "DD_TRACE_KAFKAJS_ENABLED": "false",  # In Node the integration is kafkajs.
            "DD_TRACE_PDO_ENABLED": "false",  # Use PDO for PHP,
            "DD_TRACE_PROPAGATION_STYLE_EXTRACT": "datadog,tracecontext,b3multi,baggage",
            "DD_TRACE_PROPAGATION_BEHAVIOR_EXTRACT": "restart",
            "DD_LOGS_INJECTION": "true",
        },
        appsec_enabled=False,  # disable ASM to test non asm client ip tagging
        iast_enabled=False,
        include_kafka=True,
        include_postgres_db=True,
        doc="",
        scenario_groups=[ScenarioGroup.TRACING_CONFIG, ScenarioGroup.ESSENTIALS],
    )

    tracing_config_nondefault_2 = EndToEndScenario(
        "TRACING_CONFIG_NONDEFAULT_2",
        weblog_env={
            "DD_TRACE_OBFUSCATION_QUERY_STRING_REGEXP": "",
            "DD_TRACE_KAFKA_ENABLED": "true",
            "DD_TRACE_KAFKAJS_ENABLED": "true",
            "DD_TRACE_PDO_ENABLED": "true",  # Use PDO for PHP
            "DD_TRACE_CLIENT_IP_HEADER": "custom-ip-header",
            "DD_TRACE_CLIENT_IP_ENABLED": "true",
            "DD_TRACE_PROPAGATION_STYLE_EXTRACT": "datadog,tracecontext,b3multi,baggage",
            "DD_TRACE_PROPAGATION_BEHAVIOR_EXTRACT": "ignore",
        },
        include_kafka=True,
        include_postgres_db=True,
        doc="Test tracer configuration when a collection of non-default settings are applied",
        scenario_groups=[ScenarioGroup.TRACING_CONFIG],
    )
    tracing_config_nondefault_3 = EndToEndScenario(
        "TRACING_CONFIG_NONDEFAULT_3",
        weblog_env={
            "DD_TRACE_HTTP_CLIENT_TAG_QUERY_STRING": "false",
            "DD_TRACE_CLIENT_IP_HEADER": "custom-ip-header",
            "DD_TRACE_PROPAGATION_STYLE_EXTRACT": "datadog,tracecontext,b3multi,baggage",
            "DD_TRACE_PROPAGATION_BEHAVIOR_EXTRACT": "restart",
            "DD_TRACE_PROPAGATION_EXTRACT_FIRST": "true",
            "DD_LOGS_INJECTION": "true",
            "DD_TRACE_128_BIT_TRACEID_LOGGING_ENABLED": "false",
        },
        appsec_enabled=False,
        doc="",
        scenario_groups=[ScenarioGroup.TRACING_CONFIG],
    )

    parametric = ParametricScenario("PARAMETRIC", doc="WIP")

    debugger_probes_status = EndToEndScenario(
        "DEBUGGER_PROBES_STATUS",
        rc_api_enabled=True,
        weblog_env={
            "DD_DYNAMIC_INSTRUMENTATION_ENABLED": "1",
            "DD_REMOTE_CONFIG_ENABLED": "true",
            "DD_INTERNAL_RCM_POLL_INTERVAL": "2000",
            "DD_DEBUGGER_DIAGNOSTICS_INTERVAL": "1",
        },
        doc="Test scenario for checking if method probe statuses can be successfully 'RECEIVED' and 'INSTALLED'",
        scenario_groups=[ScenarioGroup.DEBUGGER],
    )

    debugger_probes_snapshot = EndToEndScenario(
        "DEBUGGER_PROBES_SNAPSHOT",
        rc_api_enabled=True,
        weblog_env={
            "DD_DYNAMIC_INSTRUMENTATION_ENABLED": "1",
            "DD_REMOTE_CONFIG_ENABLED": "true",
            "DD_CODE_ORIGIN_FOR_SPANS_ENABLED": "true",
        },
        library_interface_timeout=5,
        doc="Test scenario for checking if debugger successfully generates snapshots for probes",
        scenario_groups=[ScenarioGroup.DEBUGGER],
    )

    debugger_pii_redaction = EndToEndScenario(
        "DEBUGGER_PII_REDACTION",
        rc_api_enabled=True,
        weblog_env={
            'RAILS_LOG_TO_STDOUT':'1',
            "DD_DYNAMIC_INSTRUMENTATION_ENABLED": "1",
            "DD_REMOTE_CONFIG_ENABLED": "true",
            "DD_DYNAMIC_INSTRUMENTATION_REDACTED_TYPES": "weblog.Models.Debugger.CustomPii,com.datadoghq.system_tests.springboot.CustomPii,CustomPii",  # noqa: E501
            "DD_DYNAMIC_INSTRUMENTATION_REDACTED_IDENTIFIERS": "customidentifier1,customidentifier2",
        },
        library_interface_timeout=5,
        doc="Check pii redaction",
        scenario_groups=[ScenarioGroup.DEBUGGER],
    )

    debugger_expression_language = EndToEndScenario(
        "DEBUGGER_EXPRESSION_LANGUAGE",
        rc_api_enabled=True,
        weblog_env={"DD_DYNAMIC_INSTRUMENTATION_ENABLED": "1", "DD_REMOTE_CONFIG_ENABLED": "true"},
        library_interface_timeout=5,
        doc="Check expression language",
        scenario_groups=[ScenarioGroup.DEBUGGER],
    )

    debugger_exception_replay = EndToEndScenario(
        "DEBUGGER_EXCEPTION_REPLAY",
        rc_api_enabled=True,
        weblog_env={
            "DD_DYNAMIC_INSTRUMENTATION_ENABLED": "1",
            "DD_REMOTE_CONFIG_ENABLED": "true",
            "DD_EXCEPTION_DEBUGGING_ENABLED": "true",
            "DD_EXCEPTION_REPLAY_CAPTURE_MAX_FRAMES": "10",
        },
        library_interface_timeout=5,
        doc="Check exception replay",
        scenario_groups=[ScenarioGroup.DEBUGGER],
    )

    debugger_symdb = EndToEndScenario(
        "DEBUGGER_SYMDB",
        rc_api_enabled=True,
        weblog_env={
            "DD_DYNAMIC_INSTRUMENTATION_ENABLED": "1",
            "DD_SYMBOL_DATABASE_UPLOAD_ENABLED": "1",
            "DD_REMOTE_CONFIG_ENABLED": "true",
            "DD_INTERNAL_RCM_POLL_INTERVAL": "2000",
            "DD_DEBUGGER_DIAGNOSTICS_INTERVAL": "1",
        },
        library_interface_timeout=5,
        doc="Test scenario for checking symdb.",
        scenario_groups=[ScenarioGroup.DEBUGGER],
    )

    debugger_inproduct_enablement = EndToEndScenario(
        "DEBUGGER_INPRODUCT_ENABLEMENT",
        rc_api_enabled=True,
        weblog_env={
            "DD_APM_TRACING_ENABLED": "true",
            "DD_REMOTE_CONFIG_ENABLED": "true",
            "DD_INTERNAL_RCM_POLL_INTERVAL": "2000",
        },
        library_interface_timeout=5,
        doc="Test scenario for checking dynamic enablement.",
        scenario_groups=[ScenarioGroup.DEBUGGER],
    )

    fuzzer = DockerScenario("FUZZER", doc="Fake scenario for fuzzing (launch without pytest)", github_workflow=None)

    # Single Step Instrumentation scenarios (HOST and CONTAINER)

    simple_installer_auto_injection = InstallerAutoInjectionScenario(
        "SIMPLE_INSTALLER_AUTO_INJECTION",
        "Onboarding Container Single Step Instrumentation scenario (minimal test scenario)",
        scenario_groups=[ScenarioGroup.ONBOARDING, ScenarioGroup.SIMPLE_ONBOARDING],
        github_workflow="aws_ssi",
    )
    multi_installer_auto_injection = InstallerAutoInjectionScenario(
        "MULTI_INSTALLER_AUTO_INJECTION",
        "Onboarding Container Single Step Instrumentation scenario for multicontainer apps",
        scenario_groups=[ScenarioGroup.ONBOARDING, ScenarioGroup.SIMPLE_ONBOARDING],
        github_workflow="aws_ssi",
    )
    installer_auto_injection = InstallerAutoInjectionScenario(
        "INSTALLER_AUTO_INJECTION",
        doc="Installer auto injection scenario",
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    installer_not_supported_auto_injection = InstallerAutoInjectionScenario(
        "INSTALLER_NOT_SUPPORTED_AUTO_INJECTION",
        "Onboarding host Single Step Instrumentation scenario for not supported languages",
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    chaos_installer_auto_injection = InstallerAutoInjectionScenario(
        "CHAOS_INSTALLER_AUTO_INJECTION",
        doc=(
            "Onboarding Host Single Step Instrumentation scenario. "
            "Machines with previous ld.so.preload entries. Perform chaos testing"
        ),
        vm_provision="auto-inject-ld-preload",
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    simple_auto_injection_profiling = InstallerAutoInjectionScenario(
        "SIMPLE_AUTO_INJECTION_PROFILING",
        "Onboarding Single Step Instrumentation scenario with profiling activated by the app env var",
        app_env={
            "DD_PROFILING_ENABLED": "auto",
            "DD_PROFILING_UPLOAD_PERIOD": "10",
            "DD_INTERNAL_PROFILING_LONG_LIVED_THRESHOLD": "1500",
        },
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )
    host_auto_injection_install_script_profiling = InstallerAutoInjectionScenario(
        "HOST_AUTO_INJECTION_INSTALL_SCRIPT_PROFILING",
        doc=(
            "Onboarding Host Single Step Instrumentation scenario using agent "
            "auto install script with profiling activating by the installation process"
        ),
        vm_provision="host-auto-inject-install-script",
        agent_env={"DD_PROFILING_ENABLED": "auto"},
        app_env={"DD_PROFILING_UPLOAD_PERIOD": "10", "DD_INTERNAL_PROFILING_LONG_LIVED_THRESHOLD": "1500"},
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    container_auto_injection_install_script_profiling = InstallerAutoInjectionScenario(
        "CONTAINER_AUTO_INJECTION_INSTALL_SCRIPT_PROFILING",
        "Onboarding Container Single Step Instrumentation profiling scenario using agent auto install script",
        vm_provision="container-auto-inject-install-script",
        agent_env={"DD_PROFILING_ENABLED": "auto"},
        app_env={"DD_PROFILING_UPLOAD_PERIOD": "10", "DD_INTERNAL_PROFILING_LONG_LIVED_THRESHOLD": "1500"},
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    demo_aws = InstallerAutoInjectionScenario(
        "DEMO_AWS",
        "Demo aws scenario",
        vm_provision="demo",
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    host_auto_injection_install_script = InstallerAutoInjectionScenario(
        "HOST_AUTO_INJECTION_INSTALL_SCRIPT",
        "Onboarding Host Single Step Instrumentation scenario using agent auto install script",
        vm_provision="host-auto-inject-install-script",
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    container_auto_injection_install_script = InstallerAutoInjectionScenario(
        "CONTAINER_AUTO_INJECTION_INSTALL_SCRIPT",
        "Onboarding Container Single Step Instrumentation scenario using agent auto install script",
        vm_provision="container-auto-inject-install-script",
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    local_auto_injection_install_script = InstallerAutoInjectionScenario(
        "LOCAL_AUTO_INJECTION_INSTALL_SCRIPT",
        doc=(
            "To be executed locally with krunvm. Installs all the software fron agent installation script, "
            "and the replace the apm-library with the uploaded tar file from binaries"
        ),
        vm_provision="local-auto-inject-install-script",
        scenario_groups=[ScenarioGroup.ONBOARDING],
        github_workflow="aws_ssi",
    )

    lib_injection_validation = WeblogInjectionScenario(
        "LIB_INJECTION_VALIDATION",
        doc="Validates the init images without kubernetes enviroment",
        github_workflow="libinjection",
        scenario_groups=[ScenarioGroup.ALL, ScenarioGroup.LIB_INJECTION],
    )

    lib_injection_validation_unsupported_lang = WeblogInjectionScenario(
        "LIB_INJECTION_VALIDATION_UNSUPPORTED_LANG",
        doc="Validates the init images without kubernetes enviroment (unsupported lang versions)",
        github_workflow="libinjection",
        scenario_groups=[ScenarioGroup.ALL, ScenarioGroup.LIB_INJECTION],
    )

    k8s_lib_injection = K8sScenario("K8S_LIB_INJECTION", doc="Kubernetes lib injection with admission controller")
    k8s_lib_injection_operator = K8sScenario(
        "K8S_LIB_INJECTION_OPERATOR",
        doc="Use CRD Datadog Operator (uses real agent). Not configure the admission controller, the operator does it",
        with_datadog_operator=True,
    )
    k8s_lib_injection_uds = K8sScenario(
        "K8S_LIB_INJECTION_UDS",
        doc="Kubernetes lib injection with admission controller and uds",
        use_uds=True,
    )
    k8s_lib_injection_no_ac = K8sManualInstrumentationScenario(
        "K8S_LIB_INJECTION_NO_AC",
        doc="Kubernetes lib injection without admission controller",
    )
    k8s_lib_injection_no_ac_uds = K8sManualInstrumentationScenario(
        "K8S_LIB_INJECTION_NO_AC_UDS",
        doc="Kubernetes lib injection without admission controller and UDS",
        use_uds=True,
    )
    k8s_lib_injection_profiling_disabled = K8sScenario(
        "K8S_LIB_INJECTION_PROFILING_DISABLED",
        doc="Kubernetes lib injection with admission controller and profiling disabled by default",
        weblog_env={"DD_PROFILING_UPLOAD_PERIOD": "10", "DD_INTERNAL_PROFILING_LONG_LIVED_THRESHOLD": "1500"},
    )
    k8s_lib_injection_profiling_enabled = K8sScenario(
        "K8S_LIB_INJECTION_PROFILING_ENABLED",
        doc="Kubernetes lib injection with admission controller and profiling enaabled by cluster config",
        weblog_env={"DD_PROFILING_UPLOAD_PERIOD": "10", "DD_INTERNAL_PROFILING_LONG_LIVED_THRESHOLD": "1500"},
        dd_cluster_feature={"datadog.profiling.enabled": "auto"},
    )
    k8s_lib_injection_profiling_override = K8sScenario(
        "K8S_LIB_INJECTION_PROFILING_OVERRIDE",
        doc="Kubernetes lib injection with admission controller and profiling enaabled overriting cluster config",
        weblog_env={"DD_PROFILING_UPLOAD_PERIOD": "10", "DD_INTERNAL_PROFILING_LONG_LIVED_THRESHOLD": "1500"},
        dd_cluster_feature={
            "clusterAgent.env[0].name": "DD_ADMISSION_CONTROLLER_AUTO_INSTRUMENTATION_PROFILING_ENABLED",
            "clusterAgent.env[0].value": "auto",
        },
    )
    k8s_lib_injection_spark_djm = K8sSparkScenario("K8S_LIB_INJECTION_SPARK_DJM", doc="Kubernetes lib injection DJM")

    docker_ssi = DockerSSIScenario(
        "DOCKER_SSI",
        doc="Validates the installer and the ssi on a docker environment",
        scenario_groups=[ScenarioGroup.ALL, ScenarioGroup.DOCKER_SSI],
    )

    appsec_rasp = EndToEndScenario(
        "APPSEC_RASP",
        weblog_env={"DD_APPSEC_RASP_ENABLED": "true", "DD_APPSEC_RULES": "/appsec_rasp_ruleset.json"},
        weblog_volumes={"./tests/appsec/rasp/rasp_ruleset.json": {"bind": "/appsec_rasp_ruleset.json", "mode": "ro"}},
        doc="Enable APPSEC RASP",
        github_workflow="endtoend",
        scenario_groups=[ScenarioGroup.APPSEC, ScenarioGroup.APPSEC_RASP],
    )

    appsec_rasp_non_blocking = EndToEndScenario(
        "APPSEC_RASP_NON_BLOCKING",
        weblog_env={"DD_APPSEC_RASP_ENABLED": "true", "DD_APPSEC_RULES": "/appsec_rasp_non_blocking_ruleset.json"},
        weblog_volumes={
            "./tests/appsec/rasp/rasp_non_blocking_ruleset.json": {
                "bind": "/appsec_rasp_non_blocking_ruleset.json",
                "mode": "ro",
            }
        },
        doc="Enable APPSEC RASP",
        github_workflow="endtoend",
        scenario_groups=[ScenarioGroup.APPSEC],
    )

    agent_not_supporting_span_events = EndToEndScenario(
        "AGENT_NOT_SUPPORTING_SPAN_EVENTS",
        span_events=False,
        doc="The trace agent does not support Span Events as a top-level span field",
        scenario_groups=[ScenarioGroup.INTEGRATIONS],
    )

    external_processing = ExternalProcessingScenario(
        name="EXTERNAL_PROCESSING",
        doc="Envoy + external processing",
        rc_api_enabled=True,
    )

    external_processing_blocking = ExternalProcessingScenario(
        name="EXTERNAL_PROCESSING_BLOCKING",
        doc="Envoy + external processing + blocking rule file",
        extproc_env={"DD_APPSEC_RULES": "/appsec_blocking_rule.json"},
        extproc_volumes={"./tests/appsec/blocking_rule.json": {"bind": "/appsec_blocking_rule.json", "mode": "ro"}},
    )

    ipv6 = IPV6Scenario("IPV6")

    runtime_metrics_enabled = EndToEndScenario(
        "RUNTIME_METRICS_ENABLED",
        # Add environment variable DD_DOGSTATSD_START_DELAY=0 to avoid the default 30s startup delay in the Java tracer.
        # That delay is used in production to reduce the impact on startup and other side-effects on various application
        # servers. These considerations do not apply to the system-tests environment so we can reduce it to 0s.
        weblog_env={"DD_DOGSTATSD_START_DELAY": "0"},
        runtime_metrics_enabled=True,
        # Disable the proxy in between weblog and the agent so that we can send metrics (via UDP) to the agent.
        # The mitmproxy can only proxy UDP traffic by doing a host-wide transparent proxy, but we currently
        # via specific ports. As a result, with the proxy enabled all UDP traffic is being dropped.
        use_proxy_for_weblog=False,
        doc="Test runtime metrics",
    )


scenarios = _Scenarios()


def get_all_scenarios() -> list[Scenario]:
    result = []
    for name in dir(scenarios):
        if not name.startswith("_"):
            scenario: Scenario = getattr(scenarios, name)
            if issubclass(scenario.__class__, Scenario):
                result.append(scenario)

    return result


def _main():
    data = {
        scenario.name: {
            "name": scenario.name,
            "doc": scenario.doc,
            "github_workflow": scenario.github_workflow,
            "scenario_groups": scenario.scenario_groups,
        }
        for scenario in get_all_scenarios()
    }

    print(json.dumps(data, indent=2))  # noqa: T201


if __name__ == "__main__":
    _main()
