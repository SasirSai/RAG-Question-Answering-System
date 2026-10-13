# Garbage Collection Algorithms in Managed Runtimes

## 1. Automatic Memory Management
Managed execution runtimes (Java Virtual Machine, Go runtime, .NET CLR, V8 JavaScript engine) manage heap allocation and deallocation automatically, eliminating dangling pointer bugs, double-free crashes, and uninitialized reads.

## 2. Foundational GC Paradigms
- **Reference Counting:** Each heap object contains an integer reference counter incremented when a reference is assigned and decremented when a reference falls out of scope. When the counter reaches zero, the object is immediately reclaimed. Advantage: immediate deterministic reclamation. Disadvantage: inability to handle cyclic object references and high atomic counter update overhead.
- **Tracing Garbage Collection:** Determines live objects by traversing the object graph starting from a set of known GC Roots (thread stack frames, global static variables, CPU registers). Objects unreached during graph traversal are identified as garbage.

## 3. Generational Hypothesis
The Weak Generational Hypothesis states that the vast majority of allocated objects die very shortly after allocation (infant mortality). Consequently, runtimes partition memory into generations:
- **Young Generation (Eden and Survivor spaces):** Freshly allocated objects reside in Eden. Frequent, highly efficient Minor GC cycles scavenge surviving objects into Survivor spaces.
- **Old (Tenured) Generation:** Objects that survive multiple Minor GC collection thresholds are promoted (tenured) to the Old Generation, which is collected much less frequently via Major / Full GC passes.

## 4. Modern Low-Latency Collectors
Modern production JVM collectors (ZGC and Shenandoah) and Go's runtime collector prioritize sub-millisecond stop-the-world (STW) pauses:
- **Concurrent Marking:** Traces the object graph concurrently while application mutator threads continue execution, utilizing read/write barriers and colored pointers.
- **Concurrent Compaction:** Relocates objects to eliminate heap fragmentation concurrently without halting mutator threads.
