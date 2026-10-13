# The CAP Theorem, PACELC, and Eventual Consistency Models

## 1. The CAP Theorem Formalized
Formulated by Eric Brewer in 2000 and formally proven by Seth Gilbert and Nancy Lynch in 2002, the CAP theorem establishes fundamental trade-offs in distributed data stores under asynchronous network conditions:
- **Consistency (Linearizability):** Every read operation receives the most recent write or an error. All operations behave as if executed atomically on a single copy of data.
- **Availability:** Every non-failing node must return a non-error response for every received request, without guarantee of containing the latest write.
- **Partition Tolerance:** The system continues to operate despite an arbitrary number of messages being dropped or delayed by the network between nodes.

Because network partitions (P) are an unavoidable physical reality in distributed environments, distributed systems must choose between Consistency (CP) or Availability (AP) during a partition event.

## 2. The PACELC Theorem
Daniel Abadi extended CAP with PACELC to describe system behavior under normal conditions as well:
- If there is a Partition, how does the system choose between Availability and Consistency?
- Else (when the system is operating normally without partitions), how does the system choose between Latency and Consistency?
For example, MongoDB can be classified as PC/EC, while Cassandra defaults to PA/EL.

## 3. Eventual Consistency and Convergence
In AP systems, replicas do not synchronize synchronously. Instead, they guarantee Eventual Consistency: given no further updates, all replicas will eventually converge to identical values.
- **Read-Your-Writes Consistency:** Ensures a user who updates a record will always observe that update on subsequent reads.
- **Monotonic Read Consistency:** Guarantees that if a client reads a particular value, it will never observe an older, stale version on subsequent queries.
- **Conflict-Free Replicated Data Types (CRDTs):** Mathematical data structures (state-based or operation-based) where concurrent modifications can always be merged deterministically without centralized coordination.
