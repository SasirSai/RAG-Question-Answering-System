# API Rate Limiting: Algorithms and Distributed Implementation

## 1. Why Rate Limit?
Rate limiting protects distributed APIs against denial-of-service (DoS) attacks, brute-force credential stuffing, resource starvation, and cascading failures caused by runaway client processes.

## 2. Classical Rate Limiting Algorithms
1. **Token Bucket:**
   - A bucket holds up to a maximum capacity of b tokens.
   - Tokens are replenished at a constant rate of r tokens per second.
   - Each incoming request consumes 1 token. If the bucket has available tokens, the request is admitted; otherwise, it is rejected with HTTP 429 Too Many Requests.
   - Allows bursts of up to b requests while constraining long-term rate to r.
2. **Leaky Bucket:**
   - Incoming requests enter a FIFO queue of fixed capacity.
   - Requests leak out of the queue and execute at a constant, smooth rate.
   - Excess requests arriving when the queue is full are discarded. Eliminates bursts and guarantees smooth output traffic.
3. **Fixed Window Counter:**
   - Divides time into fixed windows (e.g., 60 seconds). Each window maintains an integer counter.
   - Vulnerable to boundary traffic bursts: twice the rate limit can pass within a short window centered on the boundary (e.g. at second 59 and second 61).
4. **Sliding Window Log:**
   - Records the timestamp of every request in a sorted set (e.g., Redis ZSET).
   - When a request arrives, all timestamps older than now - window_size are purged. The cardinality of the remaining set determines whether the request is allowed.
   - Perfectly accurate but consumes significant memory for high-volume endpoints.
5. **Sliding Window Counter:**
   - Blends fixed window counters by weighting the previous window's count proportionally to elapsed time in the current window: count = current_count + previous_count * (1 - time_into_current / window_size). Memory efficient and smooth.
