import pytest

from parametric.protos.apm_test_library_pb2 import DistributedHTTPHeaders


@pytest.mark.skip_library("golang", "not implemented")
@pytest.mark.skip_library("dotnet", "not implemented")
@pytest.mark.skip_library("nodejs", "not implemented")
def test_distributed_headers_extract_datadog(test_agent, test_library):
    """Ensure that Datadog distributed tracing headers are extracted
    and activated properly.
    """

    with test_library:
        http_headers = DistributedHTTPHeaders()
        http_headers.x_datadog_trace_id_key = "x-datadog-trace-id"
        http_headers.x_datadog_trace_id_value = "12345"
        http_headers.x_datadog_parent_id_key = "x-datadog-parent-id"
        http_headers.x_datadog_parent_id_value = "123"

        with test_library.start_span(
            name="name", service="service", resource="resource", origin="synthetics", http_headers=http_headers
        ) as span:
            span.set_meta(key="http.status_code", val="200")

    span = get_span(test_agent)
    assert span.get("trace_id") == 12345
    assert span.get("parent_id") == 123


@pytest.mark.skip("needs to be implemented by tracers and test needs to adhere to RFC")
@pytest.mark.parametrize("apm_test_server_env", [{"DD_TRACE_PROPAGATION_STYLE_EXTRACT": "W3C"}])
def test_distributed_headers_extract_w3c001(apm_test_server_env, test_agent, test_library):
    """Ensure that W3C distributed tracing headers are extracted
    and activated properly.
    """

    with test_library:
        http_headers = DistributedHTTPHeaders()
        http_headers.traceparent_key = "traceparent"
        http_headers.traceparent_value = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

        with test_library.start_span(
            name="name", service="service", resource="resource", origin="synthetics", http_headers=http_headers
        ) as span:
            span.set_meta(key="http.status_code", val="200")

    span = get_span(test_agent)
    assert span.get("trace_id") == 11803532876627986230


@pytest.mark.skip_library("golang", "not implemented")
@pytest.mark.skip_library("dotnet", "not implemented")
@pytest.mark.skip_library("nodejs", "not implemented")
def test_distributed_headers_inject_datadog(test_agent, test_library):
    """Ensure that Datadog distributed tracing headers are injected properly.
    """
    with test_library.start_span(
        name="name"
    ) as span:
        span.set_meta(key="http.status_code", val="200")
        headers = test_library.inject_headers()
    # I think I should add headers and make span, then while that span is active try to inject its context
    # Or we could create a span, inject the headers (need to see if we can pull the span id off of the span) and then we can just do the injection
    # Then from there we can call get_span and then 
    
    span = get_span(test_agent)

    print(headers)
    assert span.get("parent_id") == 123



def get_span(test_agent):
    traces = test_agent.traces()
    span = traces[0][0]
    return span
