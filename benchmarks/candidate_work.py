"""Installed SDK same-input synthetic timing, Jaccard work and allocation probe.

No source injection. Default result is stdout JSON; --out is create-only.
Python allocations and process RSS are distinct measurements, not a quota.
"""
import argparse
import copy
import ctypes
import hashlib
import json
import os
from pathlib import Path
import statistics
import time
import tracemalloc
from splitleak import audit, load, plan
import splitleak.graph as graph


def fixtures():
    def rows(content, **extra):
        return [{'id': f'R{i:03}', 'split': 'train', 'pinned': True,
                 'content': content(i), **extra} for i in range(200)]
    sparse = rows(lambda i: ' '.join(f'private{i}term{j}' for j in range(50)))
    common = rows(lambda i: 'common ' + ' '.join(f'private{i}term{j}' for j in range(50)))
    dense = rows(lambda i: 'Straße shared words', subject='same', group='same',
                 temporal_scope='clock', start=0, end=1)
    base = {'splits': ['train', 'test'], 'policy': {'near_threshold': .8}}
    return {
        'sparse-long': dict(base, samples=sparse),
        'common-token-no-near-edges': dict(base, samples=common),
        'dense-full-reasons': dict(base, samples=dense),
        'zero-threshold-disjoint': dict(base, samples=rows(lambda i: f'unique{i}'), policy={'near_threshold': 0}),
        'small-two': dict(base, samples=sparse[:2]),
        'single': dict(base, samples=sparse[:1]),
    }


def measured(fn, repeats):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        result = fn()
        times.append((time.perf_counter() - start) * 1000)
        del result
    tracemalloc.start()
    result = fn()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del result
    return {'median_ms': statistics.median(times), 'python_peak_bytes': peak,
            'scope': 'full call incl result allocation; separate untraced timing'}


def rss():
    if os.name != 'nt':
        return {'available': False}
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    assert psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    return {'current_bytes': counters.WorkingSetSize, 'process_lifetime_peak_bytes': counters.PeakWorkingSetSize,
            'scope': 'whole process incl imports, prior cases and tracing; not graph-owned'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path)
    p.add_argument('--repeats', type=int, default=3)
    a = p.parse_args()
    assert a.repeats > 0
    results = {}
    for name, document in fixtures().items():
        before = copy.deepcopy(document)
        calls = {'intersection': 0, 'union': 0}
        class CountSet(set):
            def __and__(self, other):
                calls['intersection'] += 1
                return super().__and__(other)
            def __or__(self, other):
                calls['union'] += 1
                return super().__or__(other)
        graph.set = CountSet
        try:
            edges = graph.relations(document)
        finally:
            del graph.set
        graph_digest = hashlib.sha256(json.dumps(edges, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()
        results[name] = {'rows': len(document['samples']), 'edges': len(edges), 'graph_sha256': graph_digest,
                         'actual_jaccard_set_operations': calls, 'load': measured(lambda: load(document), a.repeats),
                         'audit': measured(lambda: audit(document), a.repeats),
                         'whole_plan_with_independent_checker': measured(lambda: plan(document), a.repeats), 'rss': rss()}
        assert document == before
        results[name]['input_unchanged'] = True
    if a.out:
        with a.out.open('x', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
    print(json.dumps(results))


if __name__ == '__main__':
    main()
