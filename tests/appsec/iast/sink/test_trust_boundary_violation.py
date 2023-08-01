# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import pytest
from utils import context, coverage, released, missing_feature
from ..iast_fixtures import SinkFixture

if context.library == "cpp":
    pytestmark = pytest.mark.skip("not relevant")


@coverage.basic
@released(dotnet="?", golang="?", php_appsec="?", python="?", ruby="?", nodejs="?")
@released(
    java={
        "resteasy-netty3": "?",
        "jersey-grizzly2": "?",
        "vertx3": "?",
        "vertx4": "?",
        "akka-http": "?",
        "ratpack": "?",
        "spring-boot-3-native": "?",
        "*": "1.19.0",
    }
)
class TestTrustBoundaryViolation:
    """Test Trust Boundary Violation detection."""

    sink_fixture = SinkFixture(
        vulnerability_type="TRUST_BOUNDARY_VIOLATION",
        http_method="GET",
        insecure_endpoint="/iast/trust-boundary-violation/test_insecure",
        secure_endpoint="/iast/trust-boundary-violation/test_secure",
        data={"username": "shaquille_oatmeal", "password": "123456"},
        location_map={"nodejs": "iast/index.js",},
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

    @missing_feature(library="nodejs", reason="Metrics implemented")
    @missing_feature(library="java", reason="Metrics implemented")
    def test_telemetry_metric_instrumented_sink(self):
        self.sink_fixture.test_telemetry_metric_instrumented_sink()

    def setup_telemetry_metric_executed_sink(self):
        self.sink_fixture.setup_telemetry_metric_executed_sink()

    @missing_feature(library="nodejs", reason="Metrics implemented")
    @missing_feature(library="java", reason="Metrics implemented")
    def test_telemetry_metric_executed_sink(self):
        self.sink_fixture.test_telemetry_metric_executed_sink()
