"""Run the Deep latency budget study and write results_deep.json.

Run: python level-3-deep/run_deep.py

Local stage latencies are measured wall-clock values (each call
timed individually with time.perf_counter_ns, pooled over 3
batches, after warmup), so they vary between runs and this file
is NOT byte-identical across runs. The deterministic fields
(intents, responses, frame counts, drops, audio sizes, and all
modelled cloud totals) are identical across runs, and the exit
code gates on them plus the 500 ms hard ceiling from
DEEP-SPEC.md. The cloud side is modelled only, from stated
constants, and is labelled modelled in the output.
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from latency_lab import (  # noqa: E402
    assess_turn_budget,
    barge_drop,
    barge_full,
    modelled_cloud,
    response_size,
    setup_barge,
    stage_frame_vad,
    stage_intent_answer,
    stage_streaming,
    stage_wav_synthesis,
    summarize,
    time_callable,
    time_setup_callable,
)

sys.path.insert(0, os.path.join(HERE, "..", "level-2-build"))
from voice_pipeline import run_core_turn, synthesize_samples  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "level-1-learn"))
from voice_agent import normalize  # noqa: E402

SAMPLES = {"intent_answer": 300, "streaming": 300, "frame_vad": 100,
           "wav_synthesis": 30, "barge_drop": 60, "barge_full": 20}


def measure_case(case):
    got = run_core_turn(case["transcript"])
    response = got["response"]
    normalized = normalize(case["transcript"])
    samples = synthesize_samples(response)
    timings = {
        "frame_vad": summarize(time_callable(
            lambda: stage_frame_vad(samples), SAMPLES["frame_vad"])),
        "streaming": summarize(time_callable(
            lambda: stage_streaming(case["transcript"],
                                    case["expected_intent"]),
            SAMPLES["streaming"])),
        "intent_answer": summarize(time_callable(
            lambda: stage_intent_answer(normalized),
            SAMPLES["intent_answer"])),
        "wav_synthesis": summarize(time_callable(
            lambda: stage_wav_synthesis(response),
            SAMPLES["wav_synthesis"])),
    }
    medians = {k: v["median_us"] for k, v in timings.items()}
    budget = assess_turn_budget(medians)
    cloud = modelled_cloud(response)
    local_ms = round(budget["total_median_us"] / 1000.0, 3)
    return {
        "case_id": case["case_id"],
        "transcript": case["transcript"],
        "intent": got["intent"],
        "expected_intent": case["expected_intent"],
        "intent_correct": got["intent"] == case["expected_intent"],
        "response": response,
        "expected_response": case["expected_response"],
        "response_correct": response == case["expected_response"],
        "audio": got["audio"],
        "size": response_size(response),
        "stage_us": timings,
        "total_median_us": budget["total_median_us"],
        "within_budget": budget["within_budget"],
        "within_ceiling": budget["within_ceiling"],
        "stage_shares": budget["stage_shares"],
        "modelled_cloud": cloud,
        "modelled_cloud_to_local_ratio": round(
            cloud["total_ms"] / local_ms, 3) if local_ms else None,
    }


def run_barge(scenarios):
    rows = []
    for sc in scenarios:
        # Deterministic correctness run with the real transcript.
        probe = setup_barge(sc["first_transcript"], sc["play_frames"])
        total_frames = len(probe.frames)
        hit = probe.interrupt(sc["interrupt_transcript"])
        # Timed drop path: fresh playing session per call, setup
        # untimed, interrupt with stop timed.
        drop = summarize(time_setup_callable(
            lambda: setup_barge(sc["first_transcript"],
                                sc["play_frames"]),
            barge_drop, SAMPLES["barge_drop"]))
        # Timed full path: interrupt with the scenario transcript.
        full = summarize(time_setup_callable(
            lambda: setup_barge(sc["first_transcript"],
                                sc["play_frames"]),
            lambda s: barge_full(s, sc["interrupt_transcript"]),
            SAMPLES["barge_full"]))
        rows.append({
            "scenario_id": sc["scenario_id"],
            "first_transcript": sc["first_transcript"],
            "first_frames_total": total_frames,
            "frames_played_before_interrupt": hit["played_before"],
            "interrupt_transcript": sc["interrupt_transcript"],
            "frames_dropped": hit["dropped"],
            "cancelled": hit["cancelled"],
            "new_intent": (hit["turn"]["intent"] if hit["turn"]
                           else None),
            "drop_us": drop,
            "drop_within_budget": drop["median_us"] <= 5000.0,
            "full_us": full,
        })
    return rows


def main():
    with open(os.path.join(HERE, "cases_deep.json"),
              encoding="utf-8") as f:
        cases = json.load(f)
    rows = [measure_case(c) for c in cases["single"]]
    for r in rows:
        print(f"{r['case_id']} intent={r['intent']} "
              f"correct={r['intent_correct']} "
              f"total_median_us={r['total_median_us']:.3f} "
              f"within_budget={r['within_budget']} "
              f"modelled_cloud_ms={r['modelled_cloud']['total_ms']}")
    barge = run_barge(cases["barge_in"])
    for b in barge:
        print(f"{b['scenario_id']} barge-in: dropped="
              f"{b['frames_dropped']}, drop_median_us="
              f"{b['drop_us']['median_us']:.3f}, full_median_us="
              f"{b['full_us']['median_us']:.3f}")
    totals = [r["total_median_us"] for r in rows]
    summary = {
        "cases": len(rows),
        "intent_correct": sum(1 for r in rows if r["intent_correct"]),
        "response_correct":
            sum(1 for r in rows if r["response_correct"]),
        "within_budget": sum(1 for r in rows if r["within_budget"]),
        "within_ceiling": sum(1 for r in rows if r["within_ceiling"]),
        "mean_total_median_us": round(statistics.mean(totals), 3),
        "median_total_median_us": round(statistics.median(totals), 3),
        "max_total_median_us": round(max(totals), 3),
        "dominant_stage_cases": sum(
            1 for r in rows
            if max(r["stage_us"], key=lambda k: r["stage_us"][k]
                   ["median_us"]) == "wav_synthesis"),
        "modelled_cloud_mean_ms": round(statistics.mean(
            r["modelled_cloud"]["total_ms"] for r in rows), 3),
        "barge_in_scenarios": len(barge),
        "barge_in_frames_dropped":
            sum(b["frames_dropped"] for b in barge),
        "barge_drop_within_budget":
            sum(1 for b in barge if b["drop_within_budget"]),
    }
    out = {
        "level": "3-deep",
        "label": ("latency budget study on CPU: measured local "
                  "stage latencies for the Build voice pipeline "
                  "(frame and VAD split, streaming partial intent "
                  "tracing, Learn rule intent and answer reused by "
                  "import, tone WAV synthesis, barge-in over audio "
                  "frames; no ASR model, no TTS model, no LLM), "
                  "modelled cloud pipeline from stated constants "
                  "(modelled only, never measured), Muse VM, "
                  "standard library only"),
        "method": ("Each local stage call is timed individually "
                   "with time.perf_counter_ns after warmup, in 3 "
                   "repeated batches whose per-call samples are "
                   "pooled; per stage and case the file reports n, "
                   "mean, median, p90, p99, min, max in "
                   "microseconds (nearest-rank percentiles). "
                   "Sample counts: intent and answer 300, "
                   "streaming 300, frame and VAD 100, WAV "
                   "synthesis 30, barge-in drop 60, barge-in full "
                   "20; barge-in setups run untimed per call. "
                   "Latency fields are measured and vary between "
                   "runs, so this file is NOT byte-identical "
                   "across runs; deterministic fields (correctness, "
                   "counts, sizes, modelled totals) are identical "
                   "across runs. Cloud figures are modelled from "
                   "stated constants only: network 80 ms, ASR "
                   "final 300 ms, LLM answer 700 ms, TTS 100 ms "
                   "plus 5 ms per response word."),
        "budget_us": 100000.0,
        "ceiling_us": 500000.0,
        "samples_per_stage": SAMPLES,
        "summary": summary,
        "cases": rows,
        "barge_in": barge,
    }
    path = os.path.join(HERE, "results_deep.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Summary: intent {summary['intent_correct']} of "
          f"{summary['cases']}, response {summary['response_correct']} "
          f"of {summary['cases']}, within budget "
          f"{summary['within_budget']} of {summary['cases']}, "
          f"max total median {summary['max_total_median_us']} us, "
          f"modelled cloud mean {summary['modelled_cloud_mean_ms']} ms")
    print("Wrote", path)
    ok = (summary["intent_correct"] == summary["cases"]
          and summary["response_correct"] == summary["cases"]
          and summary["within_ceiling"] == summary["cases"]
          and summary["barge_in_frames_dropped"] == 165)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
