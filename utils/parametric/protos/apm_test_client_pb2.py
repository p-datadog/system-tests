# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/apm_test_client.proto
# Protobuf Python Version: 4.25.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1cprotos/apm_test_client.proto\"\x0b\n\tCrashArgs\"\r\n\x0b\x43rashReturn\"\x14\n\x12GetTraceConfigArgs\"x\n\x14GetTraceConfigReturn\x12\x31\n\x06\x63onfig\x18\x01 \x03(\x0b\x32!.GetTraceConfigReturn.ConfigEntry\x1a-\n\x0b\x43onfigEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\xca\x02\n\rStartSpanArgs\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x14\n\x07service\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x16\n\tparent_id\x18\x03 \x01(\x04H\x01\x88\x01\x01\x12\x15\n\x08resource\x18\x04 \x01(\tH\x02\x88\x01\x01\x12\x11\n\x04type\x18\x05 \x01(\tH\x03\x88\x01\x01\x12\x13\n\x06origin\x18\x06 \x01(\tH\x04\x88\x01\x01\x12\x32\n\x0chttp_headers\x18\x07 \x01(\x0b\x32\x17.DistributedHTTPHeadersH\x05\x88\x01\x01\x12\x1f\n\tspan_tags\x18\x08 \x03(\x0b\x32\x0c.HeaderTuple\x12\x1d\n\nspan_links\x18\t \x03(\x0b\x32\t.SpanLinkB\n\n\x08_serviceB\x0c\n\n_parent_idB\x0b\n\t_resourceB\x07\n\x05_typeB\t\n\x07_originB\x0f\n\r_http_headers\"<\n\x16\x44istributedHTTPHeaders\x12\"\n\x0chttp_headers\x18\x01 \x03(\x0b\x32\x0c.HeaderTuple\"y\n\x08SpanLink\x12\x13\n\tparent_id\x18\x01 \x01(\x04H\x00\x12/\n\x0chttp_headers\x18\x02 \x01(\x0b\x32\x17.DistributedHTTPHeadersH\x00\x12\x1f\n\nattributes\x18\x03 \x01(\x0b\x32\x0b.AttributesB\x06\n\x04\x66rom\")\n\x0bHeaderTuple\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\"4\n\x0fStartSpanReturn\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x10\n\x08trace_id\x18\x02 \x01(\x04\"$\n\x11InjectHeadersArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\"Z\n\x13InjectHeadersReturn\x12\x32\n\x0chttp_headers\x18\x01 \x01(\x0b\x32\x17.DistributedHTTPHeadersH\x00\x88\x01\x01\x42\x0f\n\r_http_headers\"\x1c\n\x0e\x46inishSpanArgs\x12\n\n\x02id\x18\x01 \x01(\x04\"\x12\n\x10\x46inishSpanReturn\"\x14\n\x12SpanGetCurrentArgs\"9\n\x14SpanGetCurrentReturn\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x10\n\x08trace_id\x18\x02 \x01(\x04\"\"\n\x0fSpanGetNameArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\"!\n\x11SpanGetNameReturn\x12\x0c\n\x04name\x18\x01 \x01(\t\"&\n\x13SpanGetResourceArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\")\n\x15SpanGetResourceReturn\x12\x10\n\x08resource\x18\x01 \x01(\t\"/\n\x0fSpanGetMetaArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0b\n\x03key\x18\x02 \x01(\t\",\n\x11SpanGetMetaReturn\x12\x17\n\x05value\x18\x01 \x01(\x0b\x32\x08.AttrVal\"1\n\x11SpanGetMetricArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0b\n\x03key\x18\x02 \x01(\t\"$\n\x13SpanGetMetricReturn\x12\r\n\x05value\x18\x01 \x01(\x02\">\n\x0fSpanSetMetaArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0b\n\x03key\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\t\"\x13\n\x11SpanSetMetaReturn\"@\n\x11SpanSetMetricArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0b\n\x03key\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\x02\"\x15\n\x13SpanSetMetricReturn\"\x7f\n\x10SpanSetErrorArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x11\n\x04type\x18\x02 \x01(\tH\x00\x88\x01\x01\x12\x14\n\x07message\x18\x03 \x01(\tH\x01\x88\x01\x01\x12\x12\n\x05stack\x18\x04 \x01(\tH\x02\x88\x01\x01\x42\x07\n\x05_typeB\n\n\x08_messageB\x08\n\x06_stack\"\x14\n\x12SpanSetErrorReturn\"8\n\x13SpanSetResourceArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x10\n\x08resource\x18\x02 \x01(\t\"\x17\n\x15SpanSetResourceReturn\"@\n\x0fSpanAddLinkArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x1c\n\tspan_link\x18\x02 \x01(\x0b\x32\t.SpanLink\"\x13\n\x11SpanAddLinkReturn\"f\n\x0fHTTPRequestArgs\x12\x0b\n\x03url\x18\x01 \x01(\t\x12\x0e\n\x06method\x18\x02 \x01(\t\x12(\n\x07headers\x18\x03 \x01(\x0b\x32\x17.DistributedHTTPHeaders\x12\x0c\n\x04\x62ody\x18\x04 \x01(\x0c\"(\n\x11HTTPRequestReturn\x12\x13\n\x0bstatus_code\x18\x01 \x01(\t\"\x10\n\x0e\x46lushSpansArgs\"\x12\n\x10\x46lushSpansReturn\"\x15\n\x13\x46lushTraceStatsArgs\"\x17\n\x15\x46lushTraceStatsReturn\"\xfa\x02\n\x11OtelStartSpanArgs\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x16\n\tparent_id\x18\x03 \x01(\x04H\x00\x88\x01\x01\x12\x16\n\tspan_kind\x18\t \x01(\x04H\x01\x88\x01\x01\x12\x14\n\x07service\x18\x04 \x01(\tH\x02\x88\x01\x01\x12\x15\n\x08resource\x18\x05 \x01(\tH\x03\x88\x01\x01\x12\x11\n\x04type\x18\x06 \x01(\tH\x04\x88\x01\x01\x12\x16\n\ttimestamp\x18\x07 \x01(\x03H\x05\x88\x01\x01\x12\x1d\n\nspan_links\x18\x0b \x03(\x0b\x32\t.SpanLink\x12\x32\n\x0chttp_headers\x18\n \x01(\x0b\x32\x17.DistributedHTTPHeadersH\x06\x88\x01\x01\x12\x1f\n\nattributes\x18\x08 \x01(\x0b\x32\x0b.AttributesB\x0c\n\n_parent_idB\x0c\n\n_span_kindB\n\n\x08_serviceB\x0b\n\t_resourceB\x07\n\x05_typeB\x0c\n\n_timestampB\x0f\n\r_http_headers\"8\n\x13OtelStartSpanReturn\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x10\n\x08trace_id\x18\x02 \x01(\x04\"C\n\x0fOtelEndSpanArgs\x12\n\n\x02id\x18\x01 \x01(\x04\x12\x16\n\ttimestamp\x18\x02 \x01(\x03H\x00\x88\x01\x01\x42\x0c\n\n_timestamp\"\x13\n\x11OtelEndSpanReturn\"%\n\x12OtelForceFlushArgs\x12\x0f\n\x07seconds\x18\x01 \x01(\r\"\'\n\x14OtelForceFlushReturn\x12\x0f\n\x07success\x18\x01 \x01(\x08\"%\n\x12OtelFlushSpansArgs\x12\x0f\n\x07seconds\x18\x01 \x01(\r\"\'\n\x14OtelFlushSpansReturn\x12\x0f\n\x07success\x18\x01 \x01(\x08\"\x19\n\x17OtelFlushTraceStatsArgs\"\x1b\n\x19OtelFlushTraceStatsReturn\"\x14\n\x12OtelStopTracerArgs\"\x16\n\x14OtelStopTracerReturn\"&\n\x13OtelIsRecordingArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\"-\n\x15OtelIsRecordingReturn\x12\x14\n\x0cis_recording\x18\x01 \x01(\x08\"&\n\x13OtelSpanContextArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\"t\n\x15OtelSpanContextReturn\x12\x0f\n\x07span_id\x18\x01 \x01(\t\x12\x10\n\x08trace_id\x18\x02 \x01(\t\x12\x13\n\x0btrace_flags\x18\x03 \x01(\t\x12\x13\n\x0btrace_state\x18\x04 \x01(\t\x12\x0e\n\x06remote\x18\x05 \x01(\x08\"\x18\n\x16OtelSpanGetCurrentArgs\"=\n\x18OtelSpanGetCurrentReturn\x12\x0f\n\x07span_id\x18\x01 \x01(\t\x12\x10\n\x08trace_id\x18\x02 \x01(\t\"G\n\x11OtelSetStatusArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0c\n\x04\x63ode\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\"\x15\n\x13OtelSetStatusReturn\"0\n\x0fOtelSetNameArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0c\n\x04name\x18\x02 \x01(\t\"\x13\n\x11OtelSetNameReturn\"I\n\x15OtelSetAttributesArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x1f\n\nattributes\x18\x02 \x01(\x0b\x32\x0b.Attributes\"\x19\n\x17OtelSetAttributesReturn\"x\n\x10OtelAddEventArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x16\n\ttimestamp\x18\x03 \x01(\x03H\x00\x88\x01\x01\x12\x1f\n\nattributes\x18\x04 \x01(\x0b\x32\x0b.AttributesB\x0c\n\n_timestamp\"\x14\n\x12OtelAddEventReturn\"\\\n\x17OtelRecordExceptionArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x1f\n\nattributes\x18\x04 \x01(\x0b\x32\x0b.Attributes\"\x1b\n\x19OtelRecordExceptionReturn\"4\n\x14OtelGetAttributeArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\x12\x0b\n\x03key\x18\x02 \x01(\t\"1\n\x16OtelGetAttributeReturn\x12\x17\n\x05value\x18\x01 \x01(\x0b\x32\x08.ListVal\"\"\n\x0fOtelGetNameArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\"!\n\x11OtelGetNameReturn\x12\x0c\n\x04name\x18\x01 \x01(\t\"#\n\x10OtelGetLinksArgs\x12\x0f\n\x07span_id\x18\x01 \x01(\x04\".\n\x12OtelGetLinksReturn\x12\x18\n\x05links\x18\x01 \x03(\x0b\x32\t.SpanLink\"r\n\nAttributes\x12*\n\x08key_vals\x18\x03 \x03(\x0b\x32\x18.Attributes.KeyValsEntry\x1a\x38\n\x0cKeyValsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x17\n\x05value\x18\x02 \x01(\x0b\x32\x08.ListVal:\x02\x38\x01\" \n\x07ListVal\x12\x15\n\x03val\x18\x01 \x03(\x0b\x32\x08.AttrVal\"g\n\x07\x41ttrVal\x12\x12\n\x08\x62ool_val\x18\x01 \x01(\x08H\x00\x12\x14\n\nstring_val\x18\x02 \x01(\tH\x00\x12\x14\n\ndouble_val\x18\x03 \x01(\x01H\x00\x12\x15\n\x0binteger_val\x18\x04 \x01(\x03H\x00\x42\x05\n\x03val\"\x10\n\x0eStopTracerArgs\"\x12\n\x10StopTracerReturn2\xdf\x10\n\tAPMClient\x12#\n\x05\x43rash\x12\n.CrashArgs\x1a\x0c.CrashReturn\"\x00\x12/\n\tStartSpan\x12\x0e.StartSpanArgs\x1a\x10.StartSpanReturn\"\x00\x12\x32\n\nFinishSpan\x12\x0f.FinishSpanArgs\x1a\x11.FinishSpanReturn\"\x00\x12>\n\x0eSpanGetCurrent\x12\x13.SpanGetCurrentArgs\x1a\x15.SpanGetCurrentReturn\"\x00\x12\x35\n\x0bSpanGetName\x12\x10.SpanGetNameArgs\x1a\x12.SpanGetNameReturn\"\x00\x12\x41\n\x0fSpanGetResource\x12\x14.SpanGetResourceArgs\x1a\x16.SpanGetResourceReturn\"\x00\x12\x35\n\x0bSpanGetMeta\x12\x10.SpanGetMetaArgs\x1a\x12.SpanGetMetaReturn\"\x00\x12;\n\rSpanGetMetric\x12\x12.SpanGetMetricArgs\x1a\x14.SpanGetMetricReturn\"\x00\x12\x35\n\x0bSpanSetMeta\x12\x10.SpanSetMetaArgs\x1a\x12.SpanSetMetaReturn\"\x00\x12;\n\rSpanSetMetric\x12\x12.SpanSetMetricArgs\x1a\x14.SpanSetMetricReturn\"\x00\x12\x38\n\x0cSpanSetError\x12\x11.SpanSetErrorArgs\x1a\x13.SpanSetErrorReturn\"\x00\x12\x41\n\x0fSpanSetResource\x12\x14.SpanSetResourceArgs\x1a\x16.SpanSetResourceReturn\"\x00\x12\x35\n\x0bSpanAddLink\x12\x10.SpanAddLinkArgs\x1a\x12.SpanAddLinkReturn\"\x00\x12;\n\x11HTTPClientRequest\x12\x10.HTTPRequestArgs\x1a\x12.HTTPRequestReturn\"\x00\x12;\n\x11HTTPServerRequest\x12\x10.HTTPRequestArgs\x1a\x12.HTTPRequestReturn\"\x00\x12;\n\rInjectHeaders\x12\x12.InjectHeadersArgs\x1a\x14.InjectHeadersReturn\"\x00\x12\x32\n\nFlushSpans\x12\x0f.FlushSpansArgs\x1a\x11.FlushSpansReturn\"\x00\x12\x41\n\x0f\x46lushTraceStats\x12\x14.FlushTraceStatsArgs\x1a\x16.FlushTraceStatsReturn\"\x00\x12;\n\rOtelStartSpan\x12\x12.OtelStartSpanArgs\x1a\x14.OtelStartSpanReturn\"\x00\x12\x35\n\x0bOtelEndSpan\x12\x10.OtelEndSpanArgs\x1a\x12.OtelEndSpanReturn\"\x00\x12\x38\n\x0cOtelAddEvent\x12\x11.OtelAddEventArgs\x1a\x13.OtelAddEventReturn\"\x00\x12M\n\x13OtelRecordException\x12\x18.OtelRecordExceptionArgs\x1a\x1a.OtelRecordExceptionReturn\"\x00\x12\x41\n\x0fOtelIsRecording\x12\x14.OtelIsRecordingArgs\x1a\x16.OtelIsRecordingReturn\"\x00\x12\x41\n\x0fOtelSpanContext\x12\x14.OtelSpanContextArgs\x1a\x16.OtelSpanContextReturn\"\x00\x12J\n\x12OtelSpanGetCurrent\x12\x17.OtelSpanGetCurrentArgs\x1a\x19.OtelSpanGetCurrentReturn\"\x00\x12;\n\rOtelSetStatus\x12\x12.OtelSetStatusArgs\x1a\x14.OtelSetStatusReturn\"\x00\x12\x35\n\x0bOtelSetName\x12\x10.OtelSetNameArgs\x1a\x12.OtelSetNameReturn\"\x00\x12G\n\x11OtelSetAttributes\x12\x16.OtelSetAttributesArgs\x1a\x18.OtelSetAttributesReturn\"\x00\x12>\n\x0eOtelFlushSpans\x12\x13.OtelFlushSpansArgs\x1a\x15.OtelFlushSpansReturn\"\x00\x12M\n\x13OtelFlushTraceStats\x12\x18.OtelFlushTraceStatsArgs\x1a\x1a.OtelFlushTraceStatsReturn\"\x00\x12\x44\n\x10OtelGetAttribute\x12\x15.OtelGetAttributeArgs\x1a\x17.OtelGetAttributeReturn\"\x00\x12\x35\n\x0bOtelGetName\x12\x10.OtelGetNameArgs\x1a\x12.OtelGetNameReturn\"\x00\x12\x38\n\x0cOtelGetLinks\x12\x11.OtelGetLinksArgs\x1a\x13.OtelGetLinksReturn\"\x00\x12\x32\n\nStopTracer\x12\x0f.StopTracerArgs\x1a\x11.StopTracerReturn\"\x00\x12>\n\x0eGetTraceConfig\x12\x13.GetTraceConfigArgs\x1a\x15.GetTraceConfigReturn\"\x00\x42*\n\x14\x63om.datadoghq.clientZ\x02./\xaa\x02\rApmTestClientb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.apm_test_client_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  _globals['DESCRIPTOR']._options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n\024com.datadoghq.clientZ\002./\252\002\rApmTestClient'
  _globals['_GETTRACECONFIGRETURN_CONFIGENTRY']._options = None
  _globals['_GETTRACECONFIGRETURN_CONFIGENTRY']._serialized_options = b'8\001'
  _globals['_ATTRIBUTES_KEYVALSENTRY']._options = None
  _globals['_ATTRIBUTES_KEYVALSENTRY']._serialized_options = b'8\001'
  _globals['_CRASHARGS']._serialized_start=32
  _globals['_CRASHARGS']._serialized_end=43
  _globals['_CRASHRETURN']._serialized_start=45
  _globals['_CRASHRETURN']._serialized_end=58
  _globals['_GETTRACECONFIGARGS']._serialized_start=60
  _globals['_GETTRACECONFIGARGS']._serialized_end=80
  _globals['_GETTRACECONFIGRETURN']._serialized_start=82
  _globals['_GETTRACECONFIGRETURN']._serialized_end=202
  _globals['_GETTRACECONFIGRETURN_CONFIGENTRY']._serialized_start=157
  _globals['_GETTRACECONFIGRETURN_CONFIGENTRY']._serialized_end=202
  _globals['_STARTSPANARGS']._serialized_start=205
  _globals['_STARTSPANARGS']._serialized_end=535
  _globals['_DISTRIBUTEDHTTPHEADERS']._serialized_start=537
  _globals['_DISTRIBUTEDHTTPHEADERS']._serialized_end=597
  _globals['_SPANLINK']._serialized_start=599
  _globals['_SPANLINK']._serialized_end=720
  _globals['_HEADERTUPLE']._serialized_start=722
  _globals['_HEADERTUPLE']._serialized_end=763
  _globals['_STARTSPANRETURN']._serialized_start=765
  _globals['_STARTSPANRETURN']._serialized_end=817
  _globals['_INJECTHEADERSARGS']._serialized_start=819
  _globals['_INJECTHEADERSARGS']._serialized_end=855
  _globals['_INJECTHEADERSRETURN']._serialized_start=857
  _globals['_INJECTHEADERSRETURN']._serialized_end=947
  _globals['_FINISHSPANARGS']._serialized_start=949
  _globals['_FINISHSPANARGS']._serialized_end=977
  _globals['_FINISHSPANRETURN']._serialized_start=979
  _globals['_FINISHSPANRETURN']._serialized_end=997
  _globals['_SPANGETCURRENTARGS']._serialized_start=999
  _globals['_SPANGETCURRENTARGS']._serialized_end=1019
  _globals['_SPANGETCURRENTRETURN']._serialized_start=1021
  _globals['_SPANGETCURRENTRETURN']._serialized_end=1078
  _globals['_SPANGETNAMEARGS']._serialized_start=1080
  _globals['_SPANGETNAMEARGS']._serialized_end=1114
  _globals['_SPANGETNAMERETURN']._serialized_start=1116
  _globals['_SPANGETNAMERETURN']._serialized_end=1149
  _globals['_SPANGETRESOURCEARGS']._serialized_start=1151
  _globals['_SPANGETRESOURCEARGS']._serialized_end=1189
  _globals['_SPANGETRESOURCERETURN']._serialized_start=1191
  _globals['_SPANGETRESOURCERETURN']._serialized_end=1232
  _globals['_SPANGETMETAARGS']._serialized_start=1234
  _globals['_SPANGETMETAARGS']._serialized_end=1281
  _globals['_SPANGETMETARETURN']._serialized_start=1283
  _globals['_SPANGETMETARETURN']._serialized_end=1327
  _globals['_SPANGETMETRICARGS']._serialized_start=1329
  _globals['_SPANGETMETRICARGS']._serialized_end=1378
  _globals['_SPANGETMETRICRETURN']._serialized_start=1380
  _globals['_SPANGETMETRICRETURN']._serialized_end=1416
  _globals['_SPANSETMETAARGS']._serialized_start=1418
  _globals['_SPANSETMETAARGS']._serialized_end=1480
  _globals['_SPANSETMETARETURN']._serialized_start=1482
  _globals['_SPANSETMETARETURN']._serialized_end=1501
  _globals['_SPANSETMETRICARGS']._serialized_start=1503
  _globals['_SPANSETMETRICARGS']._serialized_end=1567
  _globals['_SPANSETMETRICRETURN']._serialized_start=1569
  _globals['_SPANSETMETRICRETURN']._serialized_end=1590
  _globals['_SPANSETERRORARGS']._serialized_start=1592
  _globals['_SPANSETERRORARGS']._serialized_end=1719
  _globals['_SPANSETERRORRETURN']._serialized_start=1721
  _globals['_SPANSETERRORRETURN']._serialized_end=1741
  _globals['_SPANSETRESOURCEARGS']._serialized_start=1743
  _globals['_SPANSETRESOURCEARGS']._serialized_end=1799
  _globals['_SPANSETRESOURCERETURN']._serialized_start=1801
  _globals['_SPANSETRESOURCERETURN']._serialized_end=1824
  _globals['_SPANADDLINKARGS']._serialized_start=1826
  _globals['_SPANADDLINKARGS']._serialized_end=1890
  _globals['_SPANADDLINKRETURN']._serialized_start=1892
  _globals['_SPANADDLINKRETURN']._serialized_end=1911
  _globals['_HTTPREQUESTARGS']._serialized_start=1913
  _globals['_HTTPREQUESTARGS']._serialized_end=2015
  _globals['_HTTPREQUESTRETURN']._serialized_start=2017
  _globals['_HTTPREQUESTRETURN']._serialized_end=2057
  _globals['_FLUSHSPANSARGS']._serialized_start=2059
  _globals['_FLUSHSPANSARGS']._serialized_end=2075
  _globals['_FLUSHSPANSRETURN']._serialized_start=2077
  _globals['_FLUSHSPANSRETURN']._serialized_end=2095
  _globals['_FLUSHTRACESTATSARGS']._serialized_start=2097
  _globals['_FLUSHTRACESTATSARGS']._serialized_end=2118
  _globals['_FLUSHTRACESTATSRETURN']._serialized_start=2120
  _globals['_FLUSHTRACESTATSRETURN']._serialized_end=2143
  _globals['_OTELSTARTSPANARGS']._serialized_start=2146
  _globals['_OTELSTARTSPANARGS']._serialized_end=2524
  _globals['_OTELSTARTSPANRETURN']._serialized_start=2526
  _globals['_OTELSTARTSPANRETURN']._serialized_end=2582
  _globals['_OTELENDSPANARGS']._serialized_start=2584
  _globals['_OTELENDSPANARGS']._serialized_end=2651
  _globals['_OTELENDSPANRETURN']._serialized_start=2653
  _globals['_OTELENDSPANRETURN']._serialized_end=2672
  _globals['_OTELFORCEFLUSHARGS']._serialized_start=2674
  _globals['_OTELFORCEFLUSHARGS']._serialized_end=2711
  _globals['_OTELFORCEFLUSHRETURN']._serialized_start=2713
  _globals['_OTELFORCEFLUSHRETURN']._serialized_end=2752
  _globals['_OTELFLUSHSPANSARGS']._serialized_start=2754
  _globals['_OTELFLUSHSPANSARGS']._serialized_end=2791
  _globals['_OTELFLUSHSPANSRETURN']._serialized_start=2793
  _globals['_OTELFLUSHSPANSRETURN']._serialized_end=2832
  _globals['_OTELFLUSHTRACESTATSARGS']._serialized_start=2834
  _globals['_OTELFLUSHTRACESTATSARGS']._serialized_end=2859
  _globals['_OTELFLUSHTRACESTATSRETURN']._serialized_start=2861
  _globals['_OTELFLUSHTRACESTATSRETURN']._serialized_end=2888
  _globals['_OTELSTOPTRACERARGS']._serialized_start=2890
  _globals['_OTELSTOPTRACERARGS']._serialized_end=2910
  _globals['_OTELSTOPTRACERRETURN']._serialized_start=2912
  _globals['_OTELSTOPTRACERRETURN']._serialized_end=2934
  _globals['_OTELISRECORDINGARGS']._serialized_start=2936
  _globals['_OTELISRECORDINGARGS']._serialized_end=2974
  _globals['_OTELISRECORDINGRETURN']._serialized_start=2976
  _globals['_OTELISRECORDINGRETURN']._serialized_end=3021
  _globals['_OTELSPANCONTEXTARGS']._serialized_start=3023
  _globals['_OTELSPANCONTEXTARGS']._serialized_end=3061
  _globals['_OTELSPANCONTEXTRETURN']._serialized_start=3063
  _globals['_OTELSPANCONTEXTRETURN']._serialized_end=3179
  _globals['_OTELSPANGETCURRENTARGS']._serialized_start=3181
  _globals['_OTELSPANGETCURRENTARGS']._serialized_end=3205
  _globals['_OTELSPANGETCURRENTRETURN']._serialized_start=3207
  _globals['_OTELSPANGETCURRENTRETURN']._serialized_end=3268
  _globals['_OTELSETSTATUSARGS']._serialized_start=3270
  _globals['_OTELSETSTATUSARGS']._serialized_end=3341
  _globals['_OTELSETSTATUSRETURN']._serialized_start=3343
  _globals['_OTELSETSTATUSRETURN']._serialized_end=3364
  _globals['_OTELSETNAMEARGS']._serialized_start=3366
  _globals['_OTELSETNAMEARGS']._serialized_end=3414
  _globals['_OTELSETNAMERETURN']._serialized_start=3416
  _globals['_OTELSETNAMERETURN']._serialized_end=3435
  _globals['_OTELSETATTRIBUTESARGS']._serialized_start=3437
  _globals['_OTELSETATTRIBUTESARGS']._serialized_end=3510
  _globals['_OTELSETATTRIBUTESRETURN']._serialized_start=3512
  _globals['_OTELSETATTRIBUTESRETURN']._serialized_end=3537
  _globals['_OTELADDEVENTARGS']._serialized_start=3539
  _globals['_OTELADDEVENTARGS']._serialized_end=3659
  _globals['_OTELADDEVENTRETURN']._serialized_start=3661
  _globals['_OTELADDEVENTRETURN']._serialized_end=3681
  _globals['_OTELRECORDEXCEPTIONARGS']._serialized_start=3683
  _globals['_OTELRECORDEXCEPTIONARGS']._serialized_end=3775
  _globals['_OTELRECORDEXCEPTIONRETURN']._serialized_start=3777
  _globals['_OTELRECORDEXCEPTIONRETURN']._serialized_end=3804
  _globals['_OTELGETATTRIBUTEARGS']._serialized_start=3806
  _globals['_OTELGETATTRIBUTEARGS']._serialized_end=3858
  _globals['_OTELGETATTRIBUTERETURN']._serialized_start=3860
  _globals['_OTELGETATTRIBUTERETURN']._serialized_end=3909
  _globals['_OTELGETNAMEARGS']._serialized_start=3911
  _globals['_OTELGETNAMEARGS']._serialized_end=3945
  _globals['_OTELGETNAMERETURN']._serialized_start=3947
  _globals['_OTELGETNAMERETURN']._serialized_end=3980
  _globals['_OTELGETLINKSARGS']._serialized_start=3982
  _globals['_OTELGETLINKSARGS']._serialized_end=4017
  _globals['_OTELGETLINKSRETURN']._serialized_start=4019
  _globals['_OTELGETLINKSRETURN']._serialized_end=4065
  _globals['_ATTRIBUTES']._serialized_start=4067
  _globals['_ATTRIBUTES']._serialized_end=4181
  _globals['_ATTRIBUTES_KEYVALSENTRY']._serialized_start=4125
  _globals['_ATTRIBUTES_KEYVALSENTRY']._serialized_end=4181
  _globals['_LISTVAL']._serialized_start=4183
  _globals['_LISTVAL']._serialized_end=4215
  _globals['_ATTRVAL']._serialized_start=4217
  _globals['_ATTRVAL']._serialized_end=4320
  _globals['_STOPTRACERARGS']._serialized_start=4322
  _globals['_STOPTRACERARGS']._serialized_end=4338
  _globals['_STOPTRACERRETURN']._serialized_start=4340
  _globals['_STOPTRACERRETURN']._serialized_end=4358
  _globals['_APMCLIENT']._serialized_start=4361
  _globals['_APMCLIENT']._serialized_end=6504
# @@protoc_insertion_point(module_scope)
