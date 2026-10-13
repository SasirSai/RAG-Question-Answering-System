# Raft Log Compaction, Snapshots, and Cluster Membership Changes

## 1. The Need for Log Compaction
In a long-running Raft cluster, the replicated log cannot grow without bound. A continually expanding log consumes excessive disk space and requires increasingly long replay times when a rebooted node catches up. Raft addresses this through incremental snapshotting.

## 2. Snapshotting Mechanics
In Raft snapshotting:
- Each node independently creates a point-in-time snapshot of its state machine, writing the snapshot to non-volatile storage.
- The snapshot records: the state machine data, the last included index (the highest log index applied to the snapshot), and the last included term.
- Once the snapshot is persisted, all log entries up through last_included_index are discarded from the log.
- If a follower lags so far behind that the leader has already discarded the next entry needed by that follower, the leader transmits an InstallSnapshot RPC instead of standard AppendEntries.

## 3. Cluster Membership Changes (Joint Consensus)
Dynamically altering the set of servers in a cluster (adding or removing nodes) is dangerous because separate servers can switch configurations at different times, risking dual conflicting majorities.
- Raft solves configuration transitions using a two-phase Joint Consensus approach:
  1. The leader transitions the cluster into configuration C_old,new which requires separate majorities from both the old configuration C_old and the new configuration C_new for any entry to be committed.
  2. Once C_old,new is committed to both configurations, the leader creates and commits an entry for C_new, completing the transition without any possibility of split-brain decisions.
