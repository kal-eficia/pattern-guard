import json
import unittest
from pathlib import Path

from pattern_guard import analyse, check_mcq, check_sort, fix_file, plan_key
from pattern_guard.core import LETTERS

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "networks-quiz.json"


def k(s):
    return [LETTERS.index(c) for c in s]


def rules(rep):
    return {f.rule for f in rep.findings if f.severity == "fail"}


class Detection(unittest.TestCase):
    def test_runs(self):
        self.assertIn("run", rules(analyse(k("BAAAC"), 4)))

    def test_back_to_back_repeat_is_strict_by_default(self):
        self.assertIn("repeat", rules(analyse(k("CAADB"), 4)))
        self.assertNotIn("repeat", rules(analyse(k("CAADB"), 4, strict=False)))

    def test_staircases_both_ways(self):
        self.assertIn("staircase", rules(analyse(k("ABCD"), 4)))
        self.assertIn("staircase", rules(analyse(k("DCB"), 4)))

    def test_alternation(self):
        self.assertIn("alternation", rules(analyse(k("ACAC"), 4)))

    def test_cycles(self):
        self.assertIn("cycle", rules(analyse(k("ACBDACBD"), 4)))

    def test_lopsided(self):
        self.assertIn("lopsided", rules(analyse(k("BCBDBABDB"), 4, strict=False)))

    def test_clean_key(self):
        self.assertTrue(analyse(k("CADBDACB"), 4).clean)


class Planning(unittest.TestCase):
    def test_planned_keys_are_clean_and_balanced(self):
        for seed in range(25):
            for n, opts in ((8, 4), (12, 4), (20, 4), (10, 3), (15, 5)):
                key = plan_key(n, opts, seed=seed)
                rep = analyse(key, opts)
                self.assertTrue(rep.ok, (seed, n, opts, rep.key_letters(), rep.findings))
                counts = [key.count(o) for o in range(opts)]
                self.assertLessEqual(max(counts) - min(counts), 1)

    def test_seed_is_reproducible(self):
        self.assertEqual(plan_key(12, 4, seed=9), plan_key(12, 4, seed=9))


class Files(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EXAMPLE.read_text())

    def test_example_is_flagged(self):
        self.assertFalse(check_mcq(self.data["questions"]).ok)
        self.assertFalse(check_sort(self.data["questions"][-1]).ok)

    def test_fix_keeps_answers_correct(self):
        before = {q["q"]: q["options"][q["answer"]] if isinstance(q["answer"], int) else q["answer"]
                  for q in self.data["questions"] if "options" in q}
        fixed = fix_file(self.data, seed=4)
        for q in fixed["questions"]:
            if "options" in q:
                got = q["options"][q["answer"]] if isinstance(q["answer"], int) else q["answer"]
                self.assertEqual(got, before[q["q"]])
                self.assertIn(got, q["options"])
        self.assertTrue(check_mcq(fixed["questions"]).ok)
        self.assertTrue(check_sort(fixed["questions"][-1]).ok)
        self.assertEqual(sorted(i["text"] for i in fixed["questions"][-1]["items"]),
                         sorted(i["text"] for i in self.data["questions"][-1]["items"]))


if __name__ == "__main__":
    unittest.main()
