# Database Sharding and Replication Strategies

## 1. Scaling Storage Beyond Single Nodes
When dataset volume or write throughput exceeds the physical limits of a single database server, systems employ replication for fault tolerance and read scaling, and sharding (horizontal partitioning) for write and storage scaling.

## 2. Replication Topologies
- **Single-Leader (Primary-Replica):** All mutations (INSERT, UPDATE, DELETE) are directed exclusively to the designated leader node. The leader records writes in its replication stream and forwards changes to replicas. Replicas serve read-only queries.
  - Synchronous Replication: The leader waits for at least one replica to confirm write durability before responding to client. Prevents data loss on leader crash but slows down writes.
  - Asynchronous Replication: The leader acknowledges clients immediately after local commit. Risk of replication lag and data loss if the leader fails before replicating.
- **Multi-Leader (Active-Active):** Multiple nodes accept writes concurrently. Typically utilized across geographically separated data centers. Requires explicit conflict detection and resolution strategies (e.g., Last-Write-Wins or Operational Transformation).
- **Leaderless (Dynamo-Style):** Clients write directly to multiple replicas without a designated coordinator, relying on quorum reads and writes (W + R > N).

## 3. Sharding Strategies
Horizontal sharding breaks a table into distinct partitions called shards, distributed across cluster nodes:
1. **Range-Based Sharding:** Keys are assigned to shards based on continuous ranges (e.g., user_id 1-10000 on Shard A, 10001-20000 on Shard B). Enables efficient range scans but creates write hotspots if keys are monotonically increasing.
2. **Hash-Based Sharding:** A cryptographic hash function (e.g., MurmurHash3) maps keys uniformly across shards (shard = hash(key) % num_shards). Eliminates hotspotting but makes cross-shard range queries inefficient.
3. **Directory-Based Sharding:** A lookup service maps partition keys to physical shards, providing maximum placement flexibility at the cost of an extra lookup indirection.
