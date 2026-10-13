# Distributed Tracing and OpenTelemetry Standards

## 1. The Observability Triad
Modern cloud-native systems rely on three telemetry pillars: Metrics (aggregable numerical indicators), Logs (timestamped discrete event records), and Traces (end-to-end request lifecycle representations across distributed boundaries).

## 2. Distributed Tracing Model (W3C Trace Context)
A trace visualizes the progression of a request through a distributed network of services:
- **Trace:** A directed acyclic graph (DAG) of Spans representing an end-to-end execution path. Identified by a globally unique 128-bit trace-id.
- **Span:** A single contiguous unit of contiguous work performed by a specific component. A span encapsulates:
  - Span ID (64-bit unique identifier).
  - Parent Span ID (identifies caller span; root spans have no parent).
  - Operation name and start/end timestamps.
  - Attributes (key-value metadata such as http.status_code or db.system).
  - Events (timestamped annotations within the span duration).
  - Status (OK, Error, Unset).

## 3. Context Propagation
To preserve trace continuity across process and network boundaries, tracing contexts must be injected into and extracted from communication wire protocols. The W3C Trace Context recommendation specifies two standard HTTP headers:
- traceparent: Formatted as version-trace_id-parent_id-trace_flags (e.g. 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01).
- tracestate: An opaque vendor-specific list of key-value pairs for propagating vendor metadata across multi-tenant tracing vendors.

## 4. Sampling Strategies
Because collecting 100% of spans in high-throughput systems creates unsustainable network and storage costs, systems deploy sampling:
- **Head-Based Sampling:** The sampling decision is made at the root span when the request first enters the ingress gateway (e.g. probabilistic 1% sampling). Simple and lightweight, but risks dropping rare error traces.
- **Tail-Based Sampling:** Spans are buffered in memory at an OpenTelemetry collector until the entire trace completes. The collector inspects the completed trace and retains it if errors or anomalous latencies are present.
