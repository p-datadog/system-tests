# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

import threading

from utils.interfaces._core import InterfaceValidator
from utils.interfaces._schemas_validators import SchemaValidator

from utils.interfaces._library.appsec import _NoAppsecEvent, _WafAttack, _AppSecValidation, _ReportedHeader
from utils.interfaces._library.metrics import _MetricAbsence, _MetricExistence
from utils.interfaces._library.miscs import _TraceIdUniqueness, _ReceiveRequestRootTrace, _SpanValidation
from utils.interfaces._library.sampling import (
    _TracesSamplingDecision,
    _AllRequestsTransmitted,
    _AddSamplingDecisionValidation,
    _DistributedTracesDeterministicSamplingDecisisonValidation,
)
from utils.interfaces._library.trace_headers import (
    _TraceHeadersContainerTags,
    _TraceHeadersCount,
    _TraceHeadersPresent,
    _TraceHeadersPresentPhp,
    _TraceHeadersContainerTagsCpp,
)
from utils.interfaces._library.telemetry import (
    _TelemetryRequestSuccessValidation,
    _SeqIdLatencyValidation,
    _NoSkippedSeqId,
    _TelemetryProxyValidation,
    _AppStartedLibraryValidation,
    _IntegrationChangedValidation,
    TELEMETRY_AGENT_ENDPOINT,
)


class LibraryInterfaceValidator(InterfaceValidator):
    """Validate library/agent interface"""

    def __init__(self):
        super().__init__("library")
        self.ready = threading.Event()
        self.uniqueness_exceptions = _TraceIdUniquenessExceptions()

    def append_data(self, data):
        self.ready.set()
        return super().append_data(data)

    def assert_trace_headers_container_tags(self):
        self.append_validation(_TraceHeadersContainerTags())

    def assert_trace_headers_container_tags_cpp(self):
        self.append_validation(_TraceHeadersContainerTagsCpp())

    def assert_trace_headers_present(self):
        self.append_validation(_TraceHeadersPresent())

    def assert_trace_headers_present_php(self):
        self.append_validation(_TraceHeadersPresentPhp())

    def assert_trace_headers_count_match(self):
        self.append_validation(_TraceHeadersCount())

    def assert_receive_request_root_trace(self):
        self.append_validation(_ReceiveRequestRootTrace())

    def assert_schemas(self, allowed_errors=None):
        self.append_validation(SchemaValidator("library", allowed_errors))

    def assert_sampling_decision_respected(self, sampling_rate):
        self.append_validation(_TracesSamplingDecision(sampling_rate))

    def assert_all_traces_requests_forwarded(self, paths):
        self.append_validation(_AllRequestsTransmitted(paths))

    def assert_trace_id_uniqueness(self):
        self.append_validation(_TraceIdUniqueness(self.uniqueness_exceptions))

    def assert_sampling_decisions_added(self, traces):
        self.append_validation(_AddSamplingDecisionValidation(traces))

    def assert_deterministic_sampling_decisions(self, traces):
        self.append_validation(_DistributedTracesDeterministicSamplingDecisisonValidation(traces))

    def assert_no_appsec_event(self, request):
        self.append_validation(_NoAppsecEvent(request))

    def assert_waf_attack(self, request, rule=None, pattern=None, address=None, patterns=None, key_path=None):
        self.append_validation(
            _WafAttack(request, rule=rule, pattern=pattern, address=address, patterns=patterns, key_path=key_path)
        )

    def assert_metric_existence(self, metric_name):
        self.append_validation(_MetricExistence(metric_name))

    def assert_metric_absence(self, metric_name):
        self.append_validation(_MetricAbsence(metric_name))

    def add_span_validation(self, request=None, validator=None):
        self.append_validation(_SpanValidation(request=request, validator=validator))

    def add_appsec_validation(self, request=None, validator=None, legacy_validator=None):
        self.append_validation(
            _AppSecValidation(request=request, validator=validator, legacy_validator=legacy_validator)
        )

    def add_appsec_reported_header(self, request, header_name):
        self.append_validation(_ReportedHeader(request, header_name))

    def assert_telemetry_requests_are_successful(self):
        self.append_validation(_TelemetryRequestSuccessValidation(TELEMETRY_AGENT_ENDPOINT))

    def assert_seq_ids_are_roughly_sequential(self):
        self.append_validation(_SeqIdLatencyValidation())

    def assert_no_skipped_seq_ids(self):
        self.append_validation(_NoSkippedSeqId())

    def assert_send_app_started(self):
        self.append_validation(_AppStartedLibraryValidation())

    def assert_integrations_changed_message_valid(self):
        self.append_validation(_IntegrationChangedValidation())

    def assert_all_telemetry_messages_proxied(self, agent_interface):
        validation = _TelemetryProxyValidation.LibToAgent()
        self.append_validation(validation)
        agent_interface.append_validation(_TelemetryProxyValidation(validation))


class _TraceIdUniquenessExceptions:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.traces_ids = set()

    def add_trace_id(self, id):
        with self._lock:
            self.traces_ids.add(id)

    def should_be_unique(self, trace_id):
        with self._lock:
            return trace_id not in self.traces_ids
