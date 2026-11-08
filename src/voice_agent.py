"""Learn-level voice agent loop, simulated on CPU, stdlib only.

The loop is: speech in, answer, speech out. At this level there is
no real audio, no ASR model, and no TTS model:

- Speech in is simulated: the input is a text transcript that stands
  in for ASR output. It is split into simulated frames (groups of
  words) to show the streaming shape, labelled simulated everywhere.
- The answer step is a small deterministic intent and slot rule set
  over a fixed teaching knowledge base. It is not an LLM.
- Speech out is simulated: the response text is split into simulated
  frames (groups of 3 words) that a TTS engine would speak in order.
  An estimated speaking time is computed from a stated rate
  (150 words per minute, so 400 ms per word). That number is a
  formula estimate, not a measurement.

Latency is handled separately by the runner: it measures the actual
wall-clock time of each code stage below. Nothing in this file
invents a timing.

Barge-in is a small state machine in VoiceSession: while the agent
is SPEAKING, a new utterance interrupts playback, the unplayed
frames are dropped and counted, and the new utterance is processed.
"""

WORDS_PER_FRAME = 3
WORDS_PER_MINUTE = 150
MS_PER_WORD = 60000 // WORDS_PER_MINUTE  # 400 ms per word at 150 wpm

# Fixed teaching knowledge base. These are labelled teaching records,
# not live data: the clock, the date, and the weather never change.
KB = {
    "time": "10:30",
    "date": "2026-11-05",
    "weather": {
        "toronto": "clear, 12 degrees Celsius",
        "dhaka": "humid, 29 degrees Celsius",
    },
    "default_city": "toronto",
    "name": "Voice Lab",
}

HELP_TEXT = "You can ask for the time, the date, the weather, or a timer."
UNKNOWN_TEXT = ("I do not know that yet. Ask for the time, the date, "
                "the weather, or a timer.")

_PUNCT = ".,!?;:"


def normalize(text):
    """Lowercase, strip punctuation at word edges, collapse spaces."""
    words = []
    for raw in text.lower().split():
        words.append(raw.strip(_PUNCT))
    return " ".join(w for w in words if w)


def frame_text(text, words_per_frame=WORDS_PER_FRAME):
    """Split text into simulated frames of words_per_frame words.

    A frame here is a group of words, standing in for a chunk of
    streamed audio. It is simulated framing, not real audio framing.
    """
    words = text.split()
    frames = []
    for i in range(0, len(words), words_per_frame):
        frames.append(" ".join(words[i:i + words_per_frame]))
    return frames


def stage_frame(transcript):
    """Stage 1, speech in (simulated): normalize and frame a transcript."""
    normalized = normalize(transcript)
    return {"normalized": normalized, "frames_in": frame_text(normalized)}


def extract_timer_seconds(normalized):
    """Return the timer length in seconds, or None if not parseable.

    Rule: the first integer in the text is the amount. Minutes
    multiply by 60, seconds by 1. No unit word means seconds.
    Hand check: 5 minutes is 5 times 60 = 300 seconds.
    """
    amount = None
    for word in normalized.split():
        if word.isdigit():
            amount = int(word)
            break
    if amount is None:
        return None
    if "minute" in normalized:
        return amount * 60
    return amount


def extract_city(normalized):
    """Return the KB city named in the text, or the default city."""
    for city in KB["weather"]:
        if city in normalized.split():
            return city
    return KB["default_city"]


def stage_intent(normalized):
    """Stage 2: classify intent and extract slots. Fixed priority order.

    Order: stop, greeting, timer, weather, time, date, name, help,
    goodbye, unknown. The order matters: a weather question is
    checked before a time question, and timer before both.
    """
    words = normalized.split()
    if normalized == "stop" or normalized == "cancel":
        return {"intent": "stop", "slots": {}}
    if words and words[0] in ("hello", "hi", "hey"):
        return {"intent": "greeting", "slots": {}}
    if "timer" in words:
        return {"intent": "timer",
                "slots": {"seconds": extract_timer_seconds(normalized)}}
    if "weather" in words:
        return {"intent": "weather",
                "slots": {"city": extract_city(normalized)}}
    if "time" in words:
        return {"intent": "time", "slots": {}}
    if "date" in words:
        return {"intent": "date", "slots": {}}
    if "your" in words and "name" in words:
        return {"intent": "name", "slots": {}}
    if "help" in words or normalized == "what can you do":
        return {"intent": "help", "slots": {}}
    if "goodbye" in words or "bye" in words:
        return {"intent": "goodbye", "slots": {}}
    return {"intent": "unknown", "slots": {}}


def stage_answer(intent, slots):
    """Stage 3: build the response text from the teaching KB."""
    if intent == "greeting":
        return "Hello. How can I help?"
    if intent == "time":
        return "The time is " + KB["time"] + "."
    if intent == "date":
        return "The date is " + KB["date"] + "."
    if intent == "weather":
        city = slots["city"]
        return ("The weather in " + city.capitalize() + " is "
                + KB["weather"][city] + ".")
    if intent == "timer":
        if slots.get("seconds") is None:
            return "I need a number for the timer."
        return "Timer set for " + str(slots["seconds"]) + " seconds."
    if intent == "name":
        return "My name is " + KB["name"] + ", a teaching voice agent."
    if intent == "help":
        return HELP_TEXT
    if intent == "goodbye":
        return "Goodbye."
    if intent == "stop":
        return "Stopped."
    return UNKNOWN_TEXT


def stage_tts(response_text):
    """Stage 4, speech out (simulated): frame the response for playback.

    est_speech_ms is a formula estimate at 150 words per minute
    (400 ms per word). It is not a measured time.
    """
    frames = frame_text(response_text)
    words = len(response_text.split())
    return {"frames": frames, "frame_count": len(frames),
            "word_count": words, "est_speech_ms": words * MS_PER_WORD}


def run_turn(transcript):
    """Run one full turn: frame, intent, answer, tts plan."""
    framed = stage_frame(transcript)
    found = stage_intent(framed["normalized"])
    response = stage_answer(found["intent"], found["slots"])
    tts = stage_tts(response)
    return {"transcript": transcript, "normalized": framed["normalized"],
            "frames_in": framed["frames_in"], "intent": found["intent"],
            "slots": found["slots"], "response": response, "tts": tts}


def assess_budget(stage_us, budget_us):
    """Pure budget check: sum measured stage means, compare to budget.

    stage_us maps stage name to measured microseconds per call.
    Returns the total and whether the total is within budget.
    Hand check: stages of 10, 20, 30, 40 sum to 100, which is within
    a budget of 5000 and outside a budget of 50.
    """
    total = round(sum(stage_us.values()), 3)
    return {"total_us": total, "budget_us": budget_us,
            "within_budget": total <= budget_us}


class VoiceSession:
    """One conversation with a barge-in state machine.

    States: IDLE, LISTENING, THINKING, SPEAKING.
    A normal turn moves IDLE to LISTENING (transcript arrives), to
    THINKING (intent and answer run), to SPEAKING (frames play).
    When the last frame plays, the session returns to IDLE.
    interrupt() is only valid in SPEAKING: it drops the unplayed
    frames, counts them, and processes the new utterance at once.
    A stop utterance during SPEAKING cancels playback and the
    session goes to IDLE with no new spoken response frames.
    """

    def __init__(self):
        self.state = "IDLE"
        self.frames = []
        self.frames_played = 0
        self.interruptions = 0
        self.frames_dropped_total = 0
        self.last_turn = None

    def hear(self, transcript):
        """Process a transcript while not speaking. Returns the turn."""
        if self.state == "SPEAKING":
            raise RuntimeError("use interrupt() while SPEAKING")
        self.state = "LISTENING"
        turn = run_turn(transcript)
        self.state = "THINKING"
        self.last_turn = turn
        self.frames = turn["tts"]["frames"]
        self.frames_played = 0
        self.state = "SPEAKING" if self.frames else "IDLE"
        return turn

    def play_one_frame(self):
        """Play the next response frame. Returns it, or None if done."""
        if self.state != "SPEAKING":
            return None
        frame = self.frames[self.frames_played]
        self.frames_played += 1
        if self.frames_played >= len(self.frames):
            self.state = "IDLE"
        return frame

    def interrupt(self, transcript):
        """Barge in while SPEAKING with a new utterance.

        Returns a dict with the frames dropped by this interruption
        and the new turn, or None for a stop interruption (playback
        cancelled, no new response is spoken).
        """
        if self.state != "SPEAKING":
            return None
        dropped = len(self.frames) - self.frames_played
        self.frames_dropped_total += dropped
        self.interruptions += 1
        played = self.frames_played
        self.frames = []
        self.frames_played = 0
        self.state = "IDLE"
        if normalize(transcript) in ("stop", "cancel"):
            return {"dropped": dropped, "played_before": played,
                    "turn": None, "cancelled": True}
        turn = self.hear(transcript)
        return {"dropped": dropped, "played_before": played,
                "turn": turn, "cancelled": False}
