"""Three cheap add-on probes for the Deep study. Writes a new dated file in experiments/runs/.

Run: python src/run_probes.py [output.json]  (about 10 s on CPU)

It never touches the recorded Deep run. The probes:

1. Repeated runs: the Deep per-case stage timings are re-measured
   RUNS times with the same code and sample counts (run_deep.measure_case),
   and the spread of the run-level summary numbers is reported. This is
   between-run variance on one machine, not a second machine.
2. Time to first word: synthesizing only the first word of each response
   (960 samples, 6 frames of 20 ms) against the whole response, timed the
   same way. It answers ROADMAP v1.1 item 1 for the sine-loop synthesis
   only, not for a real TTS voice.
3. Paraphrase probe: the frozen Learn keyword rule scored on 20 held-out
   rewordings (cases_paraphrase.json). Deterministic, no timing.

All timings are measured on the machine named in the output and vary
between runs, so this file is not byte-identical across runs.
"""
import json
import os
import platform
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from latency_lab import summarize, time_callable  # noqa: E402
from run_deep import measure_case  # noqa: E402
from voice_agent import normalize, stage_intent  # noqa: E402
from voice_pipeline import run_core_turn, synthesize_samples  # noqa: E402

RUNS = 5
TTFW_SAMPLES = 30


# Two-sided 95% Student t quantiles by degrees of freedom (standard table values).
T95 = {2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 9: 2.262}


def spread(values):
    """Run-level spread, with a 95% t interval for the mean when the table has the df."""
    m, sd = statistics.mean(values), statistics.stdev(values)
    t = T95.get(len(values) - 1)
    half = t * sd / len(values) ** 0.5 if t else None
    return {"min": round(min(values), 3), "max": round(max(values), 3),
            "mean": round(m, 3), "stdev": round(sd, 3),
            "ci95_mean": [round(m - half, 3), round(m + half, 3)] if t else None,
            "values": [round(v, 3) for v in values]}


def repeated_runs(cases, runs=RUNS):
    per_run = []
    for _ in range(runs):
        rows = [measure_case(c) for c in cases]
        totals = [r["total_median_us"] for r in rows]
        wav = [r["stage_us"]["wav_synthesis"]["median_us"] for r in rows]
        per_run.append({
            "median_total_median_us": statistics.median(totals),
            "mean_total_median_us": statistics.mean(totals),
            "max_total_median_us": max(totals),
            "wav_share_of_mean_total": statistics.mean(wav) / statistics.mean(totals),
            "dominant_stage_cases": sum(
                1 for r in rows
                if max(r["stage_us"], key=lambda k: r["stage_us"][k]["median_us"]) == "wav_synthesis"),
            "within_budget": sum(1 for r in rows if r["within_budget"]),
            "p99_sum_over_budget": sum(
                1 for r in rows
                if sum(v["p99_us"] for v in r["stage_us"].values()) > 100000.0),
        })
    return {"runs": runs, "per_run": per_run,
            "spread": {k: spread([r[k] for r in per_run]) for k in per_run[0]}}


def time_to_first_word(cases):
    rows = []
    for c in cases:
        response = run_core_turn(c["transcript"])["response"]
        first = response.split()[0]
        full = summarize(time_callable(lambda: synthesize_samples(response), TTFW_SAMPLES))
        head = summarize(time_callable(lambda: synthesize_samples(first), TTFW_SAMPLES))
        rows.append({"case_id": c["case_id"], "words": len(response.split()),
                     "full_median_us": full["median_us"], "first_word_median_us": head["median_us"],
                     "full_over_first": round(full["median_us"] / head["median_us"], 3)})
    return {"samples_per_case": TTFW_SAMPLES, "cases": rows,
            "median_full_over_first": round(statistics.median(r["full_over_first"] for r in rows), 3)}


def paraphrase_probe(cases):
    rows = []
    for c in cases:
        got = stage_intent(normalize(c["transcript"]))["intent"]
        rows.append({**c, "intent": got, "intent_correct": got == c["expected_intent"]})
    return {"cases": rows, "n": len(rows), "intent_correct": sum(r["intent_correct"] for r in rows),
            "fell_to_unknown": sum(1 for r in rows if r["intent"] == "unknown")}



def evidence_path(study):
    """Where a timed run is written: the path given on the command line, or a new dated file in
    experiments/runs/. Open mode "x" refuses to overwrite, so recorded evidence is never replaced."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    host = platform.machine() or "unknown"
    return os.path.join(ROOT, "experiments", "runs", f"{time.strftime('%Y-%m-%d')}-probes-{host}.json")


def main():
    with open(os.path.join(ROOT, "experiments", "cases", "cases_deep.json"), encoding="utf-8") as f:
        single = json.load(f)["single"]
    with open(os.path.join(ROOT, "experiments", "cases", "cases_paraphrase.json"), encoding="utf-8") as f:
        para = json.load(f)["cases"]
    out = {
        "label": ("add-on probes to the Deep study: repeated-run variance of the measured local stage "
                  "timings, sine-loop time to first word, and a held-out paraphrase probe of the "
                  "keyword rule. No ASR model, no TTS model, no LLM. Timings are measured on this machine."),
        "machine": {"platform": platform.platform(), "machine": platform.machine(),
                    "python": platform.python_version()},
        "repeated_runs": repeated_runs(single),
        "time_to_first_word": time_to_first_word(single),
        "paraphrase": paraphrase_probe(para),
    }
    path = evidence_path("probes")
    with open(path, "x", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    p = out["paraphrase"]
    print(f"paraphrase intent {p['intent_correct']} of {p['n']}, unknown {p['fell_to_unknown']}")
    print("median total spread", out["repeated_runs"]["spread"]["median_total_median_us"])
    print("median full/first-word", out["time_to_first_word"]["median_full_over_first"])
    print("Wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
