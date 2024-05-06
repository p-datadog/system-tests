# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from utils import features, scenarios
from ..utils import BaseSourceTest, get_all_iast_events, get_iast_sources


@features.iast_source_kafka_key
@scenarios.integrations
class TestKafkaKey(BaseSourceTest):
    """Verify that kafka message key is tainted"""

    endpoint = "/iast/source/kafkakey/test"
    requests_kwargs = [{"method": "GET"}]
    source_type = "kafka.message.key"
    source_value = "hello key!"

    def get_sources(self, request):
        iast_event = get_all_iast_events()
        return get_iast_sources(iast_event)
