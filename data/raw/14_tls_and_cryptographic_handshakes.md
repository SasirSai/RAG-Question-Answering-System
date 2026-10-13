# Transport Layer Security (TLS 1.3) and Cryptographic Handshakes

## 1. Security Goals of TLS
Transport Layer Security (TLS) operates above transport protocols (TCP) to provide three cryptographic guarantees:
- **Confidentiality:** Data is encrypted to prevent eavesdropping by unauthorized third parties.
- **Integrity:** Message Authentication Codes (HMAC) or Authenticated Encryption with Associated Data (AEAD) prevent undetected tampering.
- **Authentication:** Public key certificates verify the identity of the communicating endpoints.

## 2. TLS 1.3 Handshake Architecture
Standardized in RFC 8446, TLS 1.3 reduced handshake latency from two round-trip times (2-RTT in TLS 1.2) to a single round-trip time (1-RTT) by removing legacy cipher suites and redesigning message flows:
1. **ClientHello:** The client transmits supported cipher suites and combines key share generation by guessing the server's key exchange algorithm (supplying Diffie-Hellman parameters upfront).
2. **ServerHello:** The server selects the cipher suite, responds with its own key share, and transmits its digital certificate and CertificateVerify signature.
At this exact moment, both sides compute the shared premaster secret via Elliptic Curve Diffie-Hellman (ECDHE), derive symmetric session keys, and begin exchanging encrypted application data in 1-RTT.

## 3. Zero Round-Trip Time (0-RTT) Resumption
TLS 1.3 introduces 0-RTT resumption for clients that have previously connected to a server:
- During an initial connection, the server provides a Pre-Shared Key (PSK) or Session Ticket.
- On subsequent connections, the client encrypts the very first HTTP request payload using early keys derived from the PSK and sends it alongside ClientHello in the initial TCP flight.
- **Replay Attack Vulnerability:** 0-RTT early data lacks forward secrecy and is vulnerable to replay attacks if an attacker intercepts and resends the early data flight. Therefore, 0-RTT data should only be permitted for idempotent HTTP operations (e.g., GET requests).
