# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import coverage, missing_feature
from .._test_iast_fixtures import BaseSinkTest


@coverage.basic
class Test_TrustBoundaryViolation(BaseSinkTest):
    """Test Trust Boundary Violation detection."""

    vulnerability_type = "TRUST_BOUNDARY_VIOLATION"
    http_method = "GET"
    insecure_endpoint = "/iast/trust-boundary-violation/test_insecure"
    secure_endpoint = "/iast/trust-boundary-violation/test_secure"
    data = {"username": "shaquille_oatmeal", "password": "123456"}
    location_map = {"nodejs": "iast/index.js"}

    @missing_feature(library="nodejs", reason="Metrics implemented")
    @missing_feature(library="java", reason="Metrics implemented")
    def test_telemetry_metric_instrumented_sink(self):
        super().test_telemetry_metric_instrumented_sink()

    @missing_feature(library="nodejs", reason="Metrics implemented")
    @missing_feature(library="java", reason="Metrics implemented")
    def test_telemetry_metric_executed_sink(self):
        super().test_telemetry_metric_executed_sink()
