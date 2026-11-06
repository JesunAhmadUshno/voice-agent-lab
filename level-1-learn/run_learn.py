"""Run all Learn cases and the barge-in scenarios, write results.

Run: python level-1-learn/run_learn.py
Writes level-1-learn/results_learn.json.

Correctness fields (intents, responses, frame counts, drops) are
deterministic. Latency fields are measured wall-clock: each stage
is timed with time.perf_counter_ns over a batch of calls and the
mean per call is reported, so latency values vary between runs.
No latency number in the output is invented or simulated.
"""
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from voice_agent import (VoiceSession, assess_budget, run_turn,  # noqa: E402
                         stage_answer, stage_frame, stage_intent, stage_tts)

BUDGET_US = 5000.0  # 5 ms budget for the sum of measured text-stage means
REPEATS = 2000      # calls per stage per case in each timing batch
TIMING_RUNS = 5     # batches per stage; the median batch mean is reported


def time_stage_us(fn, arg):
    """Measured mean microseconds per call for one stage function.

    Times TIMING_RUNS batches of REPEATS calls each with
    perf_counter_ns and returns the median batch mean.
    """
    means = []
    for _ in range(TIMING_RUNS):
        start = time.perf_counter_ns()
        for _ in range(REPEATS):
            fn(arg)
        elapsed = time.perf_counter_ns() - start
        means.append(elapsed / REPEATS / 1000.0)
    return round(statistics.median(means), 3)


def measure_case(case):
    turn = run_turn(case["transcript"])
    framed_in = turn["normalized"]
    stage_us = {
        "frame_in_us": time_stage_us(stage_frame, case["transcript"]),
        "intent_us": time_stage_us(stage_intent, framed_in),
        "answer_us": time_stage_us(
            lambda pair: stage_answer(pair[0], pair[1]),
            (turn["intent"], turn["slots"])),
        "tts_plan_us": time_stage_us(stage_tts, turn["response"]),
    }
    budget = assess_budget(stage_us, BUDGET_US)
    return {
        "case_id": case["case_id"],
        "transcript": case["transcript"],
        "normalized": turn["normalized"],
        "frames_in": turn["frames_in"],
        "intent": turn["intent"],
        "expected_intent": case["expected_intent"],
        "intent_correct": turn["intent"] == case["expected_intent"],
        "slots": turn["slots"],
        "response": turn["response"],
        "expected_response": case["expected_response"],
        "response_correct": turn["response"] == case["expected_response"],
        "tts_frames": turn["tts"]["frames"],
        "tts_frame_count": turn["tts"]["frame_count"],
        "tts_word_count": turn["tts"]["word_count"],
        "tts_est_speech_ms": turn["tts"]["est_speech_ms"],
        "stage_us": stage_us,
        "total_stage_us": budget["total_us"],
        "budget_us": budget["budget_us"],
        "within_budget": budget["within_budget"],
    }


def run_barge_in():
    """Two deterministic barge-in scenarios. Counts are exact."""
    out = []
    s = VoiceSession()
    s.hear("What is the weather in Toronto")
    total1 = len(s.frames)
    s.play_one_frame()
    s.play_one_frame()
    hit = s.interrupt("What time is it")
    out.append({
        "scenario_id": "B1",
        "first_transcript": "What is the weather in Toronto",
        "first_frames_total": total1,
        "frames_played_before_interrupt": hit["played_before"],
        "interrupt_transcript": "What time is it",
        "frames_dropped": hit["dropped"],
        "cancelled": hit["cancelled"],
        "new_intent": hit["turn"]["intent"],
        "new_response": hit["turn"]["response"],
        "state_after": s.state,
    })
    s = VoiceSession()
    s.hear("What can you do")
    total2 = len(s.frames)
    s.play_one_frame()
    hit = s.interrupt("Stop")
    out.append({
        "scenario_id": "B2",
        "first_transcript": "What can you do",
        "first_frames_total": total2,
        "frames_played_before_interrupt": hit["played_before"],
        "interrupt_transcript": "Stop",
        "frames_dropped": hit["dropped"],
        "cancelled": hit["cancelled"],
        "new_intent": None,
        "new_response": None,
        "state_after": s.state,
    })
    return out


def main():
    with open(os.path.join(HERE, "cases_learn.json"), encoding="utf-8") as f:
        cases = json.load(f)
    results = [measure_case(c) for c in cases]
    for r in results:
        print(f"{r['case_id']} intent={r['intent']} "
              f"correct={r['intent_correct']} "
              f"response_correct={r['response_correct']} "
              f"total_stage_us={r['total_stage_us']:.3f} "
              f"within_budget={r['within_budget']}")
    barge = run_barge_in()
    for b in barge:
        print(f"{b['scenario_id']} barge-in: played={b['frames_played_before_interrupt']} "
              f"of {b['first_frames_total']}, dropped={b['frames_dropped']}, "
              f"cancelled={b['cancelled']}, state={b['state_after']}")
    totals = [r["total_stage_us"] for r in results]
    summary = {
        "cases": len(results),
        "intent_correct": sum(1 for r in results if r["intent_correct"]),
        "response_correct": sum(1 for r in results if r["response_correct"]),
        "within_budget": sum(1 for r in results if r["within_budget"]),
        "barge_in_scenarios": len(barge),
        "barge_in_frames_dropped": sum(b["frames_dropped"] for b in barge),
        "mean_total_stage_us": round(statistics.mean(totals), 3),
        "max_total_stage_us": round(max(totals), 3),
    }
    out = {
        "level": "1-learn",
        "label": ("simulated audio framing, text transcripts stand in for "
                  "ASR output, text responses stand in for TTS output, "
                  "no real ASR or TTS model, CPU only, Muse VM"),
        "method": (f"Per stage, {TIMING_RUNS} batches of {REPEATS} calls "
                   "timed with time.perf_counter_ns; the median batch mean "
                   "per call is reported in microseconds. Correctness "
                   "fields are deterministic; latency fields are measured "
                   "and vary between runs."),
        "timing_runs": TIMING_RUNS,
        "repeats_per_batch": REPEATS,
        "budget_us": BUDGET_US,
        "summary": summary,
        "cases": results,
        "barge_in": barge,
    }
    path = os.path.join(HERE, "results_learn.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Summary: intent {summary['intent_correct']} of {summary['cases']}, "
          f"response {summary['response_correct']} of {summary['cases']}, "
          f"within budget {summary['within_budget']} of {summary['cases']}, "
          f"mean total stage {summary['mean_total_stage_us']} us, "
          f"max {summary['max_total_stage_us']} us")
    print("Wrote", path)
    ok = (summary["intent_correct"] == summary["cases"]
          and summary["response_correct"] == summary["cases"]
          and summary["within_budget"] == summary["cases"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
