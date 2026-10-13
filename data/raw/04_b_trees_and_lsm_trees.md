# Storage Engine Internals: B+ Trees versus Log-Structured Merge Trees

## 1. Introduction to Storage Engines
Storage engines form the underlying storage subsystem of relational and NoSQL databases. The two prevailing data structures for persistent index storage on disk and solid-state drives are the classical B+ Tree (employed by PostgreSQL, MySQL InnoDB, and SQLite) and the Log-Structured Merge-tree (LSM-tree, employed by RocksDB, Apache Cassandra, and Google Bigtable).

## 2. B+ Tree Architecture
A B+ Tree is a self-balancing, multi-way search tree characterized by a high branching factor (fanout, typically between 100 and 500).
- **Internal Nodes:** Store routing keys and child pointers to guide search navigation. Internal nodes contain no data records.
- **Leaf Nodes:** Store actual data records or tuple pointers, ordered contiguously by primary key. Leaf nodes are doubly linked sequentially, enabling efficient range scans.
- **Update Behavior:** B+ Trees perform in-place updates. Modifying a record involves reading the target 4KB-16KB page into memory, mutating the page in buffer cache, and writing it back to disk. Random writes incur high random I/O overhead on rotating disks and exacerbate write amplification on flash memory.

## 3. Log-Structured Merge-Tree (LSM-Tree) Architecture
LSM-trees trade off read performance to achieve exceptional sequential write throughput by appending all mutations sequentially:
- **MemTable:** An in-memory write buffer (typically implemented as a concurrent SkipList or Red-Black Tree). All inserts, updates, and deletes (represented as tombstone markers) are appended to an on-disk Write-Ahead Log (WAL) and inserted into the MemTable.
- **Immutable MemTable & Flushing:** Once the MemTable reaches a configured size threshold (typically 32MB to 64MB), it is converted to an immutable MemTable and flushed sequentially to Level 0 (L0) as a Sorted String Table (SSTable) file.
- **SSTable Structure:** SSTables are immutable disk files containing sorted key-value pairs along with a Bloom filter and a sparse block index.

## 4. Compaction Strategies: Size-Tiered vs Leveled
Because SSTables are immutable, outdated keys and tombstones accumulate across files. Compaction processes merge and reconcile SSTables:
- **Size-Tiered Compaction:** Groups SSTables of roughly equal size into tiers and merges them when a tier count threshold is met. Offers high write throughput but high temporary disk space requirements.
- **Leveled Compaction:** Organizes data into exponential levels (L0, L1, L2...). Each level (from L1 upwards) contains strictly non-overlapping key ranges. Provides bounded read latency and lower space amplification.
