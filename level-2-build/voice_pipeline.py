"""Build-level end-to-end voice pipeline, stdlib only.

Learn (level-1-learn/voice_agent.py, reused here by import) was a
single-turn simulated loop: text in, text out, word-group frames.
Build keeps that turn as its answer core and adds the system
around it:

- Real WAV audio out: a deterministic tone synthesis turns each
  response into a real WAV byte stream (8000 Hz, 16-bit mono).
  Each word is a 120 ms sine segment at a word-derived frequency,
  separated by 40 ms of silence. This is real audio data with real
  duration and energy, but it is NOT intelligible speech and no
  TTS voice is claimed: no TTS engine exists on this machine (see
  BUILD-SPEC.md for the checked substitutions).
- Voice activity split: 20 ms frames of the WAV are classified
  speech or silence by a root-mean-square energy rule.
- Streaming intent: a transcript is replayed as cumulative word
  partials and the Learn intent classifier runs on every partial,
  so the pipeline can report when the intent first stabilised.
- Dialogue: DialogueSession adds conversation state on top of the
  Learn turn: weather follow-ups naming only a city, timer slot
  filling across turns, and repeat of the last response.
- Simulated ASR noise: one deterministic error map (weather to
  whether, the dropped) stands in for ASR output errors. Word
  error rate is a word-level Levenshtein distance.
- Playback with barge-in over real audio frames: an AudioSession
  plays the WAV frames of a response and an interruption drops
  the unplayed frames, counted exactly.

No number in this module is a timing. Durations are sample counts
divided by the sample rate, which is arithmetic, not measurement.
"""
import io
import math
import os
import struct
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "level-1-learn"))
from voice_agent import (extract_timer_seconds, normalize,  # noqa: E402
                         run_turn, stage_intent)

SAMPLE_RATE = 8000
FRAME_SAMPLES = 160          # 20 ms at 8000 Hz
WORD_SAMPLES = 960           # 120 ms of tone per word (6 frames)
GAP_SAMPLES = 320            # 40 ms of silence between words (2 frames)
AMPLITUDE = 8000
VAD_RMS_THRESHOLD = 100.0    # sine frames sit near 5657, silence at 0

CLARIFY_TIMER = "For how long should I set the timer?"
NO_REPEAT = "There is nothing to repeat yet."


def word_frequency(word):
    """Deterministic tone frequency for one word, 300 to 699 Hz."""
    return 300 + (sum(word.encode("utf-8")) % 400)


def synthesize_samples(text):
    """Return the int samples of the tone synthesis for a text.

    Layout: for each word, WORD_SAMPLES of sine at the word
    frequency, then GAP_SAMPLES of silence, with no trailing gap
    after the last word. Hand check: a 1-word text has 960 samples
    (6 frames); a 9-word text has 9 * 960 + 8 * 320 = 11200 samples
    (70 frames, 1400 ms at 8000 Hz).
    """
    words = text.split()
    samples = []
    for wi, word in enumerate(words):
        freq = word_frequency(word)
        for i in range(WORD_SAMPLES):
            samples.append(int(AMPLITUDE * math.sin(
                2.0 * math.pi * freq * i / SAMPLE_RATE)))
        if wi < len(words) - 1:
            samples.extend([0] * GAP_SAMPLES)
    return samples


def samples_to_wav_bytes(samples):
    """Pack int samples into a WAV byte string (16-bit mono)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(b"".join(struct.pack("<h", s) for s in samples))
    return buf.getvalue()


def synthesize_wav(text):
    """Full audio record for a response text. All fields exact."""
    samples = synthesize_samples(text)
    data = samples_to_wav_bytes(samples)
    frames = audio_frames(samples)
    speech = sum(1 for f in frames if frame_is_speech(f))
    return {"samples": samples, "wav_bytes": len(data),
            "sample_count": len(samples),
            "duration_ms": round(len(samples) * 1000 / SAMPLE_RATE, 3),
            "frame_count": len(frames), "speech_frames": speech,
            "silence_frames": len(frames) - speech}


def audio_frames(samples):
    """Split samples into 20 ms frames (the last may be short)."""
    return [samples[i:i + FRAME_SAMPLES]
            for i in range(0, len(samples), FRAME_SAMPLES)]


def frame_rms(frame):
    """Root-mean-square energy of one frame. Silence is exactly 0."""
    if not frame:
        return 0.0
    return math.sqrt(sum(s * s for s in frame) / len(frame))


def frame_is_speech(frame):
    return frame_rms(frame) > VAD_RMS_THRESHOLD


def partials_of(transcript):
    """Cumulative word partials of the normalized transcript."""
    words = normalize(transcript).split()
    return [" ".join(words[:i + 1]) for i in range(len(words))]


def streaming_trace(transcript, expected_intent):
    """Intent per partial, and where the expected intent first hits.

    first_correct_partial is 1-based, or None if no partial reaches
    the expected intent. stable_from_first means every partial from
    the first correct one to the end keeps the expected intent.
    """
    partials = partials_of(transcript)
    intents = [stage_intent(p)["intent"] for p in partials]
    first = None
    for i, found in enumerate(intents):
        if found == expected_intent:
            first = i + 1
            break
    stable = (first is not None
              and all(x == expected_intent for x in intents[first - 1:]))
    return {"partials": len(partials), "partial_intents": intents,
            "first_correct_partial": first, "stable_from_first": stable,
            "final_intent": intents[-1] if intents else "unknown"}


NOISE_SUBSTITUTIONS = {"weather": "whether"}
NOISE_DROPS = {"the"}


def simulate_asr(transcript):
    """Deterministic simulated ASR output for a transcript.

    On the normalized words: weather becomes whether, and the word
    the is dropped. Nothing else changes, so the word error rate of
    this step is computable by hand for any input.
    """
    out = []
    for word in normalize(transcript).split():
        if word in NOISE_DROPS:
            continue
        out.append(NOISE_SUBSTITUTIONS.get(word, word))
    return " ".join(out)


def word_error_rate(reference, hypothesis):
    """Word-level Levenshtein distance divided by reference words."""
    ref = reference.split()
    hyp = hypothesis.split()
    if not ref:
        return 0.0 if not hyp else 1.0
    prev = list(range(len(hyp) + 1))
    for i, rword in enumerate(ref, start=1):
        cur = [i] + [0] * len(hyp)
        for j, hword in enumerate(hyp, start=1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1,
                         prev[j - 1] + (0 if rword == hword else 1))
        prev = cur
    return round(prev[len(hyp)] / len(ref), 4)


def run_core_turn(transcript):
    """One single turn: Learn turn plus audio and streaming records."""
    turn = run_turn(transcript)
    audio = synthesize_wav(turn["response"])
    trace = streaming_trace(transcript, turn["intent"])
    return {"transcript": transcript, "normalized": turn["normalized"],
            "intent": turn["intent"], "slots": turn["slots"],
            "response": turn["response"],
            "audio": {k: audio[k] for k in
                      ("wav_bytes", "sample_count", "duration_ms",
                       "frame_count", "speech_frames", "silence_frames")},
            "streaming": trace}


class DialogueSession:
    """Multi-turn conversation state over the Learn turn.

    Adds three behaviours the single-turn Learn loop cannot do:
    weather follow-ups that name only a city (And in Dhaka) reuse
    the weather intent with the new city; a timer request with no
    amount asks the clarifying question and fills the slot from
    the next turn; a repeat request (Say that again, Repeat)
    replays the last response.
    """

    def __init__(self):
        self.last_intent = None
        self.last_city = None
        self.last_response = None
        self.pending_slot = None
        self.turns = 0

    def _followup_city(self, normalized):
        words = normalized.split()
        if not words or words[0] not in ("and", "what"):
            return None
        for city in ("toronto", "dhaka"):
            if city in words:
                return city
        return None

    def hear(self, transcript):
        """Process one dialogue turn. Returns intent and response."""
        normalized = normalize(transcript)
        self.turns += 1
        if self.pending_slot == "timer_seconds":
            seconds = extract_timer_seconds(
                "timer " + normalized if normalized else "timer")
            self.pending_slot = None
            if seconds is not None:
                return self._finish("timer",
                                    "Timer set for " + str(seconds)
                                    + " seconds.")
            return self._finish("timer_pending", CLARIFY_TIMER,
                                pending="timer_seconds")
        if normalized in ("repeat", "say that again"):
            if self.last_response is None:
                return self._finish("repeat", NO_REPEAT)
            return self._finish("repeat", self.last_response,
                                keep_last=True)
        city = self._followup_city(normalized)
        if city is not None and self.last_intent == "weather":
            turn = run_turn("What is the weather in " + city)
            return self._finish(turn["intent"], turn["response"],
                                city=city)
        turn = run_turn(transcript)
        if turn["intent"] == "timer" and turn["slots"].get(
                "seconds") is None:
            return self._finish("timer_pending", CLARIFY_TIMER,
                                pending="timer_seconds")
        city_slot = turn["slots"].get("city") \
            if turn["intent"] == "weather" else None
        return self._finish(turn["intent"], turn["response"],
                            city=city_slot)

    def _finish(self, intent, response, city=None, pending=None,
                keep_last=False):
        self.last_intent = intent
        if city is not None:
            self.last_city = city
        if not keep_last:
            self.last_response = response
        self.pending_slot = pending
        return {"intent": intent, "response": response}


class AudioSession:
    """Playback of one response WAV, with barge-in over its frames.

    hear() synthesizes the response audio through a DialogueSession
    and loads its frames for playback. interrupt() drops the
    unplayed frames, counts them, and processes the interruption
    through the same dialogue session, so context survives a
    barge-in.
    """

    def __init__(self):
        self.dialogue = DialogueSession()
        self.frames = []
        self.frames_played = 0
        self.interruptions = 0
        self.frames_dropped_total = 0
        self.state = "IDLE"
        self.last_audio = None

    def hear(self, transcript):
        if self.state == "SPEAKING":
            raise RuntimeError("use interrupt() while SPEAKING")
        result = self.dialogue.hear(transcript)
        audio = synthesize_wav(result["response"])
        self.last_audio = audio
        self.frames = audio_frames(audio["samples"])
        self.frames_played = 0
        self.state = "SPEAKING" if self.frames else "IDLE"
        return result

    def play_frames(self, count):
        """Play up to count frames. Returns how many played."""
        played = 0
        while played < count and self.state == "SPEAKING":
            self.frames_played += 1
            played += 1
            if self.frames_played >= len(self.frames):
                self.state = "IDLE"
        return played

    def interrupt(self, transcript):
        """Barge in: drop unplayed frames, process the new turn."""
        if self.state != "SPEAKING":
            return None
        dropped = len(self.frames) - self.frames_played
        played = self.frames_played
        self.frames_dropped_total += dropped
        self.interruptions += 1
        self.frames = []
        self.frames_played = 0
        self.state = "IDLE"
        if normalize(transcript) in ("stop", "cancel"):
            return {"dropped": dropped, "played_before": played,
                    "cancelled": True, "turn": None}
        result = self.hear(transcript)
        return {"dropped": dropped, "played_before": played,
                "cancelled": False, "turn": result}
