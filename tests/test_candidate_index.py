import copy
import random
import unittest
from unittest.mock import patch
from splitleak import audit, check, explain, load, plan
import splitleak.graph as graph
import splitleak.repair as repair
from candidate_oracle import fixture, groups, path, reference


def run_cases():
    totals = {'seeded_200_row_cases': 100, 'shuffled_cases': 100, 'edges_compared': 0,
              'plan_reference': 'same repair with independent all-pairs edges; not a new optimizer oracle'}
    for seed in range(100):
        document = fixture(seed)
        before = copy.deepcopy(document)
        model = load(document)
        expected = reference(model)
        actual = audit(model)
        assert actual['edges'] == expected, ('edges', seed)
        expected_groups = groups([s.id for s in model.samples], expected)
        assert actual['components'] == expected_groups, ('components', seed)
        assert explain(model, 'R000', 'R199') == path([s.id for s in model.samples], expected, 'R000', 'R199'), ('path', seed)
        proposed = plan(model, max_states=1000)
        with patch.object(repair, 'relations', reference):
            expected_plan = plan(model, max_states=1000)
        assert proposed == expected_plan, ('plan', seed)
        assignment = {s.id: s.split for s in model.samples}
        verdict = check(model, {'document_digest': model.digest, 'assignment': assignment})
        conflicts = [g for g in expected_groups if len({assignment[s] for s in g}) > 1]
        residual = [[e['a'], e['b']] for e in expected if assignment[e['a']] != assignment[e['b']]]
        assert verdict['component_conflicts'] == conflicts and verdict['residual_cross_split_edges'] == residual
        assert verdict['valid'] == (not conflicts)
        if proposed['assignment'] is not None:
            assert check(model, proposed) == proposed['check'] and proposed['check']['valid']
        shuffled = copy.deepcopy(document)
        random.Random(seed).shuffle(shuffled['samples'])
        assert audit(shuffled) == actual and plan(shuffled, max_states=1000) == proposed
        assert document == before
        totals['edges_compared'] += len(expected)
    return totals


class CandidateTests(unittest.TestCase):
    def test_hundred_seeded_200_row_full_graph_and_workflows(self):
        self.assertEqual(run_cases()['seeded_200_row_cases'], 100)

    def test_reason_order_empty_unicode_zero_and_exact_ratios(self):
        d = {'samples': [{'id': 'A', 'split': 'train', 'content': 'Straße a', 'subject': 'u', 'group': 'g', 'temporal_scope': 's', 'start': 0, 'end': 1},
                         {'id': 'B', 'split': 'test', 'content': 'STRASSE a', 'subject': 'u', 'group': 'g', 'temporal_scope': 's', 'start': .5, 'end': 2},
                         {'id': 'C', 'split': 'train', 'content': ''}, {'id': 'D', 'split': 'test', 'content': ''},
                         {'id': 'E', 'split': 'train', 'content': '  '}, {'id': 'F', 'split': 'test', 'content': 'disjoint'}],
             'policy': {'near_threshold': 0}}
        self.assertEqual(graph.relations(d), reference(d))
        self.assertEqual([r['kind'] for r in graph.relations(d)[0]['reasons']], ['group', 'subject', 'near', 'temporal'])
        d['samples'][1]['content'] = d['samples'][0]['content']
        self.assertEqual([r['kind'] for r in graph.relations(d)[0]['reasons']], ['group', 'exact', 'subject', 'near', 'temporal'])

    def test_scope_half_open_strict_decimal_and_extreme_time(self):
        for embargo in (0, .2, .20000000000000004):
            d = {'samples': [{'id': 'A', 'split': 'train', 'temporal_scope': 's', 'start': 0, 'end': .1},
                             {'id': 'B', 'split': 'test', 'temporal_scope': 's', 'start': .3, 'end': .4},
                             {'id': 'C', 'split': 'train', 'temporal_scope': 'other', 'start': 0, 'end': 1}],
                 'policy': {'near_threshold': None, 'embargo': embargo}}
            self.assertEqual(graph.relations(d), reference(d))
        for limit in (10 ** 400, 1e308):
            d['samples'] = [{'id': 'B', 'split': 'test', 'temporal_scope': 's', 'start': -limit, 'end': limit},
                            {'id': 'A', 'split': 'train', 'temporal_scope': 's', 'start': 0, 'end': 1}]
            self.assertEqual(graph.relations(d), reference(d))

    def test_mutation_has_no_cross_call_index(self):
        d = fixture(0)
        self.assertEqual(audit(d)['edges'], [])
        d['samples'][1]['content'] = d['samples'][0]['content']
        d['policy']['exact'] = True
        self.assertEqual(audit(d)['edges'], reference(d))
        d['samples'][1]['temporal_scope'] = d['samples'][0]['temporal_scope']
        d['policy']['temporal'] = True
        self.assertEqual(audit(d)['edges'], reference(d))

    def test_pair_work_and_state_boundary(self):
        d = fixture(0)
        d['policy']['near_threshold'] = .8
        p = load(d)
        tokens = {s.id: set(s.content.casefold().split()) for s in p.samples}
        from fractions import Fraction
        self.assertEqual(list(graph._candidate_pairs(p, tokens, {}, Fraction('0.8'))), [])
        d['policy']['near_threshold'] = 0
        self.assertEqual(len(graph.relations(d)), 19900)
        d = fixture(1)
        d['samples'] = d['samples'][:1]
        self.assertEqual(plan(d, max_states=1)['status'], 'UNKNOWN')
        self.assertEqual(plan(d, max_states=2)['status'], 'OPTIMAL')


if __name__ == '__main__':
    unittest.main()
