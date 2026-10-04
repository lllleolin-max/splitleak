"""All-pairs reference predicates and BFS, independent of candidate generation.

Validated model attributes supply defaults; expected pair/component/path logic
does not call the graph builder, checker or candidate index.
"""
from collections import deque
from fractions import Fraction
from itertools import combinations
import random
from splitleak.model import problem


def reference(value):
    p = problem(value)
    result = []
    for a, b in combinations(p.samples, 2):
        evidence = []
        if a.group is not None and a.group == b.group:
            evidence.append({'kind': 'group', 'strength': 1, 'meaning': 'atomic repair unit'})
        if p.policy.exact and a.content is not None and a.content == b.content:
            evidence.append({'kind': 'exact', 'strength': 1, 'meaning': 'literal text equality'})
        if p.policy.subject and a.subject is not None and a.subject == b.subject:
            evidence.append({'kind': 'subject', 'strength': 1, 'meaning': 'declared shared subject'})
        left = set(a.content.casefold().split()) if a.content is not None else set()
        right = set(b.content.casefold().split()) if b.content is not None else set()
        if p.policy.near_threshold is not None and left and right:
            intersection, union = len(left.intersection(right)), len(left.union(right))
            threshold = Fraction(str(p.policy.near_threshold))
            if intersection * threshold.denominator >= union * threshold.numerator:
                ratio = Fraction(intersection, union)
                evidence.append({'kind': 'near', 'strength': intersection / union,
                                 'ratio': str(ratio.numerator) + '/' + str(ratio.denominator),
                                 'meaning': 'token-set Jaccard; not semantic probability'})
        if p.policy.temporal and a.temporal_scope is not None and a.temporal_scope == b.temporal_scope and a.start is not None and b.start is not None:
            sa, ea, sb, eb = map(lambda x: Fraction(str(x)), (a.start, a.end, b.start, b.end))
            if sa < eb and sb < ea:
                evidence.append({'kind': 'temporal', 'strength': 1,
                                 'overlap_ratio': str(min(ea, eb) - max(sa, sb)),
                                 'meaning': 'half-open support overlap'})
            else:
                gap = sb - ea if ea <= sb else sa - eb
                if gap < Fraction(str(p.policy.embargo)):
                    evidence.append({'kind': 'embargo', 'strength': 1, 'gap_ratio': str(gap),
                                     'meaning': 'gap strictly below embargo'})
        if evidence:
            result.append({'a': a.id, 'b': b.id, 'reasons': evidence})
    return result


def groups(ids, edges):
    adjacent = {s: set() for s in ids}
    for edge in edges:
        adjacent[edge['a']].add(edge['b'])
        adjacent[edge['b']].add(edge['a'])
    remaining, found = set(ids), []
    while remaining:
        pending, seen = [min(remaining)], set()
        while pending:
            node = pending.pop()
            if node not in seen:
                seen.add(node)
                pending.extend(adjacent[node] - seen)
        remaining -= seen
        found.append(sorted(seen))
    return sorted(found)


def path(ids, edges, source, target):
    adjacent = {s: [] for s in ids}
    for edge in edges:
        adjacent[edge['a']].append((edge['b'], edge))
        adjacent[edge['b']].append((edge['a'], edge))
    queue, seen = deque([(source, [])]), {source}
    while queue:
        node, route = queue.popleft()
        if node == target:
            return {'source': source, 'target': target, 'connected': True, 'path': route,
                    'direct': len(route) == 1, 'interpretation': 'isolation policy, not transitive semantic equivalence'}
        for neighbor, edge in sorted(adjacent[node], key=lambda pair: pair[0]):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, route + [edge]))
    return {'source': source, 'target': target, 'connected': False, 'path': []}


def fixture(seed):
    rng = random.Random(1005000 + seed)
    rows = []
    for i in range(200):
        row = {'id': f'R{i:03}', 'split': 'train' if seed % 3 else rng.choice(['train', 'test']), 'pinned': True}
        kind = seed % 5
        if kind == 0:
            row.update(content=f'private{seed}row{i}', subject=f'u{i}', group=f'g{i}',
                       temporal_scope=f's{i}', start=0, end=.1)
        elif kind == 1:
            row.update(content='Straße shared', subject='u', group='g', temporal_scope='s', start=0, end=1)
        elif kind == 2:
            row.update(content=None if i % 10 == 0 else '' if i % 10 == 1 else f'disjoint{i}')
        elif kind == 3:
            row.update(content=rng.choice([None, '', ' \t ', 'Straße', 'STRASSE', 'a b', 'b c', f'unique{i}']),
                       subject=rng.choice([None, None, f'u{i // 10}']), group=rng.choice([None, None, f'g{i // 20}']))
            if i % 3:
                start = rng.randrange(50) / 10
                row.update(temporal_scope=rng.choice(['a', 'b', 'c']), start=start, end=start + .1)
        else:
            row.update(content=f'common unique{i}', subject=f'u{i // 7}', temporal_scope='s', start=i, end=i + .1)
        rows.append(row)
    policy = {'near_threshold': 0 if seed % 5 == 2 else rng.choice([None, .5, .8, 1]),
              'exact': bool(seed % 2), 'subject': bool(seed % 4), 'temporal': bool(seed % 6),
              'embargo': rng.choice([0, .1, .2, 1])}
    return {'samples': rows, 'splits': ['train', 'test'], 'policy': policy}
