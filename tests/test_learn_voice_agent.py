"""Unit tests for the Learn voice agent. Hand-computed expectations.

Run: python -m unittest tests.test_learn_voice_agent -v
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from voice_agent import (  # noqa: E402
    MS_PER_WORD,
    VoiceSession,
    assess_budget,
    extract_city,
    extract_timer_seconds,
    frame_text,
    normalize,
    run_turn,
    stage_answer,
    stage_intent,
    stage_tts,
)


class TestNormalizeAndFraming(unittest.TestCase):
    def test_normalize_strips_punctuation_and_case(self):
        self.assertEqual(normalize("What time is it?"), "what time is it")
        self.assertEqual(normalize("Hello,  THERE!"), "hello there")

    def test_frame_text_groups_of_three(self):
        # 7 words in groups of 3 give frames of 3, 3, and 1 words.
        self.assertEqual(frame_text("a b c d e f g"), ["a b c", "d e f", "g"])

    def test_frame_text_empty(self):
        self.assertEqual(frame_text(""), [])

    def test_ms_per_word_from_rate(self):
        # 150 words per minute is 60000 / 150 = 400 ms per word.
        self.assertEqual(MS_PER_WORD, 400)


class TestIntentAndSlots(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(stage_intent("hello there")["intent"], "greeting")

    def test_time(self):
        self.assertEqual(stage_intent("what time is it")["intent"], "time")

    def test_date(self):
        self.assertEqual(stage_intent("what is the date today")["intent"],
                         "date")

    def test_weather_city_slot(self):
        found = stage_intent("how is the weather in dhaka")
        self.assertEqual(found["intent"], "weather")
        self.assertEqual(found["slots"], {"city": "dhaka"})

    def test_weather_default_city(self):
        # No city named, so the default city Toronto is used.
        self.assertEqual(extract_city("what is the weather"), "toronto")

    def test_timer_minutes_hand_check(self):
        # 5 minutes is 5 times 60 = 300 seconds.
        self.assertEqual(extract_timer_seconds("set a timer for 5 minutes"),
                         300)

    def test_timer_seconds(self):
        self.assertEqual(extract_timer_seconds("set a timer for 30 seconds"),
                         30)

    def test_timer_no_number(self):
        self.assertIsNone(extract_timer_seconds("set a timer please"))

    def test_name_help_goodbye_unknown(self):
        self.assertEqual(stage_intent("what is your name")["intent"], "name")
        self.assertEqual(stage_intent("what can you do")["intent"], "help")
        self.assertEqual(stage_intent("goodbye for now")["intent"], "goodbye")
        self.assertEqual(stage_intent("tell me about quantum tunneling")
                         ["intent"], "unknown")

    def test_stop(self):
        self.assertEqual(stage_intent("stop")["intent"], "stop")

    def test_weather_beats_time_priority(self):
        # Weather is checked before time in the fixed priority order.
        self.assertEqual(stage_intent("weather and time")["intent"],
                         "weather")


class TestAnswers(unittest.TestCase):
    def test_time_answer_uses_teaching_clock(self):
        self.assertEqual(stage_answer("time", {}), "The time is 10:30.")

    def test_date_answer(self):
        self.assertEqual(stage_answer("date", {}), "The date is 2026-11-05.")

    def test_weather_answers(self):
        self.assertEqual(stage_answer("weather", {"city": "toronto"}),
                         "The weather in Toronto is clear, "
                         "12 degrees Celsius.")
        self.assertEqual(stage_answer("weather", {"city": "dhaka"}),
                         "The weather in Dhaka is humid, "
                         "29 degrees Celsius.")

    def test_timer_answer(self):
        self.assertEqual(stage_answer("timer", {"seconds": 300}),
                         "Timer set for 300 seconds.")
        self.assertEqual(stage_answer("timer", {"seconds": None}),
                         "I need a number for the timer.")

    def test_unknown_answer(self):
        self.assertEqual(stage_answer("unknown", {}),
                         "I do not know that yet. Ask for the time, "
                         "the date, the weather, or a timer.")


class TestTtsPlan(unittest.TestCase):
    def test_weather_response_plan_by_hand(self):
        # Response has 9 words: The weather in Toronto is clear, 12
        # degrees Celsius. Groups of 3 give 3 frames. Estimated
        # speech time is 9 times 400 = 3600 ms by the stated formula.
        plan = stage_tts("The weather in Toronto is clear, "
                         "12 degrees Celsius.")
        self.assertEqual(plan["frames"], ["The weather in",
                                          "Toronto is clear,",
                                          "12 degrees Celsius."])
        self.assertEqual(plan["frame_count"], 3)
        self.assertEqual(plan["word_count"], 9)
        self.assertEqual(plan["est_speech_ms"], 3600)

    def test_time_response_plan_by_hand(self):
        # "The time is 10:30." has 4 words, so 2 frames and
        # 4 times 400 = 1600 ms estimated.
        plan = stage_tts("The time is 10:30.")
        self.assertEqual(plan["frames"], ["The time is", "10:30."])
        self.assertEqual(plan["est_speech_ms"], 1600)


class TestBudget(unittest.TestCase):
    def test_budget_sum_by_hand(self):
        # 10 + 20 + 30 + 40 = 100, within 5000 and outside 50.
        stages = {"a": 10.0, "b": 20.0, "c": 30.0, "d": 40.0}
        self.assertEqual(assess_budget(stages, 5000.0),
                         {"total_us": 100.0, "budget_us": 5000.0,
                          "within_budget": True})
        self.assertFalse(assess_budget(stages, 50.0)["within_budget"])


class TestRunTurn(unittest.TestCase):
    def test_full_turn_weather(self):
        turn = run_turn("What is the weather in Toronto")
        self.assertEqual(turn["intent"], "weather")
        self.assertEqual(turn["response"],
                         "The weather in Toronto is clear, "
                         "12 degrees Celsius.")
        self.assertEqual(turn["tts"]["frame_count"], 3)

    def test_full_turn_timer(self):
        turn = run_turn("Set a timer for 5 minutes")
        self.assertEqual(turn["slots"], {"seconds": 300})
        self.assertEqual(turn["response"], "Timer set for 300 seconds.")


class TestBargeIn(unittest.TestCase):
    def test_interrupt_drops_unplayed_frames(self):
        # Weather response has 3 frames. Play 2, interrupt: 1 dropped.
        s = VoiceSession()
        s.hear("What is the weather in Toronto")
        self.assertEqual(s.state, "SPEAKING")
        self.assertEqual(s.play_one_frame(), "The weather in")
        self.assertEqual(s.play_one_frame(), "Toronto is clear,")
        hit = s.interrupt("What time is it")
        self.assertEqual(hit["dropped"], 1)
        self.assertEqual(hit["played_before"], 2)
        self.assertFalse(hit["cancelled"])
        self.assertEqual(hit["turn"]["response"], "The time is 10:30.")
        self.assertEqual(s.interruptions, 1)
        self.assertEqual(s.frames_dropped_total, 1)
        self.assertEqual(s.state, "SPEAKING")

    def test_stop_interrupt_cancels(self):
        # Help response has 13 words, so 5 frames. Play 1, stop:
        # 4 dropped, cancelled, session back to IDLE.
        s = VoiceSession()
        s.hear("What can you do")
        self.assertEqual(len(s.frames), 5)
        s.play_one_frame()
        hit = s.interrupt("Stop")
        self.assertEqual(hit["dropped"], 4)
        self.assertTrue(hit["cancelled"])
        self.assertIsNone(hit["turn"])
        self.assertEqual(s.state, "IDLE")

    def test_play_to_end_returns_to_idle(self):
        s = VoiceSession()
        s.hear("Goodbye for now")
        self.assertEqual(s.play_one_frame(), "Goodbye.")
        self.assertEqual(s.state, "IDLE")
        self.assertIsNone(s.play_one_frame())

    def test_interrupt_when_not_speaking_is_none(self):
        s = VoiceSession()
        self.assertIsNone(s.interrupt("What time is it"))

    def test_hear_while_speaking_raises(self):
        s = VoiceSession()
        s.hear("What time is it")
        with self.assertRaises(RuntimeError):
            s.hear("What is the date today")


if __name__ == "__main__":
    unittest.main()
