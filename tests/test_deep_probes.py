"""Unit tests for the Deep add-on probes. Deterministic parts only.

Run: python -m unittest tests.test_deep_probes -v
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from run_probes import paraphrase_probe, spread  # noqa: E402


class ProbeTests(unittest.TestCase):
    def test_spread_hand_check(self):
        s = spread([1.0, 2.0, 3.0])
        self.assertEqual((s["min"], s["max"], s["mean"], s["stdev"]), (1.0, 3.0, 2.0, 1.0))
        # t(2) = 4.303, half width 4.303 * 1 / sqrt(3) = 2.484
        self.assertEqual(s["ci95_mean"], [-0.484, 4.484])

    def test_paraphrase_rule_known_hits_and_misses(self):
        got = paraphrase_probe([
            {"case_id": "x1", "transcript": "Start a 2 minute timer", "expected_intent": "timer"},
            {"case_id": "x2", "transcript": "What hour is it", "expected_intent": "time"},
        ])
        self.assertEqual(got["intent_correct"], 1)
        self.assertEqual(got["fell_to_unknown"], 1)

    def test_committed_paraphrase_result_matches_rule(self):
        with open(os.path.join(HERE, "..", "experiments", "cases", "cases_paraphrase.json"), encoding="utf-8") as f:
            cases = json.load(f)["cases"]
        run = os.path.join(HERE, "..", "experiments", "runs", "2026-11-07-probes-aarch64.json")
        with open(run, encoding="utf-8") as f:
            saved = json.load(f)["paraphrase"]
        self.assertEqual(paraphrase_probe(cases), saved)


if __name__ == "__main__":
    unittest.main()
