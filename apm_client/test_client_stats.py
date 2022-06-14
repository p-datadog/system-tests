import pytest

from .conftest import _TestTracer
from .conftest import go_library_server_factory
from .conftest import python_library_server_factory


parametrize = pytest.mark.parametrize
snapshot = pytest.mark.snapshot


@snapshot(ignores=["error"])
@parametrize(
    "apm_test_server_factory",
    [
        python_library_server_factory,
        go_library_server_factory,
    ],
)
@parametrize(
    "apm_test_server_env",
    [
        {
            "DD_TRACE_COMPUTE_STATS": "1",
        },
    ],
)
def test_client_trace(apm_test_server_factory, test_agent, test_client, apm_test_server_env):
    with test_client.start_span(name="web.request", resource="/users", service="webserver") as span:
        with test_client.start_span(
            name="postgres.query", resource="SELECT 1", service="postgres", parent_id=span.span_id
        ):
            pass
    test_client.flush()

    requests = test_agent.requests()
    traces = test_agent.traces()
    stats = test_agent.tracestats()
    print(traces)
    print(stats)
    assert 0


@snapshot(
    ignores=["error"],
    # Specify a custom token so all parametrizations use the same snapshots
    token="apm_client.test_client_stats.test_client_snapshot",
)
@parametrize(
    "apm_test_server_factory",
    [
        python_library_server_factory,
        go_library_server_factory,
    ],
)
def test_client_snapshot(test_agent, test_client: _TestTracer):
    """Ensure clients mostly submit the same data for a trace.

    Data which is inconsistent enough between clients is ignored
    with the snapshot `ignores` argument.
    """
    with test_client.start_span(name="web.request", resource="/users", service="webserver") as span:
        span.set_meta("key", "val")
        with test_client.start_span(
            name="postgres.query", resource="SELECT 1", service="postgres", parent_id=span.span_id
        ):
            pass
