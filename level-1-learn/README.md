# Level 1, Learn: voice-agent-lab

Status: DONE (2026-11-05). A real-time voice agent loop built
small on CPU: speech in, answer, speech out, with barge-in
handling and a measured per-stage latency budget. Built with the
Python standard library only.

## Honest scope line

There is no real audio in this level, no ASR model, no TTS model,
no LLM, no GPU, and no external API. Speech in is simulated: a
text transcript stands in for ASR output. Speech out is
simulated: a text response stands in for TTS output, split into
simulated frames (groups of 3 words). The answer step is a
deterministic keyword intent rule over a fixed teaching knowledge
base (a fixed clock of 10:30, a fixed date of 2026-11-05, and
weather records for two cities). Those are teaching records, not
live data. Real speech models and a local against cloud latency
study are Build and Deep scope. This level was run on the Muse
VM (CPU), not on BlackBox, the assigned GPU fleet node:
NEEDS-BLACKBOX-ON for any GPU work, Learn is CPU teaching work by
design, and the grade below carries a named deduction for the
Muse VM run (minus 100).

## Method

1. Stage 1, frame in (simulated). The transcript is normalized
   (lowercase, punctuation stripped at word edges, spaces
   collapsed) and split into simulated frames of 3 words.
2. Stage 2, intent. A fixed priority rule classifies the intent:
   stop, greeting, timer, weather, time, date, name, help,
   goodbye, unknown, in that order. Slots: a timer amount (the
   first integer; minutes multiply by 60, so 5 minutes is 300
   seconds) and a weather city (Toronto or Dhaka named in the
   text, default Toronto).
3. Stage 3, answer. A template fills the response from the
   teaching knowledge base. An unknown intent gets a fixed
   fallback that names what the agent can do.
4. Stage 4, tts plan (simulated). The response is split into
   simulated frames of 3 words for playback. An estimated
   speaking time is computed by formula at 150 words per minute
   (60000 / 150 = 400 ms per word). That estimate is a formula,
   not a measurement, and is never mixed into the latency table.
5. Latency budget. Each stage is measured with
   time.perf_counter_ns: 5 batches of 2000 calls per stage per
   case, and the median batch mean per call is reported in
   microseconds. The budget is 5000 microseconds (5 ms) for the
   sum of the four stage means of one case. The budget covers
   these text stages only, not audio capture, models, or network.
6. Barge-in. A VoiceSession state machine has states IDLE,
   LISTENING, THINKING, SPEAKING. A turn ends in SPEAKING while
   frames play. Calling interrupt with a new utterance in
   SPEAKING drops and counts the unplayed frames and processes
   the new utterance at once. Interrupting with stop cancels
   playback, drops the remaining frames, and returns to IDLE.

## Run it

    python level-1-learn/run_learn.py
    python -m unittest tests.test_learn_voice_agent -v
    python tests/test_smoke.py

The runner writes level-1-learn/results_learn.json. The
correctness fields (intents, responses, frame counts, drops) are
deterministic. The latency fields are measured wall-clock values
and vary between runs, so the file is not byte-identical across
runs. The table below is the run of 2026-11-05 recorded in the
committed results file.

## Results (measured 2026-11-05, Muse VM, Python 3.12.3)

| Case | Transcript | Intent | Response | TTS frames | Est. speech ms (formula) | Frame in us | Intent us | Answer us | TTS plan us | Total stage us | Within 5000 us budget |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | Hello there | greeting | Hello. How can I help? | 2 | 2000 | 1.760 | 0.319 | 0.095 | 1.180 | 3.354 | yes |
| C02 | What time is it | time | The time is 10:30. | 2 | 1600 | 2.183 | 0.514 | 0.213 | 1.103 | 4.013 | yes |
| C03 | What is the date today | date | The date is 2026-11-05. | 2 | 1600 | 2.367 | 0.656 | 0.223 | 1.092 | 4.338 | yes |
| C04 | What is the weather in Toronto | weather | The weather in Toronto is clear, 12 degrees Celsius. | 3 | 3600 | 2.528 | 0.963 | 0.437 | 1.609 | 5.537 | yes |
| C05 | How is the weather in Dhaka | weather | The weather in Dhaka is humid, 29 degrees Celsius. | 3 | 3600 | 2.527 | 1.256 | 0.431 | 1.588 | 5.802 | yes |
| C06 | What is the weather | weather | The weather in Toronto is clear, 12 degrees Celsius. | 3 | 3600 | 2.159 | 0.978 | 0.441 | 1.574 | 5.152 | yes |
| C07 | Set a timer for 5 minutes | timer | Timer set for 300 seconds. | 2 | 2000 | 2.447 | 1.054 | 0.329 | 1.213 | 5.043 | yes |
| C08 | Set a timer for 30 seconds | timer | Timer set for 30 seconds. | 2 | 2000 | 2.650 | 1.074 | 0.327 | 1.227 | 5.278 | yes |
| C09 | What is your name | name | My name is Voice Lab, a teaching voice agent. | 3 | 3600 | 2.138 | 0.754 | 0.320 | 1.610 | 4.822 | yes |
| C10 | What can you do | help | You can ask for the time, the date, the weather, or a timer. | 5 | 5200 | 2.170 | 0.755 | 0.157 | 2.081 | 5.163 | yes |
| C11 | Goodbye for now | goodbye | Goodbye. | 1 | 400 | 1.870 | 0.696 | 0.153 | 0.707 | 3.426 | yes |
| C12 | Tell me about quantum tunneling | unknown | I do not know that yet. Ask for the time, the date, the weather, or a timer. | 6 | 6800 | 2.414 | 1.019 | 0.170 | 2.492 | 6.095 | yes |

Barge-in scenarios (deterministic counts):

| Scenario | First response frames | Played before interrupt | Interrupt | Dropped | Result |
| --- | --- | --- | --- | --- | --- |
| B1 | 3 (weather in Toronto) | 2 | What time is it | 1 | New response: The time is 10:30. State SPEAKING |
| B2 | 5 (help text) | 1 | Stop | 4 | Playback cancelled, no new response. State IDLE |

Summary: On 12 labelled text cases, a simulated voice agent loop (text transcripts in, text responses out, no real ASR or TTS model) matched the expected intent 12 of 12 and the expected exact response 12 of 12, and its measured total stage latency was within a 5000 microsecond budget on 12 of 12 cases (mean 4.835 microseconds, max 6.095 microseconds). In 2 barge-in scenarios it dropped 5 unplayed frames in total. 30 unit tests passed.

Hand checks: the mean total is the mean of the 12 per-case
totals in the table (sum 58.023 microseconds, divided by 12 =
4.835). Drops are 1 plus 4 = 5. The timer slot for 5 minutes is
5 times 60 = 300 seconds. The weather response in C04 has 9
words, so it makes 3 frames of 3 words and its formula estimate
is 9 times 400 = 3600 ms. The help response in C10 has 13 words,
so it makes 5 frames (3, 3, 3, 3, 1), and playing 1 then stopping
drops the other 4.

Jev claim_check gate on the summary claim above: model
jev-1.13.0, question id supported, noul 0.87, route ACT (clear
at 0.85 or above in the claim_check bands), 756 input tokens,
20 output tokens. A first, longer claim that also carried the
grade scored 0.44 and was reworded to evidence only before this
run. Spec and results:
hidden_files/jev-p18-learn-claim-spec-2026-11-05.json and
hidden_files/jev-p18-learn-claim-results-2026-11-05.json in the
goal workspace.

## Failure modes and limits

- Simulated audio only: transcripts stand in for ASR, so ASR
  errors, accents, noise, and partial streaming transcripts are
  not measured at all. Framing by word groups is a teaching
  stand-in for real audio framing, not a codec or a stream.
- No real TTS: no voice, prosody, or audio is produced. The
  speaking time is a fixed-rate formula, not a synthesis time.
- Rule intent, fixed knowledge base: keyword priority misses
  paraphrases (for example, asking the hour without the word
  time falls to unknown), the clock and date are fixed teaching
  records, weather covers two cities, and the timer is only
  parsed, it never counts down.
- The latency budget is nearly free to pass at this scale: the
  four text stages run in microseconds, so a 5 ms budget shows
  the accounting shape, not a hard real-time result. Real voice
  latency is dominated by ASR, model, TTS, and network time,
  none of which exist here. Measured times also vary by run and
  by machine, and batch timing averages out per-call jitter.
- Barge-in is a state machine on simulated frames: there is no
  microphone, no voice activity detection, and no overlapping
  audio, so a real interruption (talking over playing audio) is
  modelled, not handled.
- One session, one speaker, no persistence: interruptions,
  memory, and identity do not survive a restart.
- This level was run on the Muse VM (CPU), not on its fleet
  node BlackBox. That costs a grade deduction, named below.

## Grade

Grade: 8,500 of 10,000 for this Learn level.

Deductions (they sum to 1,500):
- No real ASR or TTS model, simulated audio framing only,
  with text standing in for both audio directions: minus 600.
- Deterministic keyword intent and a fixed teaching knowledge
  base (two weather cities, a fixed clock and date), with no
  LLM answer step: minus 400.
- Small designed case set: 12 turns and 2 barge-in scenarios,
  all written for this level: minus 250.
- Run on the Muse VM (CPU), not the assigned BlackBox fleet
  node (NEEDS-BLACKBOX-ON): minus 100.
- The latency budget covers only the four text stages at
  microsecond scale, with no audio, network, streaming, or
  model latency, and measured times vary between runs:
  minus 100.
- One session at a time, no concurrency, no persistence, and
  the parsed timer never actually runs: minus 50.

## What Build adds next

Real speech in and out: a local ASR model and a TTS model on
BlackBox in the same loop, streaming partial transcripts, real
barge-in over playing audio, and a latency budget that includes
model and audio time. See the root README level map.
