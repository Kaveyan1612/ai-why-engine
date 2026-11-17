"""
Multi-Tier Reasoning Explainer for AI Why? Engine.
Generates beginner, intermediate, and expert technical explanations
guided by retrieved domain knowledge citations.
"""

from typing import Dict, Any, List
from app.models.schemas import TierExplanation, DocumentCitation

class MultiTierExplainer:
    def explain(self, query: str, citations: List[DocumentCitation]) -> Dict[str, TierExplanation]:
        q_lower = query.lower()
        context_hint = citations[0].title if citations else "System Runtime Fault"

        # Determine domain pattern
        if "cuda" in q_lower or "torch" in q_lower or "gpu" in q_lower:
            return self._build_cuda_explanation(query, citations)
        elif "deadlock" in q_lower or "mutex" in q_lower or "lock" in q_lower:
            return self._build_deadlock_explanation(query, citations)
        elif "sigsegv" in q_lower or "segmentation" in q_lower:
            return self._build_sigsegv_explanation(query, citations)
        else:
            return self._build_oom_explanation(query, citations)

    def _build_oom_explanation(self, query: str, citations: List[DocumentCitation]) -> Dict[str, TierExplanation]:
        return {
            "beginner": TierExplanation(
                level="beginner",
                summary="The operating system ran out of room in memory and was forced to shut down the program.",
                detailed_explanation=(
                    "Think of your computer's RAM like a physical desk where you keep books you are currently reading. "
                    "When the desk becomes completely piled up with books and papers, you cannot place a single new sheet down. "
                    "Rather than allowing the whole building to collapse, a safety guard (the Linux Out-of-Memory Killer) "
                    "steps in and forcefully removes the largest pile of work to keep the rest of the computer running."
                ),
                analogy="A chef in a kitchen whose counter is completely full of dirty plates—the manager steps in and throws away the biggest pot to keep the kitchen from halting.",
                architectural_impact="The application crashed with Exit Code 137, dropping current user requests and requiring a container restart.",
                root_cause_analysis="The application memory consumption steadily grew until it breached the container's allocated ceiling.",
                remediation_steps=[
                    "Give the container more memory allocation in Docker/Kubernetes.",
                    "Look for large files or lists being loaded all at once instead of in chunks.",
                    "Restart the service regularly as a temporary band-aid while finding the leak."
                ],
                code_fix="# Stream large datasets in chunks instead of loading all at once:\nwith open('large_dataset.json', 'r') as f:\n    for line in f:\n        process_line(line)"
            ),
            "intermediate": TierExplanation(
                level="intermediate",
                summary="Container Resident Set Size (RSS) exceeded cgroup memory.max threshold, triggering the kernel OOM killer.",
                detailed_explanation=(
                    "Under Linux cgroup v1/v2 enforcement, the kernel tracks anonymous memory, page cache buffers, and swap usage. "
                    "When total allocation breaches the container cgroup ceiling and kswapd cannot reclaim sufficient page frames "
                    "from the inactive file list, the mem_cgroup_out_of_memory handler scores processes based on RSS and oom_score_adj. "
                    "The process with the highest badness score is dispatched SIGKILL (Exit Code 128 + 9 = 137)."
                ),
                analogy="A strict tenant lease with an electrical breaker: when total wattage exceeds the panel limit, the main breaker trips instantly.",
                architectural_impact="Container restart storm (CrashLoopBackOff), potential cascading failovers across remaining cluster nodes.",
                root_cause_analysis="Unbounded memory consumption caused by unevicted in-memory cache entries and lack of backpressure.",
                remediation_steps=[
                    "Profile heap memory growth using jemalloc or pprof over a representative load cycle.",
                    "Configure explicit heap boundary flags (e.g. JVM -XX:MaxRAMPercentage=75.0 or Go GOMEMLIMIT).",
                    "Implement a LRU eviction policy with bounded size and TTL expiration on all in-memory caches."
                ],
                code_fix="from functools import lru_cache\n\n# Enforce bounded cache size to avoid unbounded memory growth:\n@lru_cache(maxsize=4096)\ndef get_processed_payload(payload_id: str):\n    return fetch_and_parse(payload_id)"
            ),
            "expert": TierExplanation(
                level="expert",
                summary="Kernel zone allocator failure in alloc_pages_nodemask() leading to mem_cgroup_out_of_memory() SIGKILL invocation.",
                detailed_explanation=(
                    "The Linux buddy allocator failed an order-0 page allocation in ZONE_NORMAL. The kernel attempted direct reclamation "
                    "via try_to_free_mem_cgroup_pages(). Because dirty page writeback was throttled and unevictable page lists dominated, "
                    "the reclaim loop yielded 0 freed pages. Consequently, out_of_memory() invoked select_bad_process(), calculating "
                    "points = (rss_pages + swap_pages) * 1000 / total_pages + oom_score_adj. The target task received an uncatchable SIGKILL. "
                    "Kernel slab inspection reveals dentry/inode cache exhaustion coupled with unmapped anonymous mmap() allocations."
                ),
                analogy="Physical page frame depletion in kernel zone memory with exhausted slab freelists.",
                architectural_impact="Instant process teardown without execution of exit handlers, leaving socket endpoints in TIME_WAIT / RST state.",
                root_cause_analysis="Kernel slab fragmentation and anonymous dirty page accumulation without swap backing under cgroup v2 memory.max.",
                remediation_steps=[
                    "Tune host sysctl: vm.overcommit_memory=2, vm.overcommit_ratio=80 to prevent over-allocation.",
                    "Audit native memory via eBPF tracing (bpftrace -e 'kprobe:alloc_pages { @[kstack()] = count(); }').",
                    "Isolate page cache usage by mounting with tmpfs or configuring memory.high throttling for early backpressure."
                ],
                code_fix="// In C/C++ or kernel runtime configuration:\n// Enforce madvise MADV_DONTNEED on released buffers to promptly return pages to kernel MMU:\n#include <sys/mman.h>\n\nvoid release_scratch_pages(void* addr, size_t len) {\n    madvise(addr, len, MADV_DONTNEED);\n}"
            )
        }

    def _build_cuda_explanation(self, query: str, citations: List[DocumentCitation]) -> Dict[str, TierExplanation]:
        return {
            "beginner": TierExplanation(
                level="beginner",
                summary="Your graphics card (GPU) ran completely out of video memory (VRAM) while running the AI model.",
                detailed_explanation=(
                    "A graphics card has its own dedicated ultra-fast memory called VRAM. When training or running an AI model, "
                    "the model's weights and the data batch must fit simultaneously in this memory. When your batch size is too large "
                    "or the model is too big, the graphics card cannot fit the next calculation, and the program halts with an Out-of-Memory error."
                ),
                analogy="Trying to fit 10 people inside a 5-seater sedan: it doesn't matter how fast the car is, everyone simply cannot fit inside at once.",
                architectural_impact="Model training or inference crashes abruptly; ongoing batch gradients are lost.",
                root_cause_analysis="Tensor memory requirements exceeded the physical VRAM capacity of the GPU device.",
                remediation_steps=[
                    "Reduce your training batch size (e.g., from 32 to 16 or 8).",
                    "Use mixed precision (FP16 or BF16) instead of standard 32-bit floating point.",
                    "Make sure you aren't storing the loss history as full tensors in a Python list."
                ],
                code_fix="# Change loss accumulation:\n# Incorrect: loss_history.append(loss)\n# Correct:\nloss_history.append(loss.item())"
            ),
            "intermediate": TierExplanation(
                level="intermediate",
                summary="PyTorch caching allocator (THCCachingHostAllocator) failed to reserve contiguous GPU VRAM.",
                detailed_explanation=(
                    "During the forward/backward pass, PyTorch dynamically allocates memory for weights, activations, and gradients. "
                    "The caching allocator keeps freed blocks in an internal pool to prevent expensive cudaMalloc/cudaFree driver calls. "
                    "When activation tensors accumulate (or an autograd computation graph is preserved by storing non-detached tensors), "
                    "the allocator runs out of unfragmented pool blocks, raising 'RuntimeError: CUDA out of memory'."
                ),
                analogy="A luggage locker system where small bags are scattered across large lockers, leaving no single empty locker big enough for a large suitcase.",
                architectural_impact="Immediate crash of the worker thread; GPU context may need to be reset in distributed DDP setups.",
                root_cause_analysis="Accumulation of autograd computational graph or excessive intermediate activation memory during backpropagation.",
                remediation_steps=[
                    "Enable Gradient Checkpointing to recompute activations during backward pass instead of storing them.",
                    "Use torch.cuda.amp.autocast() to reduce tensor memory footprint by half.",
                    "Explicitly call torch.cuda.empty_cache() between validation cycles."
                ],
                code_fix="from torch.cuda.amp import autocast, GradScaler\n\nscaler = GradScaler()\nwith autocast():\n    outputs = model(inputs)\n    loss = criterion(outputs, targets)\nscaler.scale(loss).backward()\nscaler.step(optimizer)\nscaler.update()"
            ),
            "expert": TierExplanation(
                level="expert",
                summary="PyTorch CUDA allocator arena fragmentation causing cudaErrorMemoryAllocation from the NVIDIA Unified Memory Driver.",
                detailed_explanation=(
                    "The THCCachingHostAllocator operates block pools segregated into small (<1MB) and large (>1MB) arenas. "
                    "When variable-length input sequences produce alternating tensor sizes, arena fragmentation prevents satisfying "
                    "a large allocation even when torch.cuda.mem_get_info() indicates sufficient aggregate free memory. "
                    "Additionally, non-contiguous strides in view transformations create duplicate storage buffers."
                ),
                analogy="Virtual address space fragmentation in non-paged device hardware memory.",
                architectural_impact="CUDA driver synchronization deadlock across multi-GPU NCCL communicators.",
                root_cause_analysis="Sub-allocator chunk fragmentation and uncoalesced activation tensor memory layouts.",
                remediation_steps=[
                    "Set environment variable: export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:128",
                    "Profile memory trace with torch.cuda.memory._record_memory_history(True) and dump snapshot to Chrome tracing.",
                    "Implement FlashAttention-2 kernels to eliminate O(N^2) attention matrix storage in VRAM."
                ],
                code_fix="import os\n# Enable virtual memory expandable segments in PyTorch allocator:\nos.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'\nimport torch\ntorch.cuda.empty_cache()"
            )
        }

    def _build_sigsegv_explanation(self, query: str, citations: List[DocumentCitation]) -> Dict[str, TierExplanation]:
        return {
            "beginner": TierExplanation(
                level="beginner",
                summary="The program crashed because it tried to read or write to an invalid memory location (like an empty house address).",
                detailed_explanation=(
                    "Every computer program is given a specific neighborhood of memory addresses it is permitted to use. "
                    "A Segmentation Fault happens when the program tries to deliver a letter to an address that does not exist, "
                    "or tries to enter a restricted area it has no permission to touch. The computer halts the program immediately "
                    "to prevent corruption."
                ),
                analogy="A delivery driver trying to drop a parcel off at 'House #0' on a street that starts at House #100.",
                architectural_impact="Process terminates immediately with Signal 11, potentially leaving uncommitted data in local buffers.",
                root_cause_analysis="Attempted to dereference an uninitialized, NULL, or freed memory address.",
                remediation_steps=[
                    "Check for NULL pointer checks before accessing objects.",
                    "Make sure arrays are not accessed beyond their allocated length (out-of-bounds).",
                    "Compile with debug symbols enabled (-g) to see the exact line of code that caused the crash."
                ],
                code_fix="// Always verify pointers before dereferencing:\nif (ptr != NULL) {\n    ptr->doSomething();\n}"
            ),
            "intermediate": TierExplanation(
                level="intermediate",
                summary="Hardware MMU generated a page fault on an unmapped or write-protected virtual memory address (SIGSEGV 11).",
                detailed_explanation=(
                    "When an instruction attempts to load from or store to a virtual address, the CPU Memory Management Unit (MMU) "
                    "walks the page tables. If the page table entry (PTE) is not present (e.g. 0x0 NULL pointer), or if the memory page "
                    "is marked PROT_READ and the CPU attempts a write instruction, a page fault exception is generated. "
                    "The kernel handles this exception by delivering signal SIGSEGV to the faulting thread."
                ),
                analogy="Trying to enter a secure facility with a keycard that has neither a registered name nor access clearance.",
                architectural_impact="Immediate process abort, potential core dump generation on disk.",
                root_cause_analysis="Dangling pointer dereference, use-after-free, or array index out-of-bounds buffer overrun.",
                remediation_steps=[
                    "Compile and test with AddressSanitizer: -fsanitize=address,undefined -g.",
                    "Run under Valgrind: valgrind --leak-check=full --track-origins=yes ./binary.",
                    "Use RAII and smart pointers in C++ (std::unique_ptr) to eliminate manual lifecycle errors."
                ],
                code_fix="#include <memory>\n// Replace raw pointers with std::unique_ptr for automatic deterministic lifecycle:\nstd::unique_ptr<Worker> worker = std::make_unique<Worker>();\nworker->execute();"
            ),
            "expert": TierExplanation(
                level="expert",
                summary="Virtual address translation fault; CR2 register points to canonical address violation or unmapped PTE.",
                detailed_explanation=(
                    "The instruction pointer (RIP) executed a memory operand referencing an unmapped virtual address stored in control register CR2. "
                    "The kernel page fault handler (do_user_addr_fault()) determined that find_vma() returned NULL or the faulting address "
                    "failed access permission flags (VM_READ/VM_WRITE) against the VMA descriptor. "
                    "In multi-threaded scenarios, this is frequently triggered by a race condition where Thread 1 executes free() and Thread 2 "
                    "reads the pointer concurrently before synchronization barrier completion."
                ),
                analogy="TLB miss followed by page table walk terminating at a zeroed page directory pointer.",
                architectural_impact="Direct unrecoverable termination; thread stack frames unwound abruptly without C++ destructor execution.",
                root_cause_analysis="Thread race condition leading to double-free or use-after-free corrupting heap metadata arenas.",
                remediation_steps=[
                    "Inspect core dump: gdb -q ./binary core -ex 'thread apply all bt full'.",
                    "Analyze memory allocations with eBPF memleak: /usr/share/bcc/tools/memleak -p $(pidof process).",
                    "Audit atomic state transitions using ThreadSanitizer (-fsanitize=thread)."
                ],
                code_fix="// Enforce thread-safe atomic pointer exchange:\n#include <atomic>\n\nstd::atomic<Buffer*> active_buffer{nullptr};\nBuffer* old_buf = active_buffer.exchange(new_buf, std::memory_order_acq_rel);\nif (old_buf) delete old_buf;"
            )
        }

    def _build_deadlock_explanation(self, query: str, citations: List[DocumentCitation]) -> Dict[str, TierExplanation]:
        return {
            "beginner": TierExplanation(
                level="beginner",
                summary="Two or more parts of the software got stuck in a standoff where each is waiting for the other to finish.",
                detailed_explanation=(
                    "Imagine two cars meeting in a very narrow one-lane tunnel going in opposite directions. "
                    "Neither driver is willing to back up, so both sit there forever with their engines running. "
                    "In software, this is called a deadlock: Thread A holds Key 1 and wants Key 2, while Thread B holds Key 2 and wants Key 1."
                ),
                analogy="Two polite people trying to pass each other in a doorway: both step to the same side at the exact same moment, repeatedly blocking each other.",
                architectural_impact="The system freezes or stops responding to user commands; CPU usage drops to near zero as threads sleep forever.",
                root_cause_analysis="Circular waiting condition between multiple threads attempting to acquire locks.",
                remediation_steps=[
                    "Always acquire locks in the exact same order everywhere in the code.",
                    "Set timeouts on locks so threads give up instead of waiting forever.",
                    "Minimize the amount of work done while holding a lock."
                ],
                code_fix="# Acquire locks in consistent numerical order:\n# Thread 1 and Thread 2 both lock lock_a then lock_b\nwith lock_a:\n    with lock_b:\n        do_work()"
            ),
            "intermediate": TierExplanation(
                level="intermediate",
                summary="Lock Order Inversion satisfying the four Coffman deadlock conditions (Circular Wait).",
                detailed_explanation=(
                    "A concurrent deadlock occurs when Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait are all simultaneously satisfied. "
                    "Thread 1 acquires Mutex A and requests Mutex B; concurrently, Thread 2 acquires Mutex B and requests Mutex A. "
                    "Both threads enter the kernel futex_wait queue indefinitely, causing API timeouts and thread pool exhaustion."
                ),
                analogy="Dining Philosophers: every philosopher picks up their left fork simultaneously, so nobody can pick up their right fork.",
                architectural_impact="Worker pool starvation, upstream load balancer 504 Gateway Timeouts, thread leaks.",
                root_cause_analysis="Asymmetric lock acquisition order across disparate service handlers.",
                remediation_steps=[
                    "Implement std::lock or Python's bounded context manager to lock multiple mutexes atomically without deadlocking.",
                    "Use try_lock_for() with exponential backoff on failure.",
                    "Capture thread dumps using jstack or gdb to identify the cycle in the lock dependency graph."
                ],
                code_fix="// In C++17:\n#include <mutex>\n\nstd::scoped_lock lock(mutexA, mutexB); // Atomically locks both without deadlock\nshared_data.process();"
            ),
            "expert": TierExplanation(
                level="expert",
                summary="Kernel futex sleep cycle with lock inversion across POSIX pthread_mutex_t instances.",
                detailed_explanation=(
                    "Inspection of /proc/<pid>/task/*/wchan reveals threads sleeping inside futex_wait_queue_me(). "
                    "The kernel wait queue graph contains a directed cycle (T1 -> MutexB -> T2 -> MutexA -> T1). "
                    "Priority inversion is also present when real-time priority tasks wait on lower-priority tasks that have been preempted. "
                    "Futex contention overhead escalates as threads yield CPU time slices in perpetual sleep states."
                ),
                analogy="Unsolvable circular dependency in directed acyclic graph (DAG) topology.",
                architectural_impact="Complete loss of throughput; health check probes fail, triggering cascading pod terminations.",
                root_cause_analysis="Non-deterministic lock ordering and priority inversion without mutex PI (Priority Inheritance) protocol.",
                remediation_steps=[
                    "Initialize mutexes with PTHREAD_PRIO_INHERIT protocol via pthread_mutexattr_setprotocol().",
                    "Instrument lock acquisition latency via eBPF offcputime.",
                    "Transition to lock-free MPMC ringbuffers or Actor-based isolated state architectures."
                ],
                code_fix="// Initialize pthread mutex with priority inheritance protocol:\npthread_mutexattr_t attr;\npthread_mutexattr_init(&attr);\npthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);\npthread_mutex_init(&my_mutex, &attr);"
            )
        }
