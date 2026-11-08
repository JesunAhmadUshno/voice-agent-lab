"""Run the Build evaluation and write results/build.json.

Run: python src/run_build.py

The results file is fully deterministic: it holds no wall-clock
field. Every value is a count, a sample count, a duration derived
from a sample count, a byte size, or a score over labelled cases,
so two runs produce a byte-identical file.
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from voice_agent import normalize, run_turn  # noqa: E402
from voice_pipeline import AudioSession, DialogueSession, run_core_turn, simulate_asr, word_error_rate  # noqa: E402


def run_single(cases):
    rows = []
    for case in cases:
        got = run_core_turn(case["transcript"])
        rows.append({
            "case_id": case["case_id"],
            "transcript": case["transcript"],
            "intent": got["intent"],
            "expected_intent": case["expected_intent"],
            "intent_correct": got["intent"] == case["expected_intent"],
            "response": got["response"],
            "expected_response": case["expected_response"],
            "response_correct":
                got["response"] == case["expected_response"],
            "audio": got["audio"],
            "streaming": got["streaming"],
        })
    return rows


def run_dialogues(dialogues):
    rows = []
    for dlg in dialogues:
        session = DialogueSession()
        turns = []
        for turn in dlg["turns"]:
            got = session.hear(turn["transcript"])
            turns.append({
                "transcript": turn["transcript"],
                "intent": got["intent"],
                "expected_intent": turn["expected_intent"],
                "intent_correct":
                    got["intent"] == turn["expected_intent"],
                "response": got["response"],
                "expected_response": turn["expected_response"],
                "response_correct":
                    got["response"] == turn["expected_response"],
            })
        rows.append({"dialogue_id": dlg["dialogue_id"], "turns": turns})
    return rows


def run_noise(cases):
    rows = []
    for case in cases:
        heard = simulate_asr(case["transcript"])
        got = run_turn(heard)
        rows.append({
            "case_id": case["case_id"],
            "transcript": case["transcript"],
            "asr_heard": heard,
            "wer": word_error_rate(normalize(case["transcript"]), heard),
            "intent": got["intent"],
            "expected_intent": case["expected_intent"],
            "intent_correct": got["intent"] == case["expected_intent"],
        })
    return rows


def run_barge_in(scenarios):
    rows = []
    for sc in scenarios:
        session = AudioSession()
        session.hear(sc["first_transcript"])
        total = len(session.frames)
        session.play_frames(sc["play_frames"])
        hit = session.interrupt(sc["interrupt_transcript"])
        rows.append({
            "scenario_id": sc["scenario_id"],
            "first_transcript": sc["first_transcript"],
            "first_frames_total": total,
            "frames_played_before_interrupt": hit["played_before"],
            "interrupt_transcript": sc["interrupt_transcript"],
            "frames_dropped": hit["dropped"],
            "cancelled": hit["cancelled"],
            "new_intent": (hit["turn"]["intent"] if hit["turn"] else None),
            "new_response": (hit["turn"]["response"]
                             if hit["turn"] else None),
            "state_after": session.state,
        })
    return rows


def main():
    with open(os.path.join(ROOT, "experiments", "cases", "cases_build.json"),
              encoding="utf-8") as f:
        cases = json.load(f)
    single = run_single(cases["single"])
    dialogues = run_dialogues(cases["dialogues"])
    noise = run_noise(cases["single"])
    barge = run_barge_in(cases["barge_in"])

    dlg_turns = [t for d in dialogues for t in d["turns"]]
    firsts = [r["streaming"]["first_correct_partial"] for r in single]
    summary = {
        "single_cases": len(single),
        "single_intent_correct":
            sum(1 for r in single if r["intent_correct"]),
        "single_response_correct":
            sum(1 for r in single if r["response_correct"]),
        "dialogues": len(dialogues),
        "dialogue_turns": len(dlg_turns),
        "dialogue_intent_correct":
            sum(1 for t in dlg_turns if t["intent_correct"]),
        "dialogue_response_correct":
            sum(1 for t in dlg_turns if t["response_correct"]),
        "noise_cases": len(noise),
        "noise_intent_correct":
            sum(1 for r in noise if r["intent_correct"]),
        "noise_mean_wer":
            round(statistics.mean(r["wer"] for r in noise), 4),
        "barge_in_scenarios": len(barge),
        "barge_in_frames_dropped":
            sum(b["frames_dropped"] for b in barge),
        "audio_total_wav_bytes": sum(r["audio"]["wav_bytes"]
                                     for r in single),
        "audio_total_duration_ms": round(
            sum(r["audio"]["duration_ms"] for r in single), 3),
        "audio_total_frames": sum(r["audio"]["frame_count"]
                                  for r in single),
        "audio_speech_frames": sum(r["audio"]["speech_frames"]
                                   for r in single),
        "audio_silence_frames": sum(r["audio"]["silence_frames"]
                                    for r in single),
        "streaming_cases_with_first_correct":
            sum(1 for x in firsts if x is not None),
        "streaming_mean_first_correct_partial": round(
            statistics.mean(x for x in firsts if x is not None), 3),
        "streaming_stable_cases":
            sum(1 for r in single if r["streaming"]["stable_from_first"]),
        "streaming_early_cases":
            sum(1 for r in single
                if r["streaming"]["first_correct_partial"] is not None
                and r["streaming"]["first_correct_partial"]
                < r["streaming"]["partials"]),
    }
    out = {
        "level": "2-build",
        "label": ("end-to-end voice loop on CPU: transcript partials "
                  "in (simulated ASR, no ASR model), Learn rule answer "
                  "reused by import (no LLM), tone-synthesized WAV "
                  "out (real WAV data, no intelligible speech, no "
                  "TTS model), Muse VM, standard library only"),
        "method": ("Single turns run the core pipeline; dialogues run "
                   "a stateful DialogueSession; noise runs push the "
                   "same transcripts through a deterministic simulated "
                   "ASR map (weather to whether, the dropped) and are "
                   "scored with word error rate; barge-in runs over "
                   "real 20 ms WAV frames. No wall-clock field exists "
                   "in this file: durations are sample counts divided "
                   "by 8000 Hz, so the file is byte-identical across "
                   "runs."),
        "summary": summary,
        "single": single,
        "dialogues": dialogues,
        "noise": noise,
        "barge_in": barge,
    }
    path = os.path.join(ROOT, "results", "build.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Single: intent {summary['single_intent_correct']} of "
          f"{summary['single_cases']}, response "
          f"{summary['single_response_correct']} of "
          f"{summary['single_cases']}")
    print(f"Dialogues: intent {summary['dialogue_intent_correct']} of "
          f"{summary['dialogue_turns']} turns, response "
          f"{summary['dialogue_response_correct']} of "
          f"{summary['dialogue_turns']}")
    print(f"Noise: intent {summary['noise_intent_correct']} of "
          f"{summary['noise_cases']}, mean WER "
          f"{summary['noise_mean_wer']}")
    print(f"Barge-in: {summary['barge_in_scenarios']} scenarios, "
          f"{summary['barge_in_frames_dropped']} frames dropped")
    print(f"Audio: {summary['audio_total_wav_bytes']} WAV bytes, "
          f"{summary['audio_total_duration_ms']} ms, "
          f"{summary['audio_total_frames']} frames")
    print("Wrote", path)
    ok = (summary["single_intent_correct"] == summary["single_cases"]
          and summary["single_response_correct"]
          == summary["single_cases"]
          and summary["dialogue_intent_correct"]
          == summary["dialogue_turns"]
          and summary["dialogue_response_correct"]
          == summary["dialogue_turns"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
