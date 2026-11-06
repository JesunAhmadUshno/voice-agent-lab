"""Unit tests for the Build voice pipeline. Hand-computed values.

Run: python -m unittest tests.test_build_voice_agent -v
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "level-2-build"))
from voice_pipeline import (AudioSession, DialogueSession,  # noqa: E402
                            frame_is_speech, frame_rms, run_core_turn,
                            simulate_asr, streaming_trace,
                            synthesize_samples, synthesize_wav,
                            word_error_rate, word_frequency)


class TestToneSynth(unittest.TestCase):
    def test_one_word_samples_and_frames(self):
        # "Goodbye." is 1 word: 960 samples, 6 frames of 160,
        # 960 / 8000 * 1000 = 120 ms, WAV is 44 header + 1920 data.
        audio = synthesize_wav("Goodbye.")
        self.assertEqual(audio["sample_count"], 960)
        self.assertEqual(audio["frame_count"], 6)
        self.assertEqual(audio["duration_ms"], 120.0)
        self.assertEqual(audio["wav_bytes"], 1964)
        self.assertEqual(audio["speech_frames"], 6)
        self.assertEqual(audio["silence_frames"], 0)

    def test_weather_response_layout_by_hand(self):
        # 9 words: 9 * 960 + 8 * 320 = 11200 samples, 70 frames,
        # 1400 ms, speech 9 * 6 = 54 frames, silence 8 * 2 = 16.
        audio = synthesize_wav(
            "The weather in Toronto is clear, 12 degrees Celsius.")
        self.assertEqual(audio["sample_count"], 11200)
        self.assertEqual(audio["frame_count"], 70)
        self.assertEqual(audio["duration_ms"], 1400.0)
        self.assertEqual(audio["speech_frames"], 54)
        self.assertEqual(audio["silence_frames"], 16)
        self.assertEqual(audio["wav_bytes"], 44 + 11200 * 2)

    def test_empty_text_has_no_audio(self):
        audio = synthesize_wav("")
        self.assertEqual(audio["sample_count"], 0)
        self.assertEqual(audio["frame_count"], 0)

    def test_synthesis_is_deterministic(self):
        self.assertEqual(synthesize_samples("The time is 10:30."),
                         synthesize_samples("The time is 10:30."))

    def test_frequency_band(self):
        for word in ("the", "weather", "10:30.", "zzz"):
            self.assertTrue(300 <= word_frequency(word) <= 699)

    def test_vad_speech_and_silence(self):
        samples = synthesize_samples("Goodbye. Bye.")
        # First frame is tone (speech), the gap frame is silence.
        self.assertTrue(frame_is_speech(samples[0:160]))
        self.assertEqual(frame_rms([0] * 160), 0.0)
        self.assertFalse(frame_is_speech([0] * 160))


class TestStreaming(unittest.TestCase):
    def test_weather_first_correct_partial(self):
        # Partials: what, what is, what is the are unknown; the
        # fourth partial adds weather, so first correct is 4 of 6.
        trace = streaming_trace("What is the weather in Toronto",
                                "weather")
        self.assertEqual(trace["partials"], 6)
        self.assertEqual(trace["first_correct_partial"], 4)
        self.assertTrue(trace["stable_from_first"])
        self.assertEqual(trace["final_intent"], "weather")

    def test_unknown_first_correct_is_first_partial(self):
        trace = streaming_trace("Tell me about quantum tunneling",
                                "unknown")
        self.assertEqual(trace["first_correct_partial"], 1)

    def test_time_first_correct(self):
        # "what time" already classifies as time: first correct 2.
        trace = streaming_trace("What time is it", "time")
        self.assertEqual(trace["first_correct_partial"], 2)


class TestNoiseAndWer(unittest.TestCase):
    def test_simulate_asr_weather_case(self):
        self.assertEqual(simulate_asr("What is the weather in Toronto"),
                         "what is whether in toronto")

    def test_simulate_asr_drops_the_only(self):
        self.assertEqual(simulate_asr("What is the date today"),
                         "what is date today")

    def test_wer_weather_case_by_hand(self):
        # Reference 6 words, hypothesis 5: one deletion (the) plus
        # one substitution (weather to whether) is distance 2,
        # so WER is 2 / 6 = 0.3333.
        self.assertEqual(word_error_rate(
            "what is the weather in toronto",
            "what is whether in toronto"), 0.3333)

    def test_wer_identical_is_zero(self):
        self.assertEqual(word_error_rate("what time is it",
                                         "what time is it"), 0.0)

    def test_noise_breaks_weather_intent(self):
        from voice_agent import run_turn
        heard = simulate_asr("What is the weather in Toronto")
        self.assertEqual(run_turn(heard)["intent"], "unknown")


class TestCoreTurn(unittest.TestCase):
    def test_weather_turn_audio_and_streaming(self):
        got = run_core_turn("What is the weather in Toronto")
        self.assertEqual(got["intent"], "weather")
        self.assertEqual(got["audio"]["frame_count"], 70)
        self.assertEqual(got["streaming"]["first_correct_partial"], 4)


class TestDialogue(unittest.TestCase):
    def test_weather_followup_city_only(self):
        s = DialogueSession()
        first = s.hear("What is the weather in Toronto")
        self.assertEqual(first["intent"], "weather")
        second = s.hear("And in Dhaka")
        self.assertEqual(second["intent"], "weather")
        self.assertEqual(second["response"],
                         "The weather in Dhaka is humid, "
                         "29 degrees Celsius.")
        self.assertEqual(s.last_city, "dhaka")

    def test_followup_without_weather_context_falls_through(self):
        s = DialogueSession()
        got = s.hear("And in Dhaka")
        self.assertEqual(got["intent"], "unknown")

    def test_timer_slot_filling(self):
        s = DialogueSession()
        first = s.hear("Set a timer")
        self.assertEqual(first["intent"], "timer_pending")
        self.assertEqual(first["response"],
                         "For how long should I set the timer?")
        second = s.hear("5 minutes")
        self.assertEqual(second["intent"], "timer")
        self.assertEqual(second["response"],
                         "Timer set for 300 seconds.")

    def test_repeat_replays_last_response(self):
        s = DialogueSession()
        s.hear("What time is it")
        got = s.hear("Say that again")
        self.assertEqual(got["intent"], "repeat")
        self.assertEqual(got["response"], "The time is 10:30.")

    def test_repeat_with_no_history(self):
        s = DialogueSession()
        got = s.hear("Repeat")
        self.assertEqual(got["response"],
                         "There is nothing to repeat yet.")


class TestAudioBargeIn(unittest.TestCase):
    def test_interrupt_over_audio_frames(self):
        # Weather response is 70 frames. Play 10, interrupt:
        # 60 dropped, new turn is the time response.
        s = AudioSession()
        s.hear("What is the weather in Toronto")
        self.assertEqual(len(s.frames), 70)
        s.play_frames(10)
        hit = s.interrupt("What time is it")
        self.assertEqual(hit["dropped"], 60)
        self.assertEqual(hit["played_before"], 10)
        self.assertFalse(hit["cancelled"])
        self.assertEqual(hit["turn"]["response"], "The time is 10:30.")
        self.assertEqual(s.state, "SPEAKING")
        self.assertEqual(s.frames_dropped_total, 60)

    def test_stop_cancels_playback(self):
        # Help response has 13 words: 102 frames. Play 1, stop:
        # 101 dropped, cancelled, back to IDLE.
        s = AudioSession()
        s.hear("What can you do")
        self.assertEqual(len(s.frames), 102)
        s.play_frames(1)
        hit = s.interrupt("Stop")
        self.assertEqual(hit["dropped"], 101)
        self.assertTrue(hit["cancelled"])
        self.assertEqual(s.state, "IDLE")

    def test_play_to_end_returns_to_idle(self):
        s = AudioSession()
        s.hear("Goodbye for now")
        self.assertEqual(len(s.frames), 6)
        s.play_frames(6)
        self.assertEqual(s.state, "IDLE")
        self.assertIsNone(s.interrupt("What time is it"))


if __name__ == "__main__":
    unittest.main()
