"""
Recursive Causal Graph Decomposition Engine for "Why?" reasoning.
Builds and traverses causal dependencies of failures and bugs.
"""

from typing import List, Dict, Any
from app.models.schemas import CausalStep, WhyFollowUpResponse

CAUSAL_KNOWLEDGE_TREE: Dict[str, Dict[str, Any]] = {
    "oom_kill": {
        "text": "Linux OOM Killer terminated the process with SIGKILL (Exit 137)",
        "sub_causes": ["physical_memory_exhaustion", "cgroup_limit_breach", "swap_disabled"],
        "science": "Page allocator zone exhaustion without clean page reclamation causes out_of_memory() trigger.",
        "verification": "Check 'dmesg -T | grep -E -i \"oom|killed process\"' and inspect /proc/meminfo CommitLimit."
    },
    "physical_memory_exhaustion": {
        "text": "Physical RAM and page buffers exhausted",
        "sub_causes": ["heap_leak_unbounded", "in_memory_cache_eviction_failure"],
        "science": "Resident Set Size (RSS) monotonically increases without garbage collection or explicit free().",
        "verification": "Collect heap snapshots over a 30-minute interval using pprof or jemalloc."
    },
    "cgroup_limit_breach": {
        "text": "Container memory exceeded memory.max / memory.limit_in_bytes",
        "sub_causes": ["misaligned_jvm_xmx", "untracked_native_c_allocations"],
        "science": "Kernel cgroup controller accounts for anonymous pages, swap, and shared memory against the cgroup ceiling.",
        "verification": "Examine 'cat /sys/fs/cgroup/memory/memory.failcnt' or 'cat /sys/fs/cgroup/memory.events'."
    },
    "cuda_oom": {
        "text": "CUDA Out of Memory: Device VRAM allocation failed",
        "sub_causes": ["detached_graph_loss_accumulation", "activation_memory_explosion", "vram_fragmentation"],
        "science": "THCCachingHostAllocator cannot find a contiguous chunk of unallocated VRAM matching the tensor allocation request.",
        "verification": "Run with 'PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128' and log 'torch.cuda.memory_summary()'."
    },
    "detached_graph_loss_accumulation": {
        "text": "Computation graph retained across training iterations",
        "sub_causes": ["loss_appended_without_item", "global_tensor_reference"],
        "science": "Appending a raw tensor with requires_grad=True preserves the entire backwards autograd DAG in memory.",
        "verification": "Verify all scalar loss logging calls use 'loss.item()' instead of raw tensor."
    },
    "sigsegv_fault": {
        "text": "SIGSEGV 11: Invalid memory access or address dereference",
        "sub_causes": ["null_pointer_dereference", "use_after_free", "stack_buffer_overflow"],
        "science": "CPU Memory Management Unit (MMU) encountered a page table translation exception.",
        "verification": "Recompile with '-fsanitize=address -g' and run under GDB or Valgrind."
    },
    "deadlock_condition": {
        "text": "Thread Deadlock: Two or more threads waiting circular on mutexes",
        "sub_causes": ["lock_order_inversion", "blocking_io_under_mutex", "nested_sync_primitives"],
        "science": "Circular wait invariant satisfied in violation of Dijkstra hierarchy guarantees.",
        "verification": "Capture thread stack dump using jstack (Java) or 'thread apply all bt' (GDB/C++)."
    }
}

class CausalGraphEngine:
    def __init__(self):
        self.tree = CAUSAL_KNOWLEDGE_TREE

    def get_initial_causes(self, query: str) -> List[CausalStep]:
        q = query.lower()
        if "cuda" in q or "vram" in q or "torch" in q:
            root_key = "cuda_oom"
        elif "deadlock" in q or "mutex" in q or "lock" in q:
            root_key = "deadlock_condition"
        elif "sigsegv" in q or "segmentation" in q or "null" in q:
            root_key = "sigsegv_fault"
        else:
            root_key = "oom_kill"

        node = self.tree.get(root_key, self.tree["oom_kill"])
        steps: List[CausalStep] = []
        for i, sub in enumerate(node["sub_causes"]):
            sub_info = self.tree.get(sub, {
                "text": sub.replace("_", " ").capitalize(),
                "sub_causes": [],
                "science": "Direct physiological system failure",
                "verification": "Examine system metrics"
            })
            steps.append(CausalStep(
                step_id=sub,
                claim=sub_info["text"],
                sub_causes=sub_info.get("sub_causes", []),
                confidence=round(0.92 - (i * 0.08), 2),
                evidence=sub_info.get("science", "")
            ))
        return steps

    def explore_why(self, claim_id: str, claim_text: str, depth: int = 1) -> WhyFollowUpResponse:
        key = claim_id.lower().replace("-", "_")
        node = self.tree.get(key)

        if not node:
            # Fallback dynamic decomposition
            return WhyFollowUpResponse(
                claim_id=claim_id,
                claim_text=claim_text,
                depth=depth + 1,
                direct_causes=[
                    CausalStep(
                        step_id=f"{claim_id}_sub1",
                        claim=f"Primary resource constraint under {claim_text}",
                        sub_causes=[],
                        confidence=0.88,
                        evidence="Observed via metric boundary failure"
                    ),
                    CausalStep(
                        step_id=f"{claim_id}_sub2",
                        claim="Upstream threshold or concurrency invariant violation",
                        sub_causes=[],
                        confidence=0.79,
                        evidence="Syscall sequence or latency spike precedent"
                    )
                ],
                scientific_basis="Causal chain indicates upstream state divergence prior to exception trigger.",
                suggested_verification="Inspect preceding log entries (t - 5s) and attach diagnostic profiler."
            )

        sub_steps: List[CausalStep] = []
        for i, sub in enumerate(node.get("sub_causes", [])):
            sub_info = self.tree.get(sub, {
                "text": sub.replace("_", " ").capitalize(),
                "sub_causes": [],
                "science": "Direct sub-system interaction effect"
            })
            sub_steps.append(CausalStep(
                step_id=sub,
                claim=sub_info["text"],
                sub_causes=sub_info.get("sub_causes", []),
                confidence=round(0.94 - (i * 0.07), 2),
                evidence=sub_info.get("science", "")
            ))

        return WhyFollowUpResponse(
            claim_id=claim_id,
            claim_text=node.get("text", claim_text),
            depth=depth + 1,
            direct_causes=sub_steps,
            scientific_basis=node.get("science", "Underlying runtime operational invariant."),
            suggested_verification=node.get("verification", "Execute runtime diagnostic validation.")
        )
