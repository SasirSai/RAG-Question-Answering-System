# Distributed Caching: Topologies, Eviction Policies, and Invalidation

## 1. Role of In-Memory Caching
Distributed caches such as Redis and Memcached store hot data in high-speed RAM to decouple database read capacity from traffic volume, reducing query latency from milliseconds to microseconds.

## 2. Cache Topologies
1. **Cache-Aside (Lazy Loading):** The application first queries the cache. On a cache hit, the data is returned immediately. On a cache miss, the application queries the backing database, populates the cache with the fetched record, and returns the result. This prevents cache bloat with unrequested data.
2. **Read-Through:** The application interacts solely with the cache abstraction. On a miss, the cache infrastructure itself fetches from the primary database, populates its store, and returns the value.
3. **Write-Through:** The application writes to the cache, which synchronously persists the mutation to the backing database before acknowledging completion. Guarantees strong consistency between cache and DB at the expense of higher write latency.
4. **Write-Behind (Write-Back):** Writes are acknowledged as soon as they are written to the cache. The cache asynchronously batches and flushes mutations to the database. Risk of data loss if the cache node crashes before flushing.

## 3. Eviction Strategies
When RAM capacity is saturated, the cache must evict entries according to an eviction policy:
- **LRU (Least Recently Used):** Evicts items that have not been accessed for the longest duration. Implemented using a doubly linked list coupled with a hash map for O(1) access and update.
- **LFU (Least Frequently Used):** Tracks access frequency counters; evicts items with the lowest access count. Solves the scan-resistance problem where a one-off batch scan flushes active working sets out of an LRU cache.
- **FIFO (First-In, First-Out):** Evicts items in the strict chronological order of insertion regardless of frequency or recency.

## 4. Cache Stampede and Dogpiling Mitigation
A cache stampede (or thundering herd) occurs when a high-traffic cache key expires, causing hundreds of concurrent requests to simultaneously miss and execute expensive database queries. Solutions include:
- **Mutex / Distributed Lock:** Only the first thread that experiences a cache miss acquires a lock to regenerate the value, while subsequent threads await the result.
- **Probabilistic Early Expiration (XFetch):** Background recomputation starts prior to true expiration based on access probability and remaining TTL.
