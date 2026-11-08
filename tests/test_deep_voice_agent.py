"""Unit tests for the Deep latency lab. Hand-computed values.

Run: python -m unittest tests.test_deep_voice_agent -v

Timing functions are tested for shape and count only (a measured
duration is never asserted to an exact value). Every exact value
asserted here is a pure function, a deterministic count, or a
modelled total computed by hand from the stated constants.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from latency_lab import (  # noqa: E402
    assess_turn_budget,
    barge_drop,
    modelled_cloud,
    percentile,
    response_size,
    setup_barge,
    stage_frame_vad,
    stage_intent_answer,
    stage_wav_synthesis,
    summarize,
    time_callable,
    time_setup_callable,
)


class TestPercentileAndSummary(unittest.TestCase):
    def test_percentile_nearest_rank_by_hand(self):
        # [10, 20, 30, 40]: ranks are ceil(pct/100 * 4):
        # p25 rank 1 is 10, p50 rank 2 is 20, p90 rank 4 is 40.
        self.assertEqual(percentile([40, 10, 30, 20], 25), 10)
        self.assertEqual(percentile([40, 10, 30, 20], 50), 20)
        self.assertEqual(percentile([40, 10, 30, 20], 90), 40)
        self.assertEqual(percentile([40, 10, 30, 20], 99), 40)

    def test_percentile_single_value(self):
        self.assertEqual(percentile([7.5], 90), 7.5)

    def test_summarize_by_hand(self):
        # [10, 20, 30, 40]: mean 25, median 25 (middle pair
        # averaged), p90 and p99 are 40, min 10, max 40.
        got = summarize([10.0, 20.0, 30.0, 40.0])
        self.assertEqual(got["n"], 4)
        self.assertEqual(got["mean_us"], 25.0)
        self.assertEqual(got["median_us"], 25.0)
        self.assertEqual(got["p90_us"], 40.0)
        self.assertEqual(got["p99_us"], 40.0)
        self.assertEqual(got["min_us"], 10.0)
        self.assertEqual(got["max_us"], 40.0)


class TestTimingShape(unittest.TestCase):
    def test_time_callable_pools_batches(self):
        # 30 requested samples in 3 batches of 10: 30 pooled
        # values, all non-negative, and fn really ran.
        calls = []

        def fn():
            calls.append(1)

        pooled = time_callable(fn, 30, batches=3, warmup=2)
        self.assertEqual(len(pooled), 30)
        self.assertTrue(all(v >= 0 for v in pooled))
        self.assertEqual(len(calls), 32)

    def test_time_setup_callable_builds_fresh_state(self):
        pooled = time_setup_callable(lambda: {"n": 0},
                                     lambda s: s.update(n=1),
                                     9, batches=3, warmup=1)
        self.assertEqual(len(pooled), 9)
        self.assertTrue(all(v >= 0 for v in pooled))


class TestStages(unittest.TestCase):
    def test_frame_vad_goodbye_by_hand(self):
        # "Goodbye." synthesizes to 960 samples: 6 frames, all
        # speech, no silence (no gap after the last word).
        from voice_pipeline import synthesize_samples
        got = stage_frame_vad(synthesize_samples("Goodbye."))
        self.assertEqual(got["frame_count"], 6)
        self.assertEqual(got["speech_frames"], 6)
        self.assertEqual(got["silence_frames"], 0)

    def test_frame_vad_weather_by_hand(self):
        # 9 words: 11200 samples, 70 frames, 54 speech, 16 silence.
        from voice_pipeline import synthesize_samples
        text = "The weather in Toronto is clear, 12 degrees Celsius."
        got = stage_frame_vad(synthesize_samples(text))
        self.assertEqual(got["frame_count"], 70)
        self.assertEqual(got["speech_frames"], 54)
        self.assertEqual(got["silence_frames"], 16)

    def test_intent_answer_weather(self):
        got = stage_intent_answer("what is the weather in toronto")
        self.assertEqual(got["intent"], "weather")
        self.assertEqual(got["response"],
                         "The weather in Toronto is clear, "
                         "12 degrees Celsius.")

    def test_intent_answer_timer_slots(self):
        got = stage_intent_answer("set a timer for 5 minutes")
        self.assertEqual(got["intent"], "timer")
        self.assertEqual(got["slots"]["seconds"], 300)
        self.assertEqual(got["response"], "Timer set for 300 seconds.")

    def test_wav_stage_matches_build_record(self):
        got = stage_wav_synthesis("Goodbye.")
        self.assertEqual(got["sample_count"], 960)
        self.assertEqual(got["duration_ms"], 120.0)
        self.assertEqual(got["wav_bytes"], 1964)


class TestModelledCloud(unittest.TestCase):
    def test_one_word_response_by_hand(self):
        # 80 + 300 + 700 + (100 + 5 * 1) = 1185 ms, modelled.
        got = modelled_cloud("Goodbye.")
        self.assertEqual(got["response_words"], 1)
        self.assertEqual(got["tts_first_audio_ms"], 105.0)
        self.assertEqual(got["total_ms"], 1185.0)
        self.assertEqual(got["label"], "modelled, not measured")

    def test_five_word_response_by_hand(self):
        # "Timer set for 300 seconds." is 5 words: TTS 125,
        # total 1205.
        got = modelled_cloud("Timer set for 300 seconds.")
        self.assertEqual(got["response_words"], 5)
        self.assertEqual(got["tts_first_audio_ms"], 125.0)
        self.assertEqual(got["total_ms"], 1205.0)

    def test_constants_sum_to_base(self):
        got = modelled_cloud("")
        self.assertEqual(got["response_words"], 0)
        self.assertEqual(got["total_ms"], 1180.0)


class TestBudget(unittest.TestCase):
    def test_assess_by_hand(self):
        # Medians 100 + 200 + 300 + 400 = 1000, within the
        # 100 ms budget and the 500 ms ceiling.
        got = assess_turn_budget({"frame_vad": 100.0,
                                  "streaming": 200.0,
                                  "intent_answer": 300.0,
                                  "wav_synthesis": 400.0})
        self.assertEqual(got["total_median_us"], 1000.0)
        self.assertTrue(got["within_budget"])
        self.assertTrue(got["within_ceiling"])
        self.assertTrue(
            got["stage_shares"]["wav_synthesis"]["within_stage_budget"])

    def test_assess_over_budget(self):
        got = assess_turn_budget({"frame_vad": 60000.0,
                                  "streaming": 200.0,
                                  "intent_answer": 300.0,
                                  "wav_synthesis": 50000.0})
        self.assertEqual(got["total_median_us"], 110500.0)
        self.assertFalse(got["within_budget"])
        self.assertTrue(got["within_ceiling"])
        self.assertFalse(
            got["stage_shares"]["frame_vad"]["within_stage_budget"])


class TestSizesAndBarge(unittest.TestCase):
    def test_response_size_scaling_by_hand(self):
        # n words: 960n + 320(n - 1) samples. 1 word 960, 2 words
        # 2240, 3 words 3520 samples.
        self.assertEqual(response_size("Goodbye.")["sample_count"], 960)
        self.assertEqual(response_size("Hello there.")["sample_count"],
                         2240)
        self.assertEqual(
            response_size("One two three.")["sample_count"], 3520)
        self.assertEqual(response_size("Hello there.")["duration_ms"],
                         280.0)

    def test_barge_drop_counts(self):
        # Weather response is 70 frames. Play 10, drop path with
        # stop: 60 dropped, cancelled, session back to IDLE.
        session = setup_barge("What is the weather in Toronto", 10)
        hit = barge_drop(session)
        self.assertEqual(hit["dropped"], 60)
        self.assertEqual(hit["played_before"], 10)
        self.assertTrue(hit["cancelled"])
        self.assertEqual(session.state, "IDLE")


if __name__ == "__main__":
    unittest.main()
