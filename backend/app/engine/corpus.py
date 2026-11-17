"""
Technical Knowledge Base Corpus for AI Why? Engine.
Contains curated diagnostic documentation across operating systems, distributed systems,
machine learning runtimes, concurrency primitives, and cloud-native infrastructure.
"""

KNOWLEDGE_CORPUS = [
    {
        "id": "KB-SYS-001",
        "title": "Linux Out of Memory (OOM) Killer Invariants & Cgroup Limits",
        "domain": "systems",
        "keywords": ["oom", "oomkiller", "cgroup", "memory", "paging", "kill -9", "exit code 137"],
        "content": (
            "When the Linux kernel physical allocator fails to satisfy a page allocation request (order-0 to order-10) "
            "and active/inactive LRU page reclamation fails to free sufficient dirty/clean cache pages, out_of_memory() "
            "is invoked. In containerized environments, the memory cgroup controller (cgroup v1/v2 memory.max) triggers "
            "the mem_cgroup_out_of_memory handler. The kernel computes a badness score based on resident set size (RSS), "
            "swap usage, and oom_score_adj. Processes exceeding their cgroup quota are immediately sent SIGKILL (exit code 137). "
            "Root causes include unbounded in-memory buffering, memory leaks in unmanaged heaps, excessive goroutine/thread stack growth, "
            "or insufficient swap/pagefile allocations."
        ),
        "remediation": [
            "Inspect memory profile using jemalloc/pprof or valgrind to identify heap growth.",
            "Adjust container memory limits and configure explicit heap headroom (e.g., JVM -Xmx vs container memory).",
            "Tune vm.overcommit_memory and vm.swappiness in host sysctl settings."
        ]
    },
    {
        "id": "KB-SYS-002",
        "title": "Segmentation Fault (SIGSEGV) & Invalid Memory Access Dynamics",
        "domain": "systems",
        "keywords": ["sigsegv", "segmentation fault", "null pointer", "dangling pointer", "use after free", "buffer overflow"],
        "content": (
            "A SIGSEGV (Signal 11) is delivered to a process when hardware Memory Management Unit (MMU) page table traversal "
            "encounters a translation fault, permission violation (e.g. attempting to write to read-only code segments), "
            "or an unmapped virtual address. Common runtime triggers include dereferencing a NULL pointer (address 0x0 or nearby offsets), "
            "stack buffer overruns corrupting the return address pointer, and use-after-free conditions where a pointer targets freed heap "
            "memory that has been unmapped or reassigned. In multi-threaded applications, data races on shared raw pointers lead to "
            "transient memory corruptions and unpredictable memory layout states."
        ),
        "remediation": [
            "Enable AddressSanitizer (ASan) and UndefinedBehaviorSanitizer (UBSan) during compilation (-fsanitize=address,undefined).",
            "Generate and inspect core dumps using GDB: 'gdb executable core' followed by 'bt full'.",
            "Employ smart pointers (std::unique_ptr, std::shared_ptr) or memory-safe languages to enforce ownership semantics."
        ]
    },
    {
        "id": "KB-ML-001",
        "title": "CUDA Out-Of-Memory (OOM) & PyTorch Tensor Allocation Regressions",
        "domain": "ml",
        "keywords": ["cuda", "torch", "gpu", "out of memory", "allocated memory", "device-side assert", "gradient"],
        "content": (
            "PyTorch CUDA OOM occurs when the PyTorch caching allocator (THCCachingHostAllocator) cannot reserve a contiguous block of "
            "VRAM from the NVIDIA driver runtime. This is caused by accumulating computation graphs from detached tensors (e.g., storing "
            "loss without .item()), activation tensor caching in large batch forward passes, unreleased inter-layer activation caches, "
            "or optimizer state explosion (e.g., Adam maintains 2x model parameters for first and second momentum states). "
            "Furthermore, high fragmentation within PyTorch's internal sub-allocator can result in OOM even when total free VRAM exceeds the request."
        ),
        "remediation": [
            "Use torch.cuda.empty_cache() and verify gradient graph detachment: loss_history.append(loss.item()).",
            "Enable Gradient Checkpointing (torch.utils.checkpoint) to trade compute for memory by recalculating activations.",
            "Adopt mixed precision training via torch.cuda.amp.autocast() to reduce activation and weight footprint by 50%."
        ]
    },
    {
        "id": "KB-ML-002",
        "title": "Gradient Explosion, Vanishing, and Loss Divergence (NaN / Inf)",
        "domain": "ml",
        "keywords": ["nan loss", "gradient explosion", "inf", "gradient vanishing", "divergence", "learning rate"],
        "content": (
            "Numerical instability in deep neural networks leading to NaN or Inf loss values is commonly caused by gradient compounding "
            "across deep architectures with unconstrained matrix multiplications (spectral radius > 1.0). When backpropagated gradients "
            "exceed the representable range of IEEE 754 floating point (FP16/FP32), overflow generates +/-Inf, which contaminates downstream "
            "weight updates with NaN. Additional triggers include unnormalized inputs causing large logits in cross-entropy/log functions "
            "(e.g., log(0)), division by zero in variance computation within custom normalization layers, or excessive learning rates."
        ),
        "remediation": [
            "Implement gradient clipping using torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0).",
            "Verify input data normalization (zero mean, unit variance) and inspect for unexpected zeros or negative values.",
            "Add epsilon guards (e.g., torch.clamp(x, min=1e-7)) before logarithmic or division operations."
        ]
    },
    {
        "id": "KB-NET-001",
        "title": "TCP Connection Reset by Peer (ECONNRESET) & Socket Lifecycle",
        "domain": "network",
        "keywords": ["econnreset", "connection reset", "tcp", "socket", "rst", "half-open", "keepalive"],
        "content": (
            "ECONNRESET (Error 104) occurs when the local transport layer receives a TCP segment with the RST (Reset) flag set. "
            "This indicates that the remote peer abruptly terminated the connection rather than completing a graceful four-way FIN handshake. "
            "Underlying causes include intermediate reverse proxies (e.g. Nginx, Envoy, AWS ALB) closing idle connections after a timeout "
            "while the client attempts to write, the remote server process terminating abruptly (segfault or OOM), an application writing data "
            "to a socket that the remote application has already closed, or hardware firewall state-table eviction."
        ),
        "remediation": [
            "Synchronize client and server idle keep-alive timeouts (client pool idle timeout < proxy idle timeout).",
            "Implement exponential backoff retry semantics for idempotent HTTP/RPC requests.",
            "Inspect upstream server dmesg logs for worker crashes or OOM events coincident with the connection resets."
        ]
    },
    {
        "id": "KB-CONCUR-001",
        "title": "Thread Deadlock & Lock Order Inversion in Concurrent Runtimes",
        "domain": "concurrency",
        "keywords": ["deadlock", "lock order", "mutex", "concurrency", "thread starvation", "dining philosophers"],
        "content": (
            "Deadlock occurs when two or more execution threads enter an unresolvable waiting state because each holds a shared resource/mutex "
            "that the other requires to proceed, satisfying the four Coffman conditions: Mutual Exclusion, Hold and Wait, No Preemption, and "
            "Circular Wait. The primary architectural cause is Lock Order Inversion: Thread A acquires Mutex 1 then Mutex 2, while Thread B "
            "simultaneously acquires Mutex 2 then Mutex 1. In high-concurrency environments, nested synchronization blocks and blocking I/O calls "
            "held inside locked sections exacerbate contention and deadlock probabilities."
        ),
        "remediation": [
            "Enforce a strict global lock hierarchy: always acquire mutexes in a predefined deterministic order.",
            "Use try-lock mechanisms with timeout thresholds (e.g., pthread_mutex_timedlock or std::unique_lock) rather than indefinite blocking.",
            "Migrate from coarse-grained locks to lock-free lockless data structures (atomics, channels, or actor message-passing patterns)."
        ]
    }
]
