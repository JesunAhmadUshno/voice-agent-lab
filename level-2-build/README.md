# Level 2, Build: voice-agent-lab

Status: DONE (2026-11-05). An end-to-end voice loop other people
can run: streaming transcript partials in, a dialogue answer with
conversation state, real WAV audio out, and barge-in over real
audio frames. Built with the Python standard library only, reusing
the Learn turn by import. The Build spec, written before the code,
is BUILD-SPEC.md in this folder.

## Honest scope line

There is still no real ASR model, no TTS voice, and no LLM in
this loop, and every substitution is named in BUILD-SPEC.md with
the checks behind it. Speech in is a text transcript delivered as
cumulative word partials, plus a deterministic simulated ASR noise
map. The answer step is the Learn deterministic intent rule and
template knowledge base, reused by import, with Build dialogue
state on top. Speech out is a deterministic tone synthesis: each
response word becomes a 120 ms sine segment at a word-derived
frequency, separated by 40 ms of silence, written as a real WAV
stream (8000 Hz, 16-bit mono). The WAV data, its duration, and
its energy split are real and measured from sample counts. The
audio carries no intelligible speech, and no voice quality or
recognition accuracy is claimed. This level ran on the Muse VM
(CPU). BlackBox, the assigned fleet node, was ON this cycle and
verified by the coordinator, but this Build scope has no GPU
step, so no GPU was used and the grade carries the named
fleet-node deduction.

## Method

1. Core turn (single). The Learn run_turn classifies the intent
   and fills the template response. Build adds two records to
   every turn: a streaming trace and an audio record.
2. Streaming. The normalized transcript is replayed as cumulative
   word partials and the Learn classifier runs on each partial.
   The runner records the first partial whose intent equals the
   final expected intent, and whether the intent stays stable
   from that partial to the end. On the 20 single turns the mean
   first correct partial is 2.7, the intent is stable from first
   correct in 20 of 20 cases, and in 15 of 20 cases the intent is
   already correct before the last word arrives.
3. Audio out. synthesize_wav builds the tone WAV for the
   response: 960 samples per word (120 ms) plus 320 samples of
   silence (40 ms) between words, no trailing gap. Frames are
   160 samples (20 ms). A frame is speech when its root-mean-
   square energy is above 100 (tone frames sit near 5657,
   silence frames are exactly 0). Duration is the sample count
   divided by 8000 Hz: arithmetic on counts, not a clock reading.
4. Dialogue. DialogueSession keeps last intent, last city, last
   response, and one pending slot. A weather follow-up that names
   only a city (And in Dhaka) reuses the weather intent with the
   new city. A timer request with no amount answers with the
   clarifying question and fills the slot from the next turn
   (5 minutes becomes 300 seconds). Say that again replays the
   last response.
5. ASR noise. simulate_asr maps the word weather to whether and
   drops the word the, deterministically. The same 20 transcripts
   are scored through it, with word error rate from a word-level
   Levenshtein distance over the normalized reference.
6. Barge-in over audio. AudioSession plays the response WAV
   frames. interrupt drops the unplayed frames, counts them, and
   processes the new utterance through the same dialogue session,
   so context survives an interruption. A stop interrupt cancels
   playback and returns to IDLE.

## Run it

    python level-2-build/run_build.py
    python -m unittest tests.test_build_voice_agent -v
    python -m unittest discover -s tests -v
    python tests/test_smoke.py

The runner writes level-2-build/results_build.json. The file
holds no wall-clock field, so it is byte-identical across runs
(sha256 ed5699dad566ac56 verified on two runs of the shipped
code).

## Results (measured 2026-11-05, Muse VM, Python 3.12.3)

| Case | Transcript | Intent | Response correct | WAV bytes | Duration ms | Frames (speech/silence) | First correct partial |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | Hello there | greeting | true | 12204 | 760.0 | 38 (30/8) | 1 of 2 |
| B02 | What time is it | time | true | 9644 | 600.0 | 30 (24/6) | 2 of 4 |
| B03 | What is the date today | date | true | 9644 | 600.0 | 30 (24/6) | 4 of 5 |
| B04 | What is the weather in Toronto | weather | true | 22444 | 1400.0 | 70 (54/16) | 4 of 6 |
| B05 | How is the weather in Dhaka | weather | true | 22444 | 1400.0 | 70 (54/16) | 4 of 6 |
| B06 | What is the weather | weather | true | 22444 | 1400.0 | 70 (54/16) | 4 of 4 |
| B07 | Set a timer for 5 minutes | timer | true | 12204 | 760.0 | 38 (30/8) | 3 of 6 |
| B08 | Set a timer for 30 seconds | timer | true | 12204 | 760.0 | 38 (30/8) | 3 of 6 |
| B09 | Set a timer for 2 minutes | timer | true | 12204 | 760.0 | 38 (30/8) | 3 of 6 |
| B10 | What is your name | name | true | 22444 | 1400.0 | 70 (54/16) | 4 of 4 |
| B11 | What can you do | help | true | 32684 | 2040.0 | 102 (78/24) | 4 of 4 |
| B12 | Goodbye for now | goodbye | true | 1964 | 120.0 | 6 (6/0) | 1 of 3 |
| B13 | Tell me about quantum tunneling | unknown | true | 42924 | 2680.0 | 134 (102/32) | 1 of 5 |
| B14 | Hi there | greeting | true | 12204 | 760.0 | 38 (30/8) | 1 of 2 |
| B15 | Set a timer for 90 seconds | timer | true | 12204 | 760.0 | 38 (30/8) | 3 of 6 |
| B16 | What is the weather in Dhaka today | weather | true | 22444 | 1400.0 | 70 (54/16) | 4 of 7 |
| B17 | Please set a timer | timer | true | 17324 | 1080.0 | 54 (42/12) | 4 of 4 |
| B18 | Bye now | goodbye | true | 1964 | 120.0 | 6 (6/0) | 1 of 2 |
| B19 | Hey | greeting | true | 12204 | 760.0 | 38 (30/8) | 1 of 1 |
| B20 | What time is it in Toronto | time | true | 9644 | 600.0 | 30 (24/6) | 2 of 6 |

Dialogue turns (all 13 matched expected intent and exact
response):

| Dialogue | Transcript | Intent | Response |
| --- | --- | --- | --- |
| D1 | What is the weather in Toronto | weather | The weather in Toronto is clear, 12 degrees Celsius. |
| D1 | And in Dhaka | weather | The weather in Dhaka is humid, 29 degrees Celsius. |
| D1 | What about Toronto | weather | The weather in Toronto is clear, 12 degrees Celsius. |
| D2 | Set a timer | timer_pending | For how long should I set the timer? |
| D2 | 5 minutes | timer | Timer set for 300 seconds. |
| D2 | Say that again | repeat | Timer set for 300 seconds. |
| D3 | What time is it | time | The time is 10:30. |
| D3 | Say that again | repeat | The time is 10:30. |
| D4 | Hello there | greeting | Hello. How can I help? |
| D4 | What can you do | help | You can ask for the time, the date, the weather, or a timer. |
| D4 | Goodbye for now | goodbye | Goodbye. |
| D5 | Tell me about quantum tunneling | unknown | I do not know that yet. Ask for the time, the date, the weather, or a timer. |
| D5 | What is the date today | date | The date is 2026-11-05. |

Noise runs: intent correct 16 of 20, mean word error rate
0.0826. The 4 failures are exactly the 4 weather cases (B04,
B05, B06, B16): weather becoming whether removes the only
weather keyword, so each falls to unknown. The one date case
with a dropped the (B03, WER 0.2) still classifies correctly.
Per-case WER values are in results_build.json.

Barge-in scenarios over audio frames:

| Scenario | First response frames | Played before interrupt | Interrupt | Dropped | Result |
| --- | --- | --- | --- | --- | --- |
| A1 | 70 (weather in Toronto) | 10 | What time is it | 60 | New response: The time is 10:30. State SPEAKING |
| A2 | 102 (help text) | 1 | Stop | 101 | Playback cancelled, no new response. State IDLE |
| A3 | 6 (goodbye) | 2 | What is the date today | 4 | New response: The date is 2026-11-05. State SPEAKING |

Summary: On 20 labelled single turns, the Build voice pipeline (streaming transcript partials in, Learn rule answer reused by import, tone-synthesized WAV out, no ASR model, no TTS model, and no LLM) matched the expected intent 20 of 20 and the expected exact response 20 of 20, and on 5 dialogues it matched intent and exact response on 13 of 13 turns. Through a deterministic simulated ASR noise map (weather to whether, the dropped, mean word error rate 0.0826) intent accuracy fell to 16 of 20, with all 4 failures on weather cases. It synthesized 323440 WAV bytes (20160.0 ms, 1008 frames of 20 ms) for the 20 single-turn responses, and in 3 barge-in scenarios over audio frames it dropped 165 unplayed frames in total. 53 unit tests passed.

Hand checks: the audio total is the sum of the 20 per-case WAV
byte counts in the table, and 323440 also equals 20 WAV headers
of 44 bytes plus 2 bytes for each of the 161280 total samples
(20160.0 ms at 8000 Hz). Speech and silence frames sum to the
frame total: 786 plus 222 equals 1008. Barge-in drops are 60
plus 101 plus 4 equals 165. The noise mean WER is the mean of
the 20 per-case values in results_build.json (the five non-zero
values are 0.2, 0.3333, 0.3333, 0.5, and 0.2857, sum 1.6523,
divided by 20 is 0.0826). The D2 slot fill is 5 times 60 equals
300 seconds, through the Learn slot rule.

Jev claim_check gate on the summary claim above: model
jev-1.13.0, question id supported, noul 0.72, route REVIEW
(clear at 0.85 or above, block at 0.10 or below, review between,
in the claim_check bands), 1043 input tokens, 20 output tokens.
Spec and results:
hidden_files/jev-p18-build-claim-spec-2026-11-05.json and
hidden_files/jev-p18-build-claim-results-2026-11-05.json in the
goal workspace.

## Failure modes and limits

- No real ASR: partials are a replay of a complete transcript,
  so recognition errors are only the one named substitution map,
  and accents, noise, and endpointing on real speech are not
  measured. The weather result shows the shape of the risk: one
  substituted keyword word removes the intent entirely, because
  the classifier is a keyword rule with no fallback similarity.
- No real TTS voice: the tone WAV proves the audio plumbing
  (framing, duration, energy, playback, interruption) and nothing
  about speech quality, prosody, or intelligibility.
- No LLM answer step: responses are templates over a fixed
  teaching knowledge base (fixed clock, fixed date, two weather
  cities). Paraphrases outside the keyword rules fall to unknown,
  as in Learn.
- Dialogue state is small: one pending slot, one remembered city
  and response, follow-ups only in the two written shapes (city
  only, repeat). Anything else is treated as a fresh turn.
- No device or network path: there is no microphone capture, no
  speaker playback, no streaming transport, and no concurrency.
  Frames are played by counting, not by a sound device, so real
  time playback behaviour is modelled, not observed.
- The latency story of Learn (text-stage microseconds) is not
  extended here: Build reports audio duration from sample
  counts, which is content length, not system latency. The
  local against cloud latency budget study is Deep scope.

## Grade

Grade: 7,500 of 10,000 for this Build level.

Deductions (they sum to 2,500):
- No real ASR model: speech in stays transcript partials plus
  one deterministic noise map, with real recognition unmeasured:
  minus 700.
- No real TTS voice: tone synthesis is real WAV data but carries
  no intelligible speech: minus 600.
- The answer step is the Learn rule intent and fixed knowledge
  base, with no LLM as SPEC names: minus 500.
- Designed synthetic evaluation sets: 20 single turns and 13
  dialogue turns, all authored for this level: minus 300.
- Streaming is a word-prefix replay of a complete transcript,
  not incremental recognition over audio: minus 200.
- Run on the Muse VM (CPU), not the assigned BlackBox fleet
  node (the node was on; this scope has no GPU step): minus 100.
- One session at a time, no persistence, no microphone or
  playback device, and the parsed timer never counts down:
  minus 100.

## What Deep adds next

The latency budget study from SPEC: where every millisecond
goes, stage by stage, local against cloud speech models, with
the failure modes of the budget written down. See the root
README level map.
