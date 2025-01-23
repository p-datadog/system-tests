# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import context, missing_feature, features, weblog, rfc
from ..utils import BaseSinkTest, validate_stack_traces


@features.iast_sink_email_html_injection
class TestEmailHtmlInjection(BaseSinkTest):
    """Test email html injection detection."""

    vulnerability_type = "EMAIL_HTML_INJECTION"
    http_method = "POST"
    insecure_endpoint = "/iast/email_html_injection/test_insecure"
    secure_endpoint = "/iast/email_html_injection/test_secure"
    data = {"username": "Josh", "email": "fakeemail@localhost"}
    location_map = {"java": "com.datadoghq.system_tests.iast.utils.EmailExamples"}

    @missing_feature(library="dotnet", reason="Not implemented yet")
    def test_telemetry_metric_instrumented_sink(self):
        super().test_telemetry_metric_instrumented_sink()


@rfc(
    "https://docs.google.com/document/d/1ga7yCKq2htgcwgQsInYZKktV0hNlv4drY9XzSxT-o5U/edit?tab=t.0#heading=h.d0f5wzmlfhat"
)
@features.iast_stack_trace
class TestEmailHtmlInjection_StackTrace:
    """Validate stack trace generation"""

    def setup_stack_trace(self):
        self.r = weblog.post(
            "/iast/email_html_injection/test_insecure", data={"username": "Josh", "email": "fakeemail@localhost"}
        )

    def test_stack_trace(self):
        validate_stack_traces(self.r)
