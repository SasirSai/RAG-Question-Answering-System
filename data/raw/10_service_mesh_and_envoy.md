# Service Mesh Architecture and Envoy Proxy Internals

## 1. The Microservices Communication Challenge
As monolithic architectures decompose into microservices, operational concerns including service discovery, mutual TLS (mTLS) authentication, traffic shaping, distributed tracing, and fault injection move into the network fabric. A service mesh externalizes these concerns into a dedicated infrastructure layer.

## 2. Architecture: Control Plane vs Data Plane
A service mesh consists of two fundamental components:
- **Data Plane:** High-performance network proxies deployed alongside applications as sidecar containers. All ingress and egress traffic flows through the proxy. Envoy Proxy (written in C++) is the standard data plane implementation.
- **Control Plane:** The centralized management system (e.g., Istio's istiod) that accepts declarative configuration policies, compiles them, and distributes them dynamically to data plane proxies using discovery APIs.

## 3. Envoy Proxy Threading Model
Envoy uses a single-process, multi-threaded event-driven architecture:
- **Main Thread:** Handles server initialization, administrative tasks, and control plane communication via xDS APIs (LDS, RDS, CDS, EDS).
- **Worker Threads:** Envoy spawns one worker thread per CPU core. Each worker thread runs a non-blocking libevent event loop and listens on identical socket ports using SO_REUSEPORT. Connections are bound to a single worker thread for their entire lifecycle, eliminating cross-thread locking and contention.

## 4. Resilience Patterns
- **Circuit Breaking:** Tracks downstream failure rates and immediately opens the circuit to reject calls when thresholds are crossed, protecting failing backends from cascading collapse.
- **Rate Limiting:** Enforces token bucket algorithms either locally per proxy or globally via gRPC rate limiting services.
- **Outlier Detection:** Passively monitors backend responses, ejecting consecutive 5xx hosts from the load balancing pool for a configurable base ejection time.
