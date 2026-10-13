# Database Concurrency Control and ANSI SQL Isolation Levels

## 1. Concurrency Anomalies
When concurrent transactions execute against a database without proper isolation, several anomalies can arise:
- **Dirty Read (P1):** Transaction T1 modifies a row. Transaction T2 reads the row before T1 commits. If T1 rolls back, T2 has read uncommitted, invalid state.
- **Non-Repeatable Read (P2 / Fuzzy Read):** Transaction T1 reads a row. Transaction T2 modifies or deletes that row and commits. If T1 re-reads the row, it observes a different value.
- **Phantom Read (P3):** Transaction T1 reads a set of rows satisfying a search condition. Transaction T2 inserts or deletes rows matching that condition and commits. If T1 repeats the query, it observes a different set of rows.
- **Lost Update:** Two transactions concurrently read a value and subsequently update it based on the read value, causing one transaction to overwrite the other without incorporating its changes.

## 2. Standard ANSI SQL Isolation Levels
ANSI SQL-92 defines four isolation levels characterized by which anomalies they prevent:
1. **Read Uncommitted:** Permitted anomalies: Dirty Read, Non-Repeatable Read, Phantom Read.
2. **Read Committed:** Prevents Dirty Reads. Permits Non-Repeatable Reads and Phantom Reads. Commonly the default in PostgreSQL, Oracle, and SQL Server.
3. **Repeatable Read:** Prevents Dirty Reads and Non-Repeatable Reads. Permits Phantom Reads (under pure locking definitions).
4. **Serializable:** Guarantees that the concurrent execution of transactions produces the identical outcome as if they had executed in some strict serial order.

## 3. Multi-Version Concurrency Control (MVCC)
Modern relational databases implement Snapshot Isolation using MVCC rather than heavy read locking. Under MVCC, readers never block writers and writers never block readers. Each transaction observes a consistent snapshot of data corresponding to the transaction's start timestamp.
