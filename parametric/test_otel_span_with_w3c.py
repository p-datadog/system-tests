import time

import pytest

from utils.parametric.spec.otel_trace import SK_PRODUCER
from utils.parametric.spec.trace import SAMPLING_PRIORITY_KEY, ORIGIN
from utils.parametric.test_agent import get_span

# this global mark applies to all tests in this file.
#   DD_TRACE_OTEL_ENABLED=true is required in some tracers (.NET, Python?)
#   CORECLR_ENABLE_PROFILING=1 is required in .NET to enable auto-instrumentation
pytestmark = pytest.mark.parametrize(
    "library_env", [{"DD_TRACE_OTEL_ENABLED": "true", "CORECLR_ENABLE_PROFILING": "1"}],
)


@pytest.mark.skip_library("dotnet", "Span names don't match expectations: 'ApmTestClient.internal' == 'operation'")
@pytest.mark.skip_library("php", "Not implemented")
@pytest.mark.skip_library("ruby", "Not implemented")
def test_otel_start_span_with_w3c(test_agent, test_library):
    """
        - Start/end a span with start and end options
    """
    with test_library:
        duration_us = int(2 * 1_000_000)
        start_time = int(time.time())
        with test_library.otel_start_span(
            "operation", span_kind=SK_PRODUCER, timestamp=start_time, attributes={"start_attr_key": "start_attr_val"},
        ) as parent:
            parent.end_span(timestamp=start_time + duration_us)
    duration_ns = int(duration_us * 1_000)  # OTEL durations are microseconds, must convert to ns for dd

    root_span = get_span(test_agent)
    assert root_span["name"] == "operation"
    assert root_span["resource"] == "operation"
    assert root_span["meta"]["start_attr_key"] == "start_attr_val"
    assert root_span["duration"] == duration_ns


@pytest.mark.skip_library("java", "Not implemented")
@pytest.mark.skip_library("php", "Not implemented")
@pytest.mark.skip_library("ruby", "Not implemented")
def test_otel_span_with_w3c_headers(test_agent, test_library):
    with test_library:
        with test_library.otel_start_span(
            name="name", http_headers=[["traceparent", "00-00000000000000001111111111111111-2222222222222222-01"]],
        ) as span:
            context = span.span_context()
            assert context.get("trace_flags") == "01"
            assert context.get("trace_id") == "00000000000000001111111111111111"
            span.end_span()

    span = get_span(test_agent)
    assert span.get("trace_id") == 1229782938247303441
    assert span.get("parent_id") == 2459565876494606882
    assert span["metrics"].get(SAMPLING_PRIORITY_KEY) == 1
    assert span["meta"].get(ORIGIN) is None
