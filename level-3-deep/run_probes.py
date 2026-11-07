"""Three cheap add-on probes for the Deep study. Writes results_probes.json.

Run: python level-3-deep/run_probes.py   (about 10 s on CPU)

It never touches results_deep.json. The probes:

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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from latency_lab import summarize, time_callable  # noqa: E402
from run_deep import measure_case  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "level-1-learn"))
from voice_agent import normalize, stage_intent  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "level-2-build"))
from voice_pipeline import run_core_turn, synthesize_samples  # noqa: E402

RUNS = 5
TTFW_SAMPLES = 30


def spread(values):
    return {"min": round(min(values), 3), "max": round(max(values), 3),
            "mean": round(statistics.mean(values), 3),
            "stdev": round(statistics.stdev(values), 3),
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


def main():
    with open(os.path.join(HERE, "cases_deep.json"), encoding="utf-8") as f:
        single = json.load(f)["single"]
    with open(os.path.join(HERE, "cases_paraphrase.json"), encoding="utf-8") as f:
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
    path = os.path.join(HERE, "results_probes.json")
    with open(path, "w", encoding="utf-8") as f:
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
