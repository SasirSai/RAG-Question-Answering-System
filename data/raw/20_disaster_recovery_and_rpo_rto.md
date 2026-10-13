# Disaster Recovery: RPO, RTO, and Multi-Region Architectures

## 1. Defining Disaster Recovery Metrics
Disaster recovery (DR) planning ensures organizational resilience against catastrophic events such as data center power loss, natural disasters, regional fiber cuts, and ransomware attacks. Two fundamental metrics govern DR requirements:
- **Recovery Point Objective (RPO):** The maximum acceptable age of data files or transactions that must be recovered from backup storage for normal operations to resume if a disaster occurs. RPO dictates acceptable data loss measured in time. An RPO of zero requires synchronous replication across failure domains.
- **Recovery Time Objective (RTO):** The maximum acceptable duration of time that a system can remain offline after a disaster is declared before service availability must be restored. RTO dictates acceptable downtime.

## 2. Multi-Region Resilience Patterns
1. **Backup and Restore (Cold Standby):** Data backups and disk snapshots are periodically replicated to a secondary region. In a disaster, infrastructure is provisioned from scratch and data is restored. Very low cost, but high RTO (hours to days) and RPO determined by snapshot intervals.
2. **Pilot Light:** Critical core infrastructure (database replicas) runs continuously in the secondary region with asynchronous data replication. Compute clusters remain turned off or scaled to zero until disaster declaration. Low cost with moderate RTO (15-30 minutes).
3. **Warm Standby:** A scaled-down but fully functional duplicate environment runs continuously in the secondary region. If the primary fails, the secondary environment scales up its instances and assumes traffic. Low RTO (minutes) and low RPO.
4. **Active-Active (Multi-Region Live-Live):** Multiple geographical regions actively serve live user traffic concurrently. Traffic is dynamically shifted via global DNS or Anycast routing. Zero RTO and near-zero RPO, with high architectural complexity and cross-region consensus requirements.
