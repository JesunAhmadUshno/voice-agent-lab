"""Deep-level latency budget study, stdlib only.

Build (level-2-build) proved the voice loop runs end to end and
reported audio duration from sample counts. Duration is content
length, not system latency. This module measures the system
latency of every stage that actually runs locally, reusing the
Learn and Build code by import, and puts a modelled cloud
pipeline next to the measurements.

Measured (local, this machine, time.perf_counter_ns):
- frame and VAD split of a response WAV sample list
- streaming partial intent tracing of a transcript
- intent classification plus template answer
- WAV tone synthesis of a response
- barge-in handling over audio frames (drop path and full path)

Modelled only (never measured, no network, no cloud call):
- a cloud speech pipeline built from the stated constants below.
  Every function and file that reports it labels it modelled.

The inherited substitutions stay in force and are named in
DEEP-SPEC.md: no real ASR model, no real TTS voice, no LLM. The
measured synthesis time is the cost of a sine loop, and the
measured answer time is the cost of a keyword rule. Neither is
presented as the cost of a speech or language model.
"""
import math
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "level-1-learn"))
sys.path.insert(0, os.path.join(HERE, "..", "level-2-build"))
from voice_agent import stage_answer, stage_intent  # noqa: E402
from voice_pipeline import (  # noqa: E402
    AudioSession,
    audio_frames,
    frame_is_speech,
    streaming_trace,
    synthesize_samples,
    synthesize_wav,
)

# Design budget, set in DEEP-SPEC.md before measuring.
BUDGET_US = 100000.0        # 100 ms for the sum of stage medians
CEILING_US = 500000.0       # 500 ms hard ceiling, the exit gate
BARGE_DROP_BUDGET_US = 5000.0
STAGE_BUDGET_US = {
    "frame_vad": 10000.0,
    "streaming": 10000.0,
    "intent_answer": 5000.0,
    "wav_synthesis": 70000.0,
}

# Modelled cloud constants. Stated modelling choices only, not
# measurements of any real service. Labelled modelled everywhere.
CLOUD_NETWORK_RTT_MS = 80.0
CLOUD_ASR_FINAL_MS = 300.0
CLOUD_LLM_ANSWER_MS = 700.0
CLOUD_TTS_BASE_MS = 100.0
CLOUD_TTS_PER_WORD_MS = 5.0


def percentile(values, pct):
    """Nearest-rank percentile of a non-empty list.

    Hand check on [10, 20, 30, 40]: p25 is 10 (rank 1), p50 is
    20 (rank 2), p90 is 40 (rank 4), p99 is 40 (rank 4).
    """
    ordered = sorted(values)
    rank = max(1, math.ceil(pct / 100.0 * len(ordered)))
    return ordered[rank - 1]


def summarize(samples_us):
    """Summary stats for pooled per-call microsecond samples.

    Hand check on [10, 20, 30, 40]: n 4, mean 25.0, median 25.0
    (statistics.median averages the middle pair), p90 40,
    p99 40, min 10, max 40.
    """
    return {
        "n": len(samples_us),
        "mean_us": round(statistics.mean(samples_us), 3),
        "median_us": round(statistics.median(samples_us), 3),
        "p90_us": round(percentile(samples_us, 90), 3),
        "p99_us": round(percentile(samples_us, 99), 3),
        "min_us": round(min(samples_us), 3),
        "max_us": round(max(samples_us), 3),
    }


def time_callable(fn, samples, batches=3, warmup=3):
    """Time fn() individually and pool the per-call samples.

    Runs warmup untimed calls, then batches rounds of
    samples // batches timed calls each (at least 1 per batch),
    timing every call with time.perf_counter_ns. Returns the
    pooled list of per-call microseconds. The pooled count can
    differ from samples when samples is not divisible by
    batches; the summary reports the true n.
    """
    for _ in range(warmup):
        fn()
    per_batch = max(1, samples // batches)
    pooled = []
    for _ in range(batches):
        for _ in range(per_batch):
            start = time.perf_counter_ns()
            fn()
            pooled.append((time.perf_counter_ns() - start) / 1000.0)
    return pooled


def time_setup_callable(setup, fn, samples, batches=3, warmup=1):
    """Time fn(state) where setup() builds a fresh state per call.

    For stateful stages (barge-in): setup runs untimed before
    every timed call, so the measurement covers only fn on the
    prepared state. Warmup rounds run setup plus fn untimed.
    """
    for _ in range(warmup):
        fn(setup())
    per_batch = max(1, samples // batches)
    pooled = []
    for _ in range(batches):
        for _ in range(per_batch):
            state = setup()
            start = time.perf_counter_ns()
            fn(state)
            pooled.append((time.perf_counter_ns() - start) / 1000.0)
    return pooled


def stage_frame_vad(samples):
    """Frame and VAD split: frames plus the speech frame count."""
    frames = audio_frames(samples)
    speech = sum(1 for f in frames if frame_is_speech(f))
    return {"frame_count": len(frames), "speech_frames": speech,
            "silence_frames": len(frames) - speech}


def stage_streaming(transcript, expected_intent):
    """Streaming partial intent trace of one transcript."""
    return streaming_trace(transcript, expected_intent)


def stage_intent_answer(normalized):
    """Intent classification plus the template answer."""
    found = stage_intent(normalized)
    return {"intent": found["intent"], "slots": found["slots"],
            "response": stage_answer(found["intent"], found["slots"])}


def stage_wav_synthesis(response_text):
    """The Build tone synthesis record for one response."""
    return synthesize_wav(response_text)


def setup_barge(first_transcript, play_frames):
    """Build a playing AudioSession, untimed. Returns the session."""
    session = AudioSession()
    session.hear(first_transcript)
    session.play_frames(play_frames)
    return session


def barge_drop(session):
    """Drop path: interrupt a playing session with stop."""
    return session.interrupt("Stop")


def barge_full(session, interrupt_transcript):
    """Full path: interrupt with a new utterance (a whole new turn)."""
    return session.interrupt(interrupt_transcript)


def modelled_cloud(response_text):
    """Modelled cloud pipeline total for one response. MODELLED.

    Built only from the stated constants above: network 80 ms,
    ASR final 300 ms, LLM answer 700 ms, TTS 100 ms plus 5 ms
    per response word. Hand check: a 1-word response totals
    1185 ms; a 5-word response totals 1205 ms. This is a model,
    never a measurement, and no real service is named.
    """
    words = len(response_text.split())
    tts = CLOUD_TTS_BASE_MS + CLOUD_TTS_PER_WORD_MS * words
    total = (CLOUD_NETWORK_RTT_MS + CLOUD_ASR_FINAL_MS
             + CLOUD_LLM_ANSWER_MS + tts)
    return {"label": "modelled, not measured",
            "network_rtt_ms": CLOUD_NETWORK_RTT_MS,
            "asr_final_ms": CLOUD_ASR_FINAL_MS,
            "llm_answer_ms": CLOUD_LLM_ANSWER_MS,
            "tts_first_audio_ms": tts,
            "response_words": words,
            "total_ms": total}


def assess_turn_budget(stage_medians_us, budget_us=BUDGET_US):
    """Sum the per-turn stage medians and compare to the budget.

    Hand check: medians of 100, 200, 300, 400 sum to 1000, which
    is within a budget of 100000 and outside a budget of 500.
    Stage shares are reported against STAGE_BUDGET_US.
    """
    total = round(sum(stage_medians_us.values()), 3)
    shares = {name: {"median_us": med,
                     "stage_budget_us": STAGE_BUDGET_US[name],
                     "within_stage_budget":
                         med <= STAGE_BUDGET_US[name]}
              for name, med in stage_medians_us.items()}
    return {"total_median_us": total, "budget_us": budget_us,
            "within_budget": total <= budget_us,
            "ceiling_us": CEILING_US,
            "within_ceiling": total <= CEILING_US,
            "stage_shares": shares}


def response_size(response_text):
    """Deterministic size record for one response. No timing."""
    samples = synthesize_samples(response_text)
    vad = stage_frame_vad(samples)
    return {"words": len(response_text.split()),
            "sample_count": len(samples),
            "duration_ms": round(len(samples) * 1000 / 8000, 3),
            "frame_count": vad["frame_count"],
            "speech_frames": vad["speech_frames"],
            "silence_frames": vad["silence_frames"]}
