# Linux epoll and High-Performance I/O Multiplexing

## 1. The C10K Problem and I/O Models
The C10K problem refers to the challenge of managing ten thousand concurrent network connections on a single commodity server. Traditional thread-per-connection architectures fail due to thread stack memory exhaustion and massive operating system scheduler context-switching overheads. Non-blocking asynchronous I/O multiplexing solves this by allowing a single thread to monitor readiness across thousands of file descriptors.

## 2. Evolution: select, poll, and epoll
- **select():** Uses fixed-size bitmasks (fd_set, capped at FD_SETSIZE typically 1024). Requires O(N) linear scanning of the descriptor set on every call and copies the entire descriptor list between user space and kernel space on every invocation.
- **poll():** Replaces fixed bitmasks with an array of pollfd structures, lifting the 1024 descriptor limit. However, it still requires O(N) kernel scanning and complete array copying between user and kernel space.
- **epoll():** Introduces an in-kernel event table managed via three system calls:
  1. epoll_create1(flags): Allocates an epoll file descriptor backed by an in-kernel red-black tree (for storing registered file descriptors) and a ready list (a doubly linked list).
  2. epoll_ctl(epfd, op, fd, event): Adds, modifies, or deletes descriptors in the interest list with O(log N) complexity.
  3. epoll_wait(epfd, events, maxevents, timeout): Suspends caller until events occur. Returns only the file descriptors that are actually ready in O(number of ready events), completely eliminating O(N) scanning.

## 3. Triggering Modes: Level-Triggered vs Edge-Triggered
- **Level-Triggered (LT):** Default mode. epoll_wait reports a file descriptor as long as its buffer contains data to be read. If an application reads only part of the buffer, subsequent calls to epoll_wait will immediately trigger again.
- **Edge-Triggered (ET):** High-performance mode (EPOLLET). epoll_wait reports an event only when the descriptor state changes (e.g., new data arrives). The application must continuously read in a loop until EWOULDBLOCK or EAGAIN is encountered; otherwise remaining data is stranded until new packets arrive.
