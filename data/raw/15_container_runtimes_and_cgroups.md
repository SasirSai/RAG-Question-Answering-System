# Container Runtimes, Linux Namespaces, and Control Groups (cgroups v2)

## 1. The Anatomy of a Linux Container
A container is not a virtual machine and contains no hypervisor. A container is a standard Linux process isolated from other host processes using kernel-level isolation features: Namespaces (which isolate what a process can see) and Control Groups (cgroups, which restrict what resources a process can consume).

## 2. Linux Namespaces
Linux namespaces partition kernel resources such that each container process perceives its own dedicated instance:
- **PID Namespace:** Isolates the process ID space. The primary container process runs as PID 1 inside the container while possessing a regular PID on the host.
- **NET Namespace:** Provides independent network devices, IP routing tables, port bindings, and iptables/nftables firewall rules.
- **MNT (Mount) Namespace:** Isolates filesystem mount points. Combined with pivot_root, it presents the container with its own isolated root filesystem (/).
- **UTS Namespace:** Isolates hostname and NIS domain names.
- **IPC Namespace:** Isolates inter-process communication resources (POSIX message queues, SysV shared memory).
- **USER Namespace:** Maps UID/GID inside the container to unprivileged UIDs on the host, preventing container breakouts from obtaining root host privileges.

## 3. Control Groups (cgroups v2)
Control groups enforce resource accounting and limits across process hierarchies:
- **cgroups v1 Limitations:** Characterized by multiple orthogonal hierarchies where each controller (memory, cpu, blkio) operated an independent tree, causing race conditions and coordination failures.
- **cgroups v2 Unified Hierarchy:** Replaces orthogonal trees with a single unified process tree where every process belongs to exactly one cgroup.
- **Controllers in cgroups v2:**
  - memory.max: Hard upper limit on memory usage; exceeding triggers the Out-Of-Memory (OOM) killer.
  - memory.high: Throttling threshold that triggers memory reclamation and delays allocations before hitting hard OOM.
  - cpu.max: Enforces quota within a period (e.g., 200000 100000 grants 2 CPU cores per 100ms window).
