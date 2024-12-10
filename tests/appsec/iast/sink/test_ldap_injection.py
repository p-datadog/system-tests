# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import context, missing_feature, features, rfc, weblog
from ..utils import BaseSinkTest, validate_stack_traces


@features.iast_sink_ldap_injection
class TestLDAPInjection(BaseSinkTest):
    """Test LDAP injection detection."""

    vulnerability_type = "LDAP_INJECTION"
    http_method = "POST"
    insecure_endpoint = "/iast/ldapi/test_insecure"
    secure_endpoint = "/iast/ldapi/test_secure"
    data = {"username": "ssam", "password": "sammy"}
    location_map = {
        "java": "com.datadoghq.system_tests.iast.utils.LDAPExamples",
        "nodejs": {"express4": "iast/index.js", "express4-typescript": "iast.ts", "express5": "iast/index.js"},
    }

    @missing_feature(context.library < "java@1.9.0", reason="Metrics not implemented")
    @missing_feature(library="dotnet", reason="Not implemented yet")
    def test_telemetry_metric_instrumented_sink(self):
        super().test_telemetry_metric_instrumented_sink()

    @missing_feature(context.library < "java@1.11.0", reason="Metrics not implemented")
    def test_telemetry_metric_executed_sink(self):
        super().test_telemetry_metric_executed_sink()


@rfc(
    "https://docs.google.com/document/d/1ga7yCKq2htgcwgQsInYZKktV0hNlv4drY9XzSxT-o5U/edit?tab=t.0#heading=h.d0f5wzmlfhat"
)
@features.iast_stack_trace
class TestLDAPInjection_StackTrace:
    """Validate stack trace generation """

    def setup_stack_trace(self):
        self.r = weblog.post("/iast/ldapi/test_insecure", data={"username": "ssam", "password": "sammy"})

    def test_stack_trace(self):
        validate_stack_traces(self.r)
