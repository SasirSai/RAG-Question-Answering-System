# Distributed Event Streaming: Apache Kafka Architecture

## 1. Fundamentals of Event Streaming
Apache Kafka is a distributed, partitioned, replicated commit-log service designed for high-throughput, low-latency publish-subscribe messaging and event-driven architectures.

## 2. Core Abstractions
- **Record (Message):** A key-value pair with an associated timestamp, headers, and payload.
- **Topic:** A logical stream of records. Topics are subdivided into physical Partitions.
- **Partition:** An ordered, immutable sequence of records continuously appended to a disk-based commit log. Each record in a partition is assigned a sequential 64-bit integer called an Offset.
- **Producer:** Applications that publish messages to Kafka topics. Producers assign messages to partitions either via round-robin, hash of the message key (hash(key) % num_partitions), or custom partitioners.
- **Consumer Group:** A cooperative set of consumer processes that divide topic partitions among themselves. Each partition is assigned to exactly one consumer within a given consumer group at any time, guaranteeing ordered consumption within a partition while scaling read parallelism.

## 3. Storage Internals and Zero-Copy I/O
Kafka achieves massive throughput through mechanical sympathy with disk hardware and operating system page caches:
- **Sequential Disk Writes:** Kafka appends records strictly to the end of partition segment files. Sequential disk writes match or exceed random memory access speeds.
- **Page Cache Reliance:** Kafka avoids holding data in JVM heap memory. It lets the OS page cache manage memory buffers, eliminating garbage collection pauses and serialization overheads.
- **Zero-Copy Network Transfer:** Kafka leverages the Linux sendfile system call to transfer byte streams directly from OS page cache buffers to the network socket descriptor, bypassing user-space copying and context switches entirely.
