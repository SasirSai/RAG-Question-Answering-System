# Two-Phase Commit (2PC) and Distributed Transactions

## 1. Problem Statement: Atomic Commitment
In distributed database architectures partitioned across multiple physical shards, a single transaction may require updates on distinct machines. The Two-Phase Commit protocol (2PC) guarantees the Atomicity and Durability properties across all participating nodes: either all participants commit their local updates, or all participants abort and roll back to their pre-transaction state.

## 2. Protocol Participants
- **Coordinator:** The centralized manager or transaction coordinator that orchestrates the execution and final resolution of the transaction.
- **Participants (Cohorts):** The database nodes that manage local partitions and execute resource writes.

## 3. Phase Breakdown
### Phase 1: Prepare (Voting Phase)
1. The coordinator writes a START_2PC record to its write-ahead log (WAL) and transmits a PREPARE request to all transaction cohorts.
2. Each cohort executes the transaction operations locally up to the point of commit, acquires necessary locks, and forces local redo and undo logs to stable non-volatile storage.
3. If the local preparation succeeds, the cohort writes a VOTE_COMMIT record to its local WAL and replies VOTE_COMMIT to the coordinator. If it cannot prepare (due to deadlocks, integrity violations, or disk faults), it writes VOTE_ABORT and transmits VOTE_ABORT.

### Phase 2: Commit / Abort (Decision Phase)
1. If the coordinator receives unanimous VOTE_COMMIT messages from every cohort, it writes a GLOBAL_COMMIT record to its WAL and broadcasts GLOBAL_COMMIT to all cohorts.
2. Upon receiving GLOBAL_COMMIT, each cohort releases locks, marks the local transaction committed, and sends an ACK response back.
3. If any cohort voted VOTE_ABORT or if a network timeout occurred before all votes were collected, the coordinator writes GLOBAL_ABORT to its WAL and broadcasts GLOBAL_ABORT to all cohorts.

## 4. The Blocking Problem and Failure Modes
The primary vulnerability of standard 2PC is that it is an inherently blocking protocol. If the coordinator crashes after cohorts have voted VOTE_COMMIT but before broadcasting GLOBAL_COMMIT, cohorts are left in an indeterminate prepared state. They cannot unilaterally abort (because the coordinator might have decided commit) nor can they unilaterally commit (because another cohort might have aborted). Resources remain locked indefinitely until coordinator recovery.
