# The Paxos Protocol: Formal Foundations and Multi-Paxos

## 1. Introduction to Paxos
The Paxos protocol, originally published by Leslie Lamport in 1998, represents the foundational theoretical framework for reaching agreement in an asynchronous, fault-tolerant distributed system where processors may fail by stopping and messages may experience arbitrary delays or reordering.

## 2. Roles in Single-Decree Paxos
Single-decree Paxos achieves consensus on a single decision value among participants categorized into three logical roles:
- **Proposers:** Nodes that advocate client proposals by submitting proposal numbers and values.
- **Acceptors:** The consensus memory and voting body that store and accept proposals. A majority quorum of acceptors must agree for a value to be chosen.
- **Learners:** Nodes that observe the agreed outcome and execute the corresponding command against the local state machine.

## 3. Two-Phase Consensus Execution
Single-decree Paxos executes across two sequential phases:
- **Phase 1a (Prepare):** A proposer selects a unique, monotonically increasing proposal number n (where n > any previously seen proposal number) and sends a Prepare(n) message to a majority of acceptors.
- **Phase 1b (Promise):** When an acceptor receives Prepare(n), if n is greater than any proposal number to which it has previously responded, the acceptor returns a Promise message committing never to accept any future proposals numbered less than n, along with the highest-numbered proposal (if any) it has already accepted.
- **Phase 2a (Accept):** If the proposer receives promises from a majority of acceptors, it assigns value v to its proposal. If any acceptor returned an already-accepted value, v must equal the value associated with the highest proposal number reported in the promises. Otherwise, the proposer chooses its own desired value. The proposer broadcasts Accept(n, v) to the acceptors.
- **Phase 2b (Accepted):** An acceptor accepts the proposal (n, v) if and only if it has not promised to only consider proposals numbered strictly greater than n.

## 4. Multi-Paxos and Leader Optimization
Running the full two-phase protocol for every single state machine transaction introduces severe performance penalties (at least two network round-trips). Multi-Paxos optimizes this by electing a stable leader. Once a leader successfully runs Phase 1 across the stream of log instances, subsequent log positions only require Phase 2 (one round trip: Accept and Accepted), cutting consensus overhead in half.
