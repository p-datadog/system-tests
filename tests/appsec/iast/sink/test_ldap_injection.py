# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import pytest
from utils import context, coverage, released, missing_feature
from .._test_iast_fixtures import SinkFixture


@coverage.basic
@missing_feature(weblog_variant="spring-boot-3-native", reason="GraalVM. Tracing support only")
class TestLDAPInjection:
    """Test LDAP injection detection."""

    sink_fixture = SinkFixture(
        vulnerability_type="LDAP_INJECTION",
        http_method="POST",
        insecure_endpoint="/iast/ldapi/test_insecure",
        secure_endpoint="/iast/ldapi/test_secure",
        data={"username": "ssam", "password": "sammy"},
        location_map={"java": "com.datadoghq.system_tests.iast.utils.LDAPExamples",},
    )

    def setup_insecure(self):
        self.sink_fixture.setup_insecure()

    def test_insecure(self):
        self.sink_fixture.test_insecure()

    def setup_secure(self):
        self.sink_fixture.setup_secure()

    def test_secure(self):
        self.sink_fixture.test_secure()

    def setup_telemetry_metric_instrumented_sink(self):
        self.sink_fixture.setup_telemetry_metric_instrumented_sink()

    @missing_feature(context.library < "java@1.13.0", reason="Not implemented yet")
    def test_telemetry_metric_instrumented_sink(self):
        self.sink_fixture.test_telemetry_metric_instrumented_sink()

    def setup_telemetry_metric_executed_sink(self):
        self.sink_fixture.setup_telemetry_metric_executed_sink()

    @missing_feature(context.library < "java@1.13.0", reason="Not implemented yet")
    def test_telemetry_metric_executed_sink(self):
        self.sink_fixture.test_telemetry_metric_executed_sink()
