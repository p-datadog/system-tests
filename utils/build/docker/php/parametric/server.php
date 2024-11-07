<?php

ini_set("datadog.trace.generate_root_span", "0");
ini_set("datadog.trace.revolt_enabled", "0");

require __DIR__ . "/vendor/autoload.php";

use Amp\ByteStream;
use Amp\Http\Server\DefaultErrorHandler;
use Amp\Http\Server\Request;
use Amp\Http\Server\RequestHandler\ClosureRequestHandler;
use Amp\Http\Server\Response;
use Amp\Http\Server\Router;
use Amp\Http\Server\SocketHttpServer;
use Amp\Log\ConsoleFormatter;
use Amp\Log\StreamHandler;
use DDTrace\Configuration;
use Monolog\Logger;
use Monolog\Processor\PsrLogMessageProcessor;
use OpenTelemetry\API\Trace\Propagation\TraceContextPropagator;
use OpenTelemetry\API\Trace\Span;
use OpenTelemetry\API\Trace\SpanKind;
use OpenTelemetry\API\Trace\StatusCode;
use OpenTelemetry\Context\ScopeInterface;
use OpenTelemetry\SDK\Trace as SDK;
use OpenTelemetry\SDK\Trace\TracerProvider;
use function Amp\trapSignal;

$logHandler = new StreamHandler(ByteStream\getStdout());
$logHandler->pushProcessor(new PsrLogMessageProcessor);
$logHandler->setFormatter(new ConsoleFormatter);
$logger = new Logger('server');
$logger->pushHandler($logHandler);

$server = SocketHttpServer::createForDirectAccess($logger);

$port = getenv('APM_TEST_CLIENT_SERVER_PORT');
$server->expose("0.0.0.0:" . $port);

$errorHandler = new DefaultErrorHandler;

function jsonResponse($array) {
    return new Response(headers: ['content-type' => 'application/json'], body: json_encode($array));
}

function arg($req, $arg) {
    static $buffer = new WeakMap;
    return ($buffer[$req] ??= json_decode($req->getBody()->buffer(), true))[$arg] ?? null;
}

// Source: https://magp.ie/2015/09/30/convert-large-integer-to-hexadecimal-without-php-math-extension/
function largeBaseConvert($numString, $fromBase, $toBase)
{
    $chars = "0123456789abcdefghijklmnopqrstuvwxyz";
    $toString = substr($chars, 0, $toBase);

    $length = strlen($numString);
    $result = '';
    for ($i = 0; $i < $length; $i++) {
        $number[$i] = strpos($chars, $numString[$i]);
    }
    do {
        $divide = 0;
        $newLen = 0;
        for ($i = 0; $i < $length; $i++) {
            $divide = $divide * $fromBase + $number[$i];
            if ($divide >= $toBase) {
                $number[$newLen++] = (int)($divide / $toBase);
                $divide = $divide % $toBase;
            } elseif ($newLen > 0) {
                $number[$newLen++] = 0;
            }
        }
        $length = $newLen;
        $result = $toString[$divide] . $result;
    } while ($newLen != 0);

    return $result;
}

function remappedSpanKind($spanKind) {
    switch ($spanKind) {
        case 1: // SK_INTERNAL
            return SpanKind::KIND_INTERNAL;
        case 2: // SK_SERVER
            return SpanKind::KIND_SERVER;
        case 3: // SK_CLIENT
            return SpanKind::KIND_CLIENT;
        case 4: // SK_PRODUCER
            return SpanKind::KIND_PRODUCER;
        case 5: // SK_CONSUMER
            return SpanKind::KIND_CONSUMER;
        default:
            return null;
    }
}

/** @var \DDTrace\SpanData $closed_spans */
$closed_spans = $spans = [];
/** @var Span[] $otelSpans */
$otelSpans = [];
/** @var ScopeInterface[] $scopes */
$scopes = [];
/** @var ?\DDTrace\SpanData $span */
$activeSpan = null;

$router = new Router($server, $logger, $errorHandler);
$router->addRoute('POST', '/trace/span/start', new ClosureRequestHandler(function (Request $req) use (&$spans, &$activeSpan) {
    if ($parent = arg($req, 'parent_id')) {
        \DDTrace\switch_stack($spans[$parent]);
        \DDTrace\create_stack();
        $span = \DDTrace\start_span();
    } else {
        $span = \DDTrace\start_trace_span();
    }
    $link_from_headers = null;
    $links = [];
    if ($span_links = arg($req, 'links')) {
        foreach ($span_links as $span_link) {
            if ($parent = $span_link["parent_id"]) {
                $links[] = $link = $spans[$parent]->getLink();
                if (isset($span_link["attributes"])) {
                    $link->attributes += $span_link["attributes"];
                }
            } else {
                $link_from_headers = $span_link;
                $headers_link = &$links[];
            }
        }
    }
    if ($headers = arg($req, 'http_headers')) {
        $headers = array_merge(...array_map(fn($h) => [strtolower($h[0]) => $h[1]], $headers));
        $callback = function ($headername) use ($headers) {
            return $headers[$headername] ?? null;
        };
        if ($link_from_headers) {
            $headers_link = \DDTrace\SpanLink::fromHeaders($callback);
            if (isset($link_from_headers["attributes"])) {
                $headers_link->attributes += $link_from_headers["attributes"];
            }
            var_dump($headers_link->samplingPriority);
            \DDTrace\set_priority_sampling($headers_link->samplingPriority);
            $span->meta += $headers_link->extractedAttributes;
        } else {
            \DDTrace\consume_distributed_tracing_headers($callback);
        }
    }
    if ($origin = arg($req, 'origin')) {
        $context = \DDTrace\current_context();
        \DDTrace\set_distributed_tracing_context($context["trace_id"], $context["distributed_tracing_parent_id"] ?? 0, $origin);
    }
    $span->name = arg($req, 'name');
    $service = arg($req, 'service');
    $span->service = !is_null($service) && $service !== '' ? $service : $span->service;
    $span->type = arg($req, 'type');
    $span->resource = arg($req, 'resource');
    $span->links = $links;

    if (\dd_trace_env_config("DD_TRACE_ENABLED")) {
        $spanId = $span->id;
    } else {
        // Workaround for error "Typed property DDTrace\SpanData::$id must not be accessed before initialization"
        // when tracing is disabled. In this case, the tracer creates only a "dummy" span without an "id".
        $spanId = 42;
    }

    $spans[$spanId] = $span;
    $activeSpan = $span;
    return jsonResponse([
        "span_id" => $spanId,
        "trace_id" => \DDTrace\trace_id(),
    ]);
}));
$router->addRoute('POST', '/trace/span/inject_headers', new ClosureRequestHandler(function (Request $req) use (&$spans) {
    $span = $spans[arg($req, 'span_id')];
    \DDTrace\switch_stack($span);
    $headers = \DDTrace\generate_distributed_tracing_headers();
    return jsonResponse(["http_headers" => array_map(null, array_keys($headers), $headers)]);
}));
$router->addRoute('POST', '/trace/span/set_resource', new ClosureRequestHandler(function (Request $req) use (&$spans) {
    $span = $spans[arg($req, 'span_id')];
    $span->resource = arg($req, 'resource');
    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/span/set_meta', new ClosureRequestHandler(function (Request $req) use (&$spans) {
    $span = $spans[arg($req, 'span_id')];
    if (is_null(arg($req, 'value'))) {
        unset($span->meta[arg($req, 'key')]);
    } else {
        $span->meta[arg($req, 'key')] = arg($req, 'value');
    }
    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/span/set_metric', new ClosureRequestHandler(function (Request $req) use (&$spans) {
    $span = $spans[arg($req, 'span_id')];
    if (is_null(arg($req, 'value'))) {
        unset($span->metrics[arg($req, 'key')]);
    } else {
        $span->metrics[arg($req, 'key')] = arg($req, 'value');
    }
    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/span/error', new ClosureRequestHandler(function (Request $req) use (&$spans) {
    $span = $spans[arg($req, 'span_id')];
    $span->meta['error.msg'] = arg($req, 'message');
    $span->meta['error.type'] = arg($req, 'type');
    $span->meta['error.stack'] = arg($req, 'stack');
    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/span/add_event', new ClosureRequestHandler(function (Request $req) use (&$spans, &$closed_spans) {
    $span = $spans[arg($req, 'span_id')];
    $name = arg($req, 'name');
    $attributes = arg($req, 'attributes');
    $timestamp = arg($req, 'timestamp');

    $event = new \DDTrace\SpanEvent($name, $attributes, $timestamp * 1000);
    $span->events[] = $event;

    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/span/add_link', new ClosureRequestHandler(function (Request $req) use (&$spans, &$closed_spans) {
    $span = $spans[arg($req, 'span_id')];
    $parent_id = arg($req, 'parent_id');
    $httpHeaders = arg($req, 'http_headers');
    if (isset($spans[$parent_id]) || isset($closed_spans[$parent_id])) {
        $link = ($spans[$parent_id] ?? $closed_spans[$parent_id])->getLink();
        $link->attributes += arg($req, "attributes") ?? [];
    } elseif ($httpHeaders) {
        $httpHeaders = array_merge(...array_map(fn($h) => [strtolower($h[0]) => $h[1]], $httpHeaders));
        $callback = function ($headername) use ($httpHeaders) {
            return $httpHeaders[$headername] ?? null;
        };
        $link = \DDTrace\SpanLink::fromHeaders($callback);
        $link->attributes += arg($req, "attributes") ?? [];
    } else {
        $link = new \DDTrace\SpanLink();
        $link->spanId = arg($req, 'parent_id');
        $link->attributes = arg($req, 'attributes') ?? [];
    }

    $span->links[] = $link;
    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/span/finish', new ClosureRequestHandler(function (Request $req) use (&$spans, &$closed_spans, &$activeSpan) {
    $span_id = arg($req, 'span_id');

    if (!isset($spans[$span_id])) {
        return jsonResponse([]);
    }

    $span = $spans[$span_id];
    \DDTrace\switch_stack($span);
    \DDTrace\close_span();
    $closed_spans[$span_id] = $span;
    unset($spans[$span_id]);

    $activeSpan = $span->parent ?? end($spans) ?? null;

    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/span/flush', new ClosureRequestHandler(function () use (&$spans) {
    \DDTrace\flush();
    dd_trace_internal_fn("synchronous_flush");
    return jsonResponse([]);
}));
$router->addRoute('GET', '/trace/span/current', new ClosureRequestHandler(function () use (&$spans, &$activeSpan) {
    $span = $activeSpan;

    if ($span instanceof \DDTrace\RootSpanData) {
        $payload = [
            "span_id" => $span->id,
            "trace_id" => $span->traceId,
        ];
    } elseif ($span instanceof \DDTrace\SpanData) {
        $rootSpan = $span;
        while ($rootSpan && !$rootSpan instanceof \DDTrace\RootSpanData && $rootSpan->parent) {
            $rootSpan = $rootSpan->parent;
        }
        $payload = [
            "span_id" => $span->id,
            "trace_id" => $rootSpan->traceId,
        ];
    } else {
        $payload = [];
    }

    return jsonResponse($payload);
}));
$router->addRoute('POST', '/trace/otel/start_span', new ClosureRequestHandler(function (Request $req) use (&$spans, &$otelSpans, &$scopes, &$activeSpan) {
    $name = arg($req, 'name');
    $timestamp = arg($req, 'timestamp');
    $spanKind = arg($req, 'span_kind');
    $parentId = arg($req, 'parent_id');
    $httpHeaders = arg($req, 'http_headers');
    $attributes = arg($req, 'attributes');

    $tracer = (new TracerProvider())->getTracer('OpenTelemetry.PHPTestTracer');

    $spanBuilder = $tracer->spanBuilder($name);
    if ($parentId) {
        if (isset($otelSpans[$parentId])) {
            $parentSpan = $otelSpans[$parentId];
        } elseif (isset($spans[$parentId])) {
            $parentSpan = $spans[$parentId];

            // Reconcile the stack
            \DDTrace\switch_stack($parentSpan);
            $parentSpan = Span::getCurrent();
            $otelSpans[$parentId] = $parentSpan;
        } else {
            return jsonResponse([]);
        }

        /** @var ?Span $parentSpan */
        $contextWithParentSpan = $parentSpan->storeInContext(OpenTelemetry\Context\Context::getRoot());
        $spanBuilder->setParent($contextWithParentSpan);
    }

    $spanKind = remappedSpanKind($spanKind);
    if ($spanKind !==  null) {
        $spanBuilder->setSpanKind($spanKind);
    }

    if ($timestamp) {
        $spanBuilder->setStartTimestamp($timestamp * 1000); // ms -> ns
    }

    $links = [];
    if ($span_links = arg($req, 'links')) {
        foreach ($span_links as $span_link) {
            $span_link_attributes = isset($span_link["attributes"]) ? $span_link["attributes"] : [];
            if ($span_link_parent_id = $span_link["parent_id"]) {
                $span_context = $otelSpans[$span_link_parent_id]->getContext();
                $spanBuilder->addLink($span_context, $span_link_attributes);
            } else if ($span_link_http_headers = $span_link["http_headers"]) {
                $carrier = [];
                foreach ($span_link_http_headers as $span_link_http_header) {
                    $carrier[$span_link_http_header[0]] = $span_link_http_header[1];
                }

                $callback = function ($headername) use ($carrier) {
                    return $carrier[$headername] ?? null;
                };
                $headers_link = \DDTrace\SpanLink::fromHeaders($callback);

                $linkSpanContext = \OpenTelemetry\API\Trace\SpanContext::create(
                    $headers_link->traceId,
                    $headers_link->spanId,
                    \OpenTelemetry\API\Trace\TraceFlags::DEFAULT, // trace flags are not currently embedded into the native span link
                    new \OpenTelemetry\API\Trace\TraceState($headers_link->traceState ?? null),
                );

                $spanBuilder->addLink($linkSpanContext, $span_link_attributes);
            }
        }
    }

    if ($httpHeaders) {
        $carrier = [];
        foreach ($httpHeaders as $headers) {
            $carrier[$headers[0]] = $headers[1];
        }
        $remoteContext = TraceContextPropagator::getInstance()->extract($carrier);
        $spanBuilder->setParent($remoteContext);
    }

    if ($attributes) {
        $spanBuilder->setAttributes($attributes);
    }

    /** @var SDK\Span $span */
    $span = $spanBuilder->startSpan();
    $spanId = largeBaseConvert($span->getContext()->getSpanId(), 16, 10);
    $traceId = largeBaseConvert($span->getContext()->getTraceId(), 16, 10);
    $scopes[$spanId] = $span->activate();
    $otelSpans[$spanId] = $span;
    $spans[$spanId] = $span->getDDSpan();
    $activeSpan = $span->getDDSpan();

    return jsonResponse([
        'span_id' => $spanId,
        'trace_id' => $traceId
    ]);
}));
$router->addRoute('POST', '/trace/otel/end_span', new ClosureRequestHandler(function (Request $req) use (&$spans, &$otelSpans, &$closed_spans, &$scopes, &$activeSpan) {
    $spanId = arg($req, 'id');
    $timestamp = arg($req, 'timestamp');

    /** @var ?Span $span */
    $span = $otelSpans[$spanId];
    if ($span) {
        $scope = $scopes[$spanId];
        $scope?->detach();
        $span->end($timestamp ? $timestamp * 1000 : null);
        $ddSpan = $span->getDDSpan();
        unset($spans[$spanId]);
        $activeSpan = $ddSpan->parent ?? end($spans) ?? null;
        $closed_spans[$spanId] = $ddSpan;
    }

    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/otel/set_attributes', new ClosureRequestHandler(function (Request $req) use (&$otelSpans) {
    $spanId = arg($req, 'span_id');
    $attributes = arg($req, 'attributes');

    /** @var ?Span $span */
    $span = $otelSpans[$spanId];
    if ($span) {
        $span->setAttributes($attributes);
    }

    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/otel/set_name', new ClosureRequestHandler(function (Request $req) use (&$otelSpans) {
    $spanId = arg($req, 'span_id');
    $name = arg($req, 'name');

    /** @var ?Span $span */
    $span = $otelSpans[$spanId];
    if ($span) {
        $span->updateName($name);
    }

    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/otel/set_status', new ClosureRequestHandler(function (Request $req) use (&$otelSpans) {
    $spanId = arg($req, 'span_id');
    $code = arg($req, 'code');
    $description = arg($req, 'description');

    switch ($code) {
        case 'UNSET':
            $code = StatusCode::STATUS_UNSET;
            break;
        case 'OK':
            $code = StatusCode::STATUS_OK;
            break;
        case 'ERROR':
            $code = StatusCode::STATUS_ERROR;
            break;
    }

    /** @var ?Span $span */
    $span = $otelSpans[$spanId];
    $span?->setStatus($code, $description);

    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/otel/flush', new ClosureRequestHandler(function (Request $req) {
    \DDTrace\flush();
    dd_trace_internal_fn("synchronous_flush");
     return jsonResponse([
         'success' => true
     ]);
}));
$router->addRoute('POST', '/trace/otel/is_recording', new ClosureRequestHandler(function (Request $req) use (&$otelSpans) {
    $spanId = arg($req, 'span_id');

    /** @var ?Span $span */
    $span = $otelSpans[$spanId];
    if ($span) {
        return jsonResponse([
            'is_recording' => $span->isRecording()
        ]);
    }

    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/otel/span_context', new ClosureRequestHandler(function (Request $req) use (&$otelSpans) {
    $spanId = arg($req, 'span_id');

    /** @var ?SDK\Span $span */
    $span = $otelSpans[$spanId];
    if ($span) {
        $spanContext = $span->getContext();

        return jsonResponse([
            'trace_id' => $spanContext->getTraceId(),
            'span_id' => $spanContext->getSpanId(),
            'trace_flags' => $spanContext->getTraceFlags() ? '01' : '00',
            'trace_state' => (string) $spanContext->getTraceState(), // Implements __toString()
            'remote' => $spanContext->isRemote()
        ]);
    }

    return jsonResponse([]);
}));
$router->addRoute('GET', '/trace/otel/current_span', new ClosureRequestHandler(function (Request $req) use (&$otelSpans, &$spans, &$activeSpan) {
    \DDTrace\switch_stack($activeSpan);
    $span = Span::getCurrent();
    $otelSpanId = $span->getContext()->getSpanId();
    $otelTraceId = $span->getContext()->getTraceId();
    $spanId = largeBaseConvert($otelSpanId, 16, 10);
    $traceId = largeBaseConvert($otelTraceId, 16, 10);

    if ($otelSpanId !== \OpenTelemetry\API\Trace\SpanContextValidator::INVALID_SPAN && $otelTraceId !== \OpenTelemetry\API\Trace\SpanContextValidator::INVALID_TRACE) {
        $otelSpans[$spanId] = $span;
    }

    return jsonResponse([
        'span_id' => (string)$spanId,
        'trace_id' => (string)$traceId,
    ]);
}));
$router->addRoute('POST', '/trace/otel/add_event', new ClosureRequestHandler(function (Request $req) use (&$otelSpans) {
    $spanId = arg($req, 'span_id');
    $name = arg($req, 'name');
    $attributes = arg($req, 'attributes');
    $timestamp = arg($req, 'timestamp');

    /** @var ?SDK\Span $span */
    $span = $otelSpans[$spanId];

    if ($span) {
        $span->addEvent($name, $attributes ?? [], (int)($timestamp * 1000));
    }

    return jsonResponse([]);
}));
$router->addRoute('POST', '/trace/otel/record_exception', new ClosureRequestHandler(function (Request $req) use (&$otelSpans) {
    $spanId = arg($req, 'span_id');
    $message = arg($req, 'message');
    $attributes = arg($req, 'attributes');

    /** @var ?SDK\Span $span */
    $span = $otelSpans[$spanId];

    if ($span) {
        $span->recordException(new \Exception($message), $attributes ?? []);
    }

    return jsonResponse([]);
}));
$router->addRoute('GET', '/trace/config', new ClosureRequestHandler(function (Request $req) {

    $tags_array = \dd_trace_env_config("DD_TAGS");
    $propagation_array = \dd_trace_env_config("DD_TRACE_PROPAGATION_STYLE");

    $config_tags = [];
    $config_propagation = "";

    if (!empty($tags_array)) {
        $callback = fn(string $k, string $v): string => "$k:$v";
        $config_tags = array_map($callback, array_keys($tags_array), array_values($tags_array));
    }

    if (!empty($propagation_array)) {
        $config_propagation = implode(",", array_keys($propagation_array));
    }

    $config = array(
        'dd_service' => trim(var_export(\dd_trace_env_config("DD_SERVICE"), true), "'"),
        'dd_env' => trim(var_export(\dd_trace_env_config("DD_ENV"), true), "'"),
        'dd_version' => trim(var_export(\dd_trace_env_config("DD_VERSION"), true), "'"),
        'dd_trace_sample_rate' => var_export(\dd_trace_env_config("DD_TRACE_SAMPLE_RATE"), true),
        'dd_trace_enabled' => var_export(\dd_trace_env_config("DD_TRACE_ENABLED"), true),
        'dd_runtime_metrics_enabled' => 'false', // PHP doesn't implement DD_RUNTIME_METRICS_ENABLED
        'dd_tags' => $config_tags,
        'dd_trace_propagation_style' => $config_propagation,
        'dd_trace_debug' => var_export(\dd_trace_env_config("DD_TRACE_DEBUG"), true),
        'dd_trace_otel_enabled' => var_export(\dd_trace_env_config("DD_TRACE_OTEL_ENABLED"), true),
        'dd_log_level' => trim(var_export(\dd_trace_env_config("DD_TRACE_LOG_LEVEL"), true), "'"),
        'dd_trace_agent_url' => trim(var_export(\dd_trace_env_config("DD_TRACE_AGENT_URL"), true), "'"),
    );
    return jsonResponse(array(
        'config' => $config
    ));

}));
$router->addRoute('GET', '/trace/crash', new ClosureRequestHandler(function (Request $req) use (&$otelSpans) {
    posix_kill(posix_getpid(), 11);

    return jsonResponse([]);
}));
$server->start($router, $errorHandler);

$signal = trapSignal([SIGINT, SIGTERM]);
$logger->info("Caught signal $signal, stopping server");

$server->stop();
