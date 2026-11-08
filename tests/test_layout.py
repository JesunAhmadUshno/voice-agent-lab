"""Portfolio standard checks: required files exist, no public grade, and the README headline
matches the evidence file it is computed from."""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBES = "experiments/runs/2026-11-07-probes-aarch64.json"
REQUIRED = ["README.md", "PROPOSAL.md", "REPORT.md", "CHANGELOG.md", "CITATION.cff", "SECURITY.md", "LICENSE",
            "src/voice_agent.py", "src/voice_pipeline.py", "src/latency_lab.py", "src/run_learn.py",
            "src/run_build.py", "src/run_deep.py", "src/run_probes.py",
            "experiments/cases/cases_learn.json", "experiments/cases/cases_build.json",
            "experiments/cases/cases_deep.json", "experiments/cases/cases_paraphrase.json",
            "experiments/runs/2026-11-05-learn-muse-vm.json", "experiments/runs/2026-11-05-deep-muse-vm.json",
            PROBES, "results/build.json",
            "docs/decisions/0001-not-pre-registered.md", "docs/decisions/0002-stand-in-components.md"]
PUBLIC = ["README.md", "PROPOSAL.md", "REPORT.md", "CHANGELOG.md", "docs/publicity.md", "site/src/App.jsx"]
GRADE = re.compile(r"of 10,000|/ ?10,?000|Grade:|grade [\d,]+|\| Total /1000")


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


class Layout(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [p for p in REQUIRED if not os.path.exists(os.path.join(ROOT, p))]
        self.assertFalse(missing, "missing: " + ", ".join(missing))

    def test_no_public_grade(self):
        paths = PUBLIC + ["fanout/" + n for n in sorted(os.listdir(os.path.join(ROOT, "fanout")))]
        for path in paths:
            hit = GRADE.search(read(path))
            self.assertIsNone(hit, f"{path} carries a grade ({hit and hit.group(0)}); grades are internal")

    def test_grade_pattern_catches_a_grade(self):
        self.assertIsNotNone(GRADE.search("Grade: 7,700 of 10,000 for this level."))

    def test_headline_matches_the_evidence(self):
        with open(os.path.join(ROOT, PROBES), encoding="utf-8") as f:
            p = json.load(f)
        sp = p["repeated_runs"]["spread"]
        share, med = sp["wav_share_of_mean_total"], sp["median_total_median_us"]
        self.assertEqual(sp["dominant_stage_cases"]["values"], [20] * 5)
        self.assertEqual(sp["within_budget"]["values"], [20] * 5)
        headline = re.search(r"^\*\*Headline\.\*\* (.+)$", read("README.md"), re.M).group(1)
        expected = [
            "largest stage in 20 of 20 turns",
            f"took {share['mean'] * 100:.1f}% of the mean turn",
            f"(95% t interval {share['ci95_mean'][0] * 100:.1f} to {share['ci95_mean'][1] * 100:.1f}%, "
            f"{p['repeated_runs']['runs']} runs on one machine)",
            f"the median turn took {med['mean'] / 1000:.3f} ms",
            f"(95% t interval {med['ci95_mean'][0] / 1000:.3f} to {med['ci95_mean'][1] / 1000:.3f} ms)",
            f"understood only {p['paraphrase']['intent_correct']} of {p['paraphrase']['n']} held-out paraphrases",
        ]
        for piece in expected:
            self.assertIn(piece, headline)


if __name__ == "__main__":
    unittest.main()
