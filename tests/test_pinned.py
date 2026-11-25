import random
import unittest

from pattern_guard import analyse, fix_mcq
from pattern_guard.quiz import answer_index, pinned_slots


def q(i, answer_slot, pinned=None, n=4):
    opts = [f"Q{i} option {k}" for k in range(n)]
    if pinned is not None:
        opts[pinned] = "All of the above"
    return {"q": f"Question {i}", "options": opts, "answer": answer_slot}


class PinnedOptions(unittest.TestCase):
    def test_detects_common_pinned_wordings(self):
        opts = ["Cache", "All of the above", "None of these", "A and B", "Both A and C", "RAM"]
        self.assertEqual(pinned_slots(opts), {1, 2, 3, 4})

    def test_pinned_distractor_never_moves(self):
        quiz = [q(i, i % 3, pinned=3) for i in range(8)]  # key ABCABCAB, "All of the above" last
        for seed in range(25):
            fixed = fix_mcq(quiz, seed=seed)
            for orig, new in zip(quiz, fixed):
                self.assertEqual(new["options"][3], "All of the above")
                self.assertEqual(sorted(new["options"]), sorted(orig["options"]))
                self.assertEqual(new["options"][new["answer"]], orig["options"][orig["answer"]])
            key = [answer_index(x) for x in fixed]
            self.assertTrue(analyse(key, 4).ok, key)

    def test_pinned_correct_answer_keeps_its_slot(self):
        quiz = [q(i, i % 4) for i in range(8)]
        quiz[2] = q(2, 3, pinned=3)  # correct answer is "All of the above"
        for seed in range(25):
            fixed = fix_mcq(quiz, seed=seed)
            self.assertEqual(fixed[2]["answer"], 3)
            self.assertEqual(fixed[2]["options"][3], "All of the above")
            key = [answer_index(x) for x in fixed]
            self.assertTrue(analyse(key, 4).ok, key)


if __name__ == "__main__":
    unittest.main()
