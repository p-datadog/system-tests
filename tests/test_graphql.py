# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import json
from utils import (
    interfaces,
    rfc,
    weblog,
    features,
    scenarios,
)


@rfc("https://docs.google.com/document/d/1JjctLYE4a4EbtmnFixQt-TilltcSV69IAeiSGjcUL34")
@scenarios.graphql_appsec
@features.graphql_query_error_reporting
class Test_GraphQLQueryErrorReporting:
    """Test if GraphQL query errors create span events"""

    def setup_execute_error_span_event(self):
        self.request = weblog.post(
            "/graphql",
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "query": "query myQuery { withError }",
                    "operationName": "myQuery",
                }
            ),
        )

    def test_execute_error_span_event(self):
        """Test if the main GraphQL span contains a span event with the appropriate error information"""

        assert self.request.status_code == 200

        spans = list(
            span
            for _, _, span in interfaces.library.get_spans(request=self.request, full_trace=True)
            if span["name"] == "graphql.execute"
        )

        assert len(spans) == 1
        span = spans[0]

        events = self._get_events(span)
        graphql_events = [event for event in events if event["name"] == "dd.graphql.query.error"]

        assert len(graphql_events) == 1
        event = graphql_events[0]

        assert event["name"] == "dd.graphql.query.error"

        attributes = event["attributes"]

        assert isinstance(attributes["message"], str)
        assert isinstance(attributes["type"], str)
        assert isinstance(attributes["stacktrace"], str)

        for path in attributes["path"]:
            assert isinstance(path, str)

        for location in attributes["locations"]:
            assert len(location.split(":")) == 2
            assert location.split(":")[0].isdigit()
            assert location.split(":")[1].isdigit()

    @staticmethod
    def _get_events(span):
        if "events" in span["meta"]:
            return json.loads(span["meta"]["events"])
        else:
            return span["span_events"]
