# Raft Consensus Protocol: Architecture and Mechanisms

## 1. Overview and Core Philosophy
Raft is a consensus algorithm designed for state machine replication across a cluster of computing nodes. Formulated by Diego Ongaro and John Ousterhout at Stanford University, Raft was developed as an explicit alternative to multi-Paxos, prioritizing understandability, formal decomposability, and verifiable state safety. Raft decomposes consensus into three independent sub-problems: Leader Election, Log Replication, and Safety enforcement.

## 2. Server Roles and State Transitions
At any given instant, each node in a Raft cluster operates in exactly one of three distinct roles: Leader, Follower, or Candidate.
- **Follower:** Followers are completely passive. They issue no remote procedure calls (RPCs) on their own volition. Instead, they respond to incoming RPCs from leaders and candidates. If a follower receives no communication over an election timeout window, it transitions to a candidate.
- **Candidate:** Candidates actively initiate elections. A candidate increments the current term, votes for itself, and broadcasts RequestVote RPCs to all peers.
- **Leader:** The elected leader handles all client interaction, sequences state machine mutations, and replicates log entries across followers via AppendEntries heartbeats.

## 3. Election Mechanics and Split Votes
Elections rely on randomized election timers to mitigate split votes. The election timeout is typically randomized between 150ms and 300ms. When a follower's election timer expires without receiving an AppendEntries heartbeat from a valid leader or granting a vote to a candidate, it increments its current term counter and transitions to Candidate state.
A candidate wins an election if it secures votes from a strict majority (quorum) of cluster nodes for the given term. Specifically, in a cluster of size N, a quorum size of floor(N/2) + 1 is required. Each node may vote for at most one candidate per term on a first-come-first-served basis, conditional on the election safety rule.

## 4. Log Matching Invariant and Safety Rule
Raft maintains the strict Log Matching Property:
1. If two entries in different logs have the same index and term, then they store the identical command.
2. If two entries in different logs have the same index and term, then their logs are identical in all preceding entries.

The election restriction ensures that a candidate cannot win an election unless its log contains all committed entries from prior terms. A voter denies its vote if the candidate's log is less up-to-date than its own log. An entry is defined as committed once it has been successfully replicated to a majority of servers by the leader that created the entry.
