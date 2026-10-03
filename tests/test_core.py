import copy
import itertools
import json
from pathlib import Path
import random
import unittest
from splitleak import InputError, load, audit, explain, plan, check, apply
from oracle import optimum


def sample(ident, split="train", **kwargs):
    return {"id": ident, "split": split, **kwargs}


def doc(rows, **kwargs):
    return {"samples": rows, "splits": ["train", "test"], **kwargs}


class CoreTests(unittest.TestCase):
    def test_chain_explains_nonsemantic_transitivity(self):
        d = doc([sample("A", content="oak birch"), sample("B", content="oak birch pine"),
                 sample("C", "test", content="birch pine"), sample("Z", "test", content="isolated", pinned=True)],
                policy={"near_threshold": 0.66}, constraints={"min_retained": {"test": 1}, "min_total": 4})
        path = explain(d, "A", "C")
        self.assertFalse(path["direct"])
        self.assertEqual(len(path["path"]), 2)
        self.assertEqual(plan(d)["cost"], 1)
        self.assertTrue(check(d, plan(d))["valid"])

    def test_relation_types_and_nulls(self):
        d = doc([sample("A", content="same", subject="u"), sample("B", "test", content="same", subject="u"),
                 sample("C"), sample("D", "test")])
        edges = audit(d)["edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual({r["kind"] for r in edges[0]["reasons"]}, {"exact", "near", "subject"})

    def test_time_scope_and_boundaries(self):
        def timed(ident, start, end, scope="sensor-a"):
            return sample(ident, start=start, end=end, temporal_scope=scope)
        d = doc([timed("A", 0, 2), timed("B", 2, 4), timed("C", 0, 2, "sensor-b")], policy={"near_threshold": None})
        self.assertEqual(audit(d)["edges"], [])
        d["policy"]["embargo"] = 1
        self.assertEqual(len(audit(d)["edges"]), 1)
        d["samples"][1]["start"] = 3
        self.assertEqual(audit(d)["edges"], [])
        d["samples"][1]["start"] = 1.9
        self.assertEqual(audit(d)["edges"][0]["reasons"][0]["kind"], "temporal")

    def test_zero_threshold_is_declared_all_nonempty_token_policy(self):
        d = doc([sample("A", content="apple"), sample("B", "test", content="pear"), sample("C", content="")],
                policy={"near_threshold": 0, "exact": False})
        self.assertEqual(len(audit(d)["edges"]), 1)
        self.assertEqual(audit(d)["edges"][0]["reasons"][0]["ratio"], "0/1")

    def test_invalid_input(self):
        invalid = [doc([sample("A"), sample("A")]), doc([sample("A", start=1)]),
                   doc([sample("A", start=1, end=1, temporal_scope="x")]),
                   doc([sample("A", start=False, end=2, temporal_scope="x")]),
                   doc([sample("A", move_cost=True)]), doc([sample("A", delete_cost=-1)]),
                   doc([sample("A", content=3)]), doc([sample("A", subject=False)]),
                   doc([sample("A")], policy={"near_threshold": float("nan")}),
                   doc([sample("A")], policy={"embargo": float("inf")}),
                   doc([sample("A")], constraints={"max_moves": True})]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(InputError):
                load(value)

    def test_pins_retention_and_permissions(self):
        d = doc([sample("A", content="same", pinned=True), sample("B", "test", content="same", pinned=True)])
        self.assertEqual(plan(d)["status"], "INFEASIBLE")
        d["samples"][1]["pinned"] = False
        d["constraints"] = {"min_retained": {"test": 1}}
        self.assertEqual(plan(d)["status"], "INFEASIBLE")
        d["constraints"] = {"max_moves": 0}
        self.assertEqual(plan(d)["status"], "INFEASIBLE")
        d["samples"][1]["delete_cost"] = 2
        self.assertEqual(plan(d)["cost"], 2)
        d["constraints"]["max_cost"] = 1
        self.assertEqual(plan(d)["status"], "INFEASIBLE")

    def test_atomic_groups_and_deleted_bridge_still_isolates(self):
        d = doc([sample("A", group="g", content="x", delete_cost=1), sample("B", "test", group="g", delete_cost=1)])
        p = plan(d)
        self.assertEqual(len(set(p["assignment"].values())), 1)
        tampered = dict(p, assignment={"A": None, "B": "test"})
        self.assertFalse(check(d, tampered)["valid"])
        d = doc([sample("A", content="oak birch", pinned=True), sample("B", content="oak birch pine", delete_cost=1),
                 sample("C", "test", content="birch pine", pinned=True)], policy={"near_threshold": 0.66})
        self.assertEqual(plan(d)["status"], "INFEASIBLE")
        self.assertFalse(check(d, {"document_digest": load(d).digest,
                                  "assignment": {"A": "train", "B": None, "C": "test"}})["valid"])

    def test_checker_reconstructs_source_and_cost(self):
        d = doc([sample("A", content="same"), sample("B", "test", content="same")])
        p = plan(d)
        self.assertTrue(check(d, p)["valid"])
        p["edges"] = []
        p["assignment"]["A"], p["assignment"]["B"] = "train", "test"
        self.assertFalse(check(d, p)["valid"])
        p = plan(d)
        p["cost"] += 1
        self.assertIn("claimed cost mismatch", check(d, p)["errors"])
        p = plan(d)
        d["samples"][0]["move_cost"] = 20
        self.assertFalse(check(d, p)["valid"])

    def test_bound_and_inspected_upper_bound(self):
        d = doc([sample("A"), sample("B")])
        self.assertEqual(plan(d, max_states=1)["status"], "UNKNOWN")
        p = plan(d, max_states=3)
        self.assertEqual(p["status"], "UNKNOWN")
        self.assertIsNotNone(p["assignment"])
        self.assertTrue(p["check"]["valid"])
        self.assertEqual(p["bound_kind"], "inspected feasible upper bound")

    def test_permutation_and_ties(self):
        rows = [sample("A", content="same"), sample("B", "test", content="same"), sample("Z", "test")]
        results = [plan(doc(list(rows))) for rows in itertools.permutations(rows)]
        self.assertTrue(all(r == results[0] for r in results))

    def test_independent_oracle_generated_cases(self):
        rng = random.Random(43)
        for trial in range(45):
            rows = [sample(str(i), rng.choice(["train", "test"]), content=rng.choice([None, "oak", "oak pine", "pine"]),
                           group=rng.choice([None, None, "g"]), move_cost=rng.randrange(4),
                           delete_cost=rng.choice([None, 0, 2]), pinned=rng.random() < .15) for i in range(4)]
            d = doc(rows, policy={"near_threshold": rng.choice([None, 0, .5, 1])},
                    constraints={"min_total": rng.randrange(5), "max_moves": rng.randrange(5),
                                 "max_deletes": rng.randrange(5), "min_retained": {"test": rng.randrange(3)}})
            actual, expected = plan(d), optimum(d)
            self.assertEqual(actual["status"], "INFEASIBLE" if expected is None else "OPTIMAL", trial)
            if expected is not None:
                self.assertEqual((actual["cost"], actual["assignment"]), (expected[0][0], expected[1]), trial)

    def test_apply_new_manifest_and_unchanged_source(self):
        d = doc([sample("A", content="same"), sample("B", "test", content="same")])
        before = copy.deepcopy(d)
        manifest = apply(d, plan(d))
        self.assertTrue(check(d, manifest)["valid"])
        self.assertEqual(d, before)

    def test_all_example_fixtures(self):
        for path in (Path(__file__).parents[1] / "examples").glob("*.json"):
            d = json.loads(path.read_text())
            expected = optimum(d)
            actual = plan(d)
            self.assertEqual(actual["status"], "INFEASIBLE" if expected is None else "OPTIMAL", path.name)
            if expected:
                self.assertEqual(actual["cost"], expected[0][0], path.name)


if __name__ == "__main__":
    unittest.main()
