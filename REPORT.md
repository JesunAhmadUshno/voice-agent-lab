# Report: voice-agent-lab

Status: FUNCTIONAL, not pre-registered (2026-11-08). Every number below
comes from a committed file in experiments/ or results/, named next to
it. Nothing here is confirmatory: no plan was locked before the results
(PROPOSAL.md, docs/decisions/0001), so the claims are scored against the
budgets and criteria the designs stated, as exploratory results.

## Scope in one paragraph

A real-time voice agent study: speech in, answer, speech out, with a
latency budget study. The local side is measured and the cloud side is
modelled, and the two are never mixed. There is no real ASR model, no
real TTS voice, and no LLM in any stage: speech in is text transcripts or
transcript partials, speech out is text responses in Stage 1 and
tone-synthesized WAV in Stages 2 and 3, and the answer step is a
deterministic keyword rule over a fixed teaching knowledge base.

The perfect intent and response scores are weak evidence: every case set
is synthetic and authored for this project, the knowledge base is fixed
(a fixed clock, a fixed date, weather for two cities), and the dominant
Deep stage times a sine loop, not a speech model.

## Headline, traced to the evidence

The README headline comes from one file,
experiments/runs/2026-11-07-probes-aarch64.json (5 full re-measurements
of the Deep stage timings on an aarch64 host, Python 3.12.3, recorded in
the file). tests/test_layout.py recomputes each number from that file and
fails if the README drifts from it.

| Headline number | Field in the evidence file | Value |
| --- | --- | --- |
| Synthesis largest stage, 20 of 20 turns | repeated_runs.spread.dominant_stage_cases (every run) | 20, 20, 20, 20, 20 |
| Synthesis share of the mean turn, 87.6% | repeated_runs.spread.wav_share_of_mean_total.mean | 0.876, 95% t interval 0.875 to 0.877 |
| Median turn, 1.316 ms | repeated_runs.spread.median_total_median_us.mean | 1315.74 us, 95% t interval 1313.814 to 1317.666 |
| Inside the 100 ms budget | repeated_runs.spread.within_budget (every run) | 20 of 20 |
| Held-out paraphrases understood, 9 of 20 | paraphrase.intent_correct, paraphrase.n | 9, 20 (11 fell to unknown) |

The interval is a 95% Student t interval over 5 runs on one machine:
between-run spread, not between-machine spread. The recorded Deep run on
the Muse VM (experiments/runs/2026-11-05-deep-muse-vm.json) is one run,
with no interval: median turn 7255.203 microseconds, synthesis about 89
percent of the mean turn, synthesis largest in 20 of 20. Absolute times
differ by several times between the machines; the stage ordering held on
both. Raw per-call samples were not saved for either run.

## Claims scored

Each criterion was written in the Build or Deep design before that
stage's runner ran (PROPOSAL.md), but committed with the results, so
these are stated criteria, not locked hypotheses.

| Claim or criterion | Evidence | Result |
| --- | --- | --- |
| Learn: every case inside the 5000 microsecond text-stage budget | experiments/runs/2026-11-05-learn-muse-vm.json summary.within_budget | Met, 12 of 12 (mean 4.835, max 6.095 microseconds) |
| Build: every single turn matches intent and exact response | results/build.json summary.single_intent_correct, single_response_correct | Met, 20 of 20 |
| Build: every dialogue turn matches | results/build.json summary.dialogue_intent_correct | Met, 13 of 13 |
| Build: intent survives simulated ASR noise (reported, not gated) | results/build.json summary.noise_intent_correct | Miss, 16 of 20 (all 4 failures on weather cases, mean WER 0.0826) |
| Deep: every turn inside 100 ms on medians | Muse VM run summary.within_budget; probe runs within_budget | Met, 20 of 20 on both machines |
| Deep: every stage inside its design share on medians | Muse VM run, per-case stage medians | Met in every case |
| Deep: barge-in drop median inside 5 ms | Muse VM run summary.barge_drop_within_budget | Met, 3 of 3 (at most 75.864 microseconds) |
| Deep: no case total median over the 500 ms ceiling | Muse VM run summary.within_ceiling | Met, 20 of 20 |
| Tails: per-stage p99 sums inside 100 ms (not a stated criterion, checked after) | Muse VM run, sum of stage p99_us per case | Miss, 11 of 20 over budget on the shared VM; 0 of 20 in each probe run |
| The rule generalises to rewordings (checked after, held out) | probe run paraphrase.intent_correct | Miss, 9 of 20 |
| Local against cloud speech pipeline | none: the cloud side is constants | Not answered: modelled only (mean 1212.75 ms), never measured |

## What the ML profile still needs (why the verdict is not Evaluated)

- A measured baseline a reviewer would expect: a real local ASR, TTS
  voice and LLM behind the same stage interfaces, and a measured cloud
  pipeline. Neither exists; the cloud side is five stated constants.
- Ablations: none were run.
- Uncertainty on every headline number: only the probe runs carry
  intervals; the recorded Learn and Deep runs are single runs with no
  saved raw samples.
- Compute, data and versions: recorded per run (machine, Python 3.12.3,
  standard library only); the case sets are authored for this project.
- A locked proposal before a confirmatory run.

## Results at a glance (formerly the README benchmarks)

### Learn (Level 1)

Measured 2026-11-05 with src/run_learn.py on the Muse VM (CPU, Python 3.12.3, standard library only). The loop is simulated: text transcripts stand in for ASR output and text responses stand in for TTS output, with simulated frames of 3 words. No real ASR or TTS model ran. Latency is the measured wall-clock mean per stage (time.perf_counter_ns, 5 batches of 2000 calls, median batch mean), and the budget is 5000 microseconds for the sum of the four text-stage means of one case. Full per-case table, barge-in scenarios, and failure modes are in Stage 1 below.

| Test | Result |
| --- | --- |
| Cases | 12 labelled text cases |
| Intent accuracy | 12 of 12 |
| Exact response match | 12 of 12 |
| Total stage latency, mean of 12 cases | 4.835 microseconds |
| Total stage latency, max of 12 cases | 6.095 microseconds |
| Within 5000 microsecond budget | 12 of 12 |
| Barge-in scenarios | 2, with 5 unplayed frames dropped in total (1 plus 4) |
| Unit tests | 30 passed, plus the scaffold smoke test |

### Build (Level 2)

Measured 2026-11-05 with src/run_build.py on the Muse VM (CPU, Python 3.12.3, standard library only). The loop runs end to end: streaming transcript partials in, the Learn rule answer reused by import with dialogue state on top (weather follow-ups, timer slot filling, repeat), and tone-synthesized WAV out (real WAV data at 8000 Hz, no intelligible speech). No ASR model, no TTS model, and no LLM ran; the substitutions are named in PROPOSAL.md (Build design). The results file holds no wall-clock field and is byte-identical across runs. Full per-case tables, dialogue turns, noise runs, and failure modes are in Stage 2 below.

| Test | Result |
| --- | --- |
| Single turns | 20 labelled cases |
| Intent accuracy, single | 20 of 20 |
| Exact response match, single | 20 of 20 |
| Dialogue turns | 13 turns in 5 dialogues |
| Intent and response, dialogues | 13 of 13 |
| Intent through simulated ASR noise | 16 of 20 (mean WER 0.0826, all 4 failures on weather cases) |
| WAV synthesized for single responses | 323440 bytes, 20160.0 ms, 1008 frames of 20 ms |
| Barge-in scenarios | 3, with 165 unplayed audio frames dropped in total (60 plus 101 plus 4) |
| Unit tests | 53 passed (30 Learn, 23 Build), plus the scaffold smoke test |

### Deep (Level 3)

Measured 2026-11-05 with src/run_deep.py on the Muse VM (CPU, Python 3.12.3, standard library only). A latency budget study: every stage that runs locally is timed individually with time.perf_counter_ns (pooled per-call samples over 3 batches, medians and nearest-rank percentiles), and a cloud pipeline built only from stated constants is modelled next to it (modelled only, never measured, no cloud service called). No ASR model, no TTS model, and no LLM ran; the substitutions are named again in PROPOSAL.md (Deep design). The results file contains measured timings and is not byte-identical across runs; its deterministic fields are identical across runs. The rest of the v2 Deep scope is the v1.1 backlog below. Full budget table and failure modes are in Stage 3 below.

| Test | Result |
| --- | --- |
| Cases | 20 labelled turns plus 3 barge-in scenarios |
| Intent and exact response | 20 of 20 |
| Dominant stage | WAV synthesis in 20 of 20 cases |
| Total local latency, median case (sum of stage medians) | 7255.203 microseconds |
| Total local latency, max case median | 41688.082 microseconds |
| Within the 100 ms local budget (medians) | 20 of 20 |
| Barge-in drop path median | at most 75.864 microseconds, 165 frames dropped in total |
| Modelled cloud total (modelled only) | mean 1212.75 ms, 29.865 to 1010.23 times the local totals |
| Unit tests | 70 passed (30 Learn, 23 Build, 17 Deep), plus the scaffold smoke test |

### Add-on probes (Deep)

src/run_probes.py wrote experiments/runs/2026-11-07-probes-aarch64.json without touching experiments/runs/2026-11-05-deep-muse-vm.json: the Deep stage timings re-measured 5 times (between-run spread), sine-loop time to first word against the whole reply, and the keyword rule on 20 held-out paraphrases (experiments/cases/cases_paraphrase.json). The probes ran on a different machine from the Deep study (recorded in the file), so only shapes and the paraphrase score carry over. The paraphrase result is a negative one: the rule understood 9 of 20 rewordings. See docs/research-review.md for how this fits the study's gaps.


## Background

Related work (formerly in docs/research-review.md; context only, nothing here is compared like for like):

- Stivers, T., et al. (2009). Universals and cultural variation in
  turn-taking in conversation. *PNAS* 106(26), 10587-10592. Human turn gaps
  cluster around a few hundred milliseconds across languages, which is the
  scale a whole voice-agent turn competes with.
- Levinson, S. C., and Torreira, F. (2015). Timing in turn-taking and its
  implications for processing models of language. *Frontiers in Psychology*
  6, 731. Argues listeners plan responses before the turn ends, the human
  analogue of streaming partial intents.
- ITU-T Recommendation G.114 (2003). One-way transmission time. The
  telephony guidance on mouth-to-ear delay, a standard reference point for
  conversational latency budgets.
- Radford, A., et al. (2023). Robust speech recognition via large-scale weak
  supervision. *ICML 2023* (arXiv:2212.04356). The Whisper models, a
  realistic local ASR candidate for remaining gap 1.
- Sohn, J., Kim, N. S., and Sung, W. (1999). A statistical model-based voice
  activity detector. *IEEE Signal Processing Letters* 6(1), 1-3. A standard
  VAD baseline against which the repo's single RMS threshold is a toy.
- Levenshtein, V. I. (1966). Binary codes capable of correcting deletions,
  insertions, and reversals. *Soviet Physics Doklady* 10(8), 707-710. The
  edit distance behind the repo's word error rate.

## Stage 1. Simulated loop (formerly Level 1, Learn)

Status: DONE (2026-11-05). A real-time voice agent loop built
small on CPU: speech in, answer, speech out, with barge-in
handling and a measured per-stage latency budget. Built with the
Python standard library only.

### Honest scope line

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
design, and the Muse VM run is named as a limit below.

### Method

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

### Run it

    python src/run_learn.py
    python -m unittest tests.test_learn_voice_agent -v
    python -m unittest tests.test_layout -v

The run of 2026-11-05 is experiments/runs/2026-11-05-learn-muse-vm.json;
a new run writes a new dated file there and never overwrites it. The
correctness fields (intents, responses, frame counts, drops) are
deterministic. The latency fields are measured wall-clock values
and vary between runs, so the file is not byte-identical across
runs. The table below is the run of 2026-11-05 recorded in the
committed results file.

### Results (measured 2026-11-05, Muse VM, Python 3.12.3)

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
level's internal score scored 0.44 and was reworded to evidence only before this
run. Spec and results:
hidden_files/jev-p18-learn-claim-spec-2026-11-05.json and
hidden_files/jev-p18-learn-claim-results-2026-11-05.json in the
goal workspace.

### Failure modes and limits

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
  node BlackBox.


### What the next stage was to add

Real speech in and out: a local ASR model and a TTS model on
BlackBox in the same loop, streaming partial transcripts, real
barge-in over playing audio, and a latency budget that includes
model and audio time.

## Stage 2. End-to-end loop (formerly Level 2, Build)

Status: DONE (2026-11-05). An end-to-end voice loop other people
can run: streaming transcript partials in, a dialogue answer with
conversation state, real WAV audio out, and barge-in over real
audio frames. Built with the Python standard library only, reusing
the Learn turn by import. The Build spec, written before the code,
is the Build design in PROPOSAL.md.

### Honest scope line

There is still no real ASR model, no TTS voice, and no LLM in
this loop, and every substitution is named in PROPOSAL.md (Build design) with
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
step, so no GPU was used; the fleet-node gap is named as a
limit.

### Method

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

### Run it

    python src/run_build.py
    python -m unittest tests.test_build_voice_agent -v
    python -m unittest discover -s tests -v
    python -m unittest tests.test_layout -v

The runner writes results/build.json. The file
holds no wall-clock field, so it is byte-identical across runs
(sha256 ed5699dad566ac56 verified on two runs of the shipped
code).

### Results (measured 2026-11-05, Muse VM, Python 3.12.3)

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
Per-case WER values are in results/build.json.

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
the 20 per-case values in results/build.json (the five non-zero
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

### Failure modes and limits

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


### What the next stage was to add

The latency budget study from SPEC: where every millisecond
goes, stage by stage, local against cloud speech models, with
the failure modes of the budget written down.

## Stage 3. Latency budget study (formerly Level 3, Deep)

Status: DONE (2026-11-05). A latency budget study of the Build
voice pipeline: where every millisecond goes, stage by stage,
measured locally, with a modelled cloud pipeline next to it.
Built with the Python standard library only, reusing the Learn
and Build code by import. The Deep spec, written before the
code, is the Deep design in PROPOSAL.md.

### Honest scope line

The local side is measured and the cloud side is modelled, and
the two are never mixed. Local stages are the stages that
actually run in this repo: frame and VAD split, streaming
partial intent tracing, intent and answer, WAV synthesis, and
barge-in handling. The cloud pipeline is built only from stated
constants (network 80 ms, ASR final 300 ms, LLM answer 700 ms,
TTS 100 ms plus 5 ms per response word), is labelled modelled
in every file, and was never measured: no cloud service was
called and no network was used. The constants are illustrative
modelling choices, not sourced measurements of any real
service.

The Build substitutions stay in force, named again here: there
is no real ASR model (speech in is still transcript partials,
so real recognition latency is not measured locally), no real
TTS voice (the measured synthesis time is the cost of a sine
loop, not of a speech model), and no LLM (the measured answer
time is the cost of a keyword rule over a fixed teaching
knowledge base, not of model inference). This level ran on the
Muse VM (CPU). BlackBox is the assigned fleet node, but this
study has no GPU step: every stage is CPU code from Learn and
Build, so no GPU was used; the fleet-node gap is named as a
limit.

### Method

1. Workloads. The 20 Build single turns (experiments/cases/cases_deep.json, the
   same transcripts and expected responses as Build) plus the
   3 Build barge-in scenarios over audio frames.
2. Timing. Each stage call is timed individually with
   time.perf_counter_ns, after 3 untimed warmup calls, in 3
   repeated batches whose per-call samples are pooled. Sample
   counts per case: intent and answer 300, streaming 300,
   frame and VAD 100 requested (99 pooled: 3 batches of 33),
   WAV synthesis 30, barge-in drop 60, barge-in full 20
   requested (18 pooled: 3 batches of 6).
   Per stage and case the results file reports n, mean,
   median, p90, p99, min, and max in microseconds.
   Percentiles are nearest-rank.
3. Barge-in timing. The setup (build a session, synthesize the
   first response, play the opening frames) runs untimed before
   every timed call. The drop path times interrupt with stop.
   The full path times interrupt with the scenario question,
   which drops the unplayed frames and runs a whole new turn.
4. Budget. Set in PROPOSAL.md (Deep design) before measuring: 100 ms for
   the sum of the four per-turn stage medians of one case
   (design shares: WAV synthesis 70 ms, frame and VAD 10 ms,
   streaming 10 ms, intent and answer 5 ms, headroom 5 ms),
   plus a 5 ms budget for the barge-in drop median. The budget
   is a reported result; the runner exit gate is the
   deterministic correctness fields plus a 500 ms hard ceiling
   on any case total median, because shared machines vary.
5. Modelled cloud. Per case: 1180 plus 5 times the response
   word count, in milliseconds, from the constants above.
   Modelled only, in every table and sentence.

The shipped run is experiments/runs/2026-11-05-deep-muse-vm.json (sha256
4aba845adb148f94 for the shipped run). Its latency fields are
measured wall-clock values and vary between runs, so the file
is NOT byte-identical across runs, and no such claim is made.
Its deterministic fields (intents, responses, frame counts,
drops, audio sizes, modelled totals) were verified identical
across two runs of the shipped code.

### Results (measured 2026-11-05, Muse VM, Python 3.12.3)

Per-case stage medians in microseconds, with the WAV p90, the
total (sum of the four stage medians), and the modelled cloud
total for the same response:

| Case | Words | Frame+VAD med us | Streaming med us | Intent+answer med us | WAV med us | WAV p90 us | Total med us | Within 100 ms | Modelled cloud ms | Modelled/local |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | 5 | 706.646 | 7.930 | 1.602 | 5986.958 | 9495.782 | 6703.136 | yes | 1205.0 | 179.77 |
| B02 | 4 | 674.202 | 13.029 | 2.413 | 5284.480 | 19266.374 | 5974.124 | yes | 1200.0 | 200.87 |
| B03 | 4 | 617.549 | 16.811 | 2.729 | 5108.377 | 7127.797 | 5745.466 | yes | 1200.0 | 208.877 |
| B04 | 9 | 1651.591 | 23.932 | 4.101 | 14237.515 | 71856.323 | 15917.139 | yes | 1225.0 | 76.962 |
| B05 | 9 | 1430.952 | 23.858 | 4.769 | 14107.977 | 65665.842 | 15567.556 | yes | 1225.0 | 78.687 |
| B06 | 9 | 1354.960 | 15.386 | 4.363 | 12779.913 | 61760.235 | 14154.622 | yes | 1225.0 | 86.542 |
| B07 | 5 | 711.609 | 21.783 | 4.195 | 6976.972 | 14976.701 | 7714.559 | yes | 1205.0 | 156.189 |
| B08 | 5 | 1588.810 | 44.233 | 7.128 | 5942.406 | 15057.537 | 7582.577 | yes | 1205.0 | 158.908 |
| B09 | 5 | 766.212 | 21.874 | 4.149 | 6038.587 | 55069.828 | 6830.822 | yes | 1205.0 | 176.402 |
| B10 | 9 | 1325.030 | 14.385 | 2.947 | 12677.557 | 55115.831 | 14019.919 | yes | 1225.0 | 87.375 |
| B11 | 13 | 3586.266 | 14.511 | 2.755 | 38084.550 | 83890.506 | 41688.082 | yes | 1245.0 | 29.865 |
| B12 | 1 | 121.143 | 11.504 | 2.588 | 1056.310 | 10179.395 | 1191.545 | yes | 1185.0 | 994.128 |
| B13 | 17 | 3571.236 | 18.234 | 3.348 | 22994.106 | 76922.542 | 26586.924 | yes | 1265.0 | 47.58 |
| B14 | 5 | 738.033 | 8.018 | 1.645 | 6180.132 | 32624.489 | 6927.828 | yes | 1205.0 | 173.932 |
| B15 | 5 | 720.043 | 21.831 | 4.176 | 5748.684 | 6139.499 | 6494.734 | yes | 1205.0 | 185.527 |
| B16 | 9 | 1366.203 | 28.461 | 4.924 | 10923.665 | 45694.574 | 12323.253 | yes | 1225.0 | 99.408 |
| B17 | 7 | 1034.638 | 14.596 | 2.964 | 10006.883 | 50327.798 | 11059.081 | yes | 1215.0 | 109.865 |
| B18 | 1 | 120.427 | 9.058 | 2.409 | 1040.608 | 1059.865 | 1172.502 | yes | 1185.0 | 1010.23 |
| B19 | 5 | 720.378 | 6.078 | 1.521 | 5673.191 | 15752.249 | 6401.168 | yes | 1205.0 | 188.252 |
| B20 | 4 | 563.574 | 18.120 | 2.625 | 5805.211 | 25950.141 | 6389.530 | yes | 1200.0 | 187.793 |

Stage medians across the 20 cases (median of the per-case
medians, microseconds):

| Stage | Median of medians us | Mean of medians us | Max median us | Design share us |
| --- | --- | --- | --- | --- |
| WAV synthesis | 6109.360 | 9832.704 | 38084.550 | 70000 |
| Frame and VAD split | 752.122 | 1168.475 | 3586.266 | 10000 |
| Streaming partial tracing | 16.099 | 17.682 | 44.233 | 10000 |
| Intent and answer | 2.955 | 3.368 | 7.128 | 5000 |

Findings:

- WAV synthesis dominates: it is the largest stage in 20 of
  20 cases and about 89 percent of the mean total (mean stage
  medians 9832.704 of 11022.228 microseconds). It grows with
  response length: 1040.608 microseconds median for the 1-word
  response (B18) against 22994.106 for the 17-word response
  (B13), because the Build synthesis loops per sample in
  Python (960 samples per word plus 320 per gap). A real
  system would stream synthesis; this pipeline synthesizes
  the whole response before any frame can play, so the full
  synthesis time sits in the response-start latency.
- The text stages are negligible by comparison: streaming
  tracing medians stay under 50 microseconds and intent plus
  answer under 8 microseconds on every case. The Learn text
  budget was never the bottleneck; the audio step is.
- Frame and VAD split is the second stage (median of medians
  752.122 microseconds) and also grows with length, because
  the RMS rule loops per sample in Python.
- Every case is within the 100 ms budget on medians: the
  median case total is 7255.203 microseconds, the mean is
  11022.228, and the worst case (B11, the 13-word help text)
  is 41688.082. Every stage is within its design share on
  medians in every case.
- The tails are not within budget: WAV p90 values reach
  83890.506 microseconds (B11) and p99 values reach
  169298.914, on a shared VM with other work running. The
  budget verdict above is a median verdict, stated as such;
  the tail behaviour is a failure mode below, not hidden.
- The modelled cloud total (mean 1212.75 ms, range 1185.0 to
  1265.0 ms across cases) is 29.865 to 1010.23 times the
  measured local total median. That ratio compares a measured
  local sine-loop pipeline against modelled constants for a
  real cloud speech stack: it shows the shape of the local
  against cloud trade (local compute is not the latency
  problem; the modelled network, recognition, model, and
  speech steps are), and it is not evidence about any real
  cloud service, because nothing cloud was measured.

Barge-in over audio frames (setup untimed, interrupt timed):

| Scenario | First frames | Played | Dropped | Drop median us | Drop p90 us | Full median us | Full p90 us |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 70 | 10 | 60 | 51.326 | 86.868 | 4674.552 | 37853.843 |
| A2 | 102 | 1 | 101 | 75.864 | 116.573 | 76.678 | 137.347 |
| A3 | 6 | 2 | 4 | 10.121 | 13.399 | 4577.467 | 52883.933 |

The drop path is fast: medians of 10.121 to 75.864
microseconds, all within the 5 ms drop budget, because
dropping is a list discard and a state change. The full path
in A1 and A3 costs about 4.6 ms at the median because it runs
a whole new turn, dominated by synthesizing the new short
response. A2 interrupts with stop, so its full path is the
drop path (76.678 microseconds). Total dropped across the 3
scenarios: 165 frames, matching Build.

Summary: On 20 labelled single turns, the Deep latency budget study measured the local stages of the Build voice pipeline on the Muse VM (frame and VAD split, streaming partial intent tracing, Learn rule intent and answer, tone WAV synthesis; no ASR model, no TTS model, no LLM): WAV synthesis was the dominant stage in 20 of 20 cases, the median total local latency was 7255.203 microseconds, the maximum total median was 41688.082 microseconds, and 20 of 20 cases were within the 100 ms local budget. In 3 barge-in scenarios the drop path median was at most 75.864 microseconds and 165 unplayed frames were dropped in total. Against a modelled cloud pipeline built only from stated constants (network 80 ms, ASR final 300 ms, LLM answer 700 ms, TTS 100 ms plus 5 ms per response word, modelled and never measured, mean modelled total 1212.75 ms), the measured local totals were 29.865 to 1010.23 times smaller. 70 unit tests passed.

Hand checks: the B12 modelled total is 1180 plus 5 times 1
word equals 1185.0 ms, and B13 is 1180 plus 5 times 17 equals
1265.0 ms, matching the table. The modelled mean is the mean
of the 20 per-case modelled totals in experiments/runs/2026-11-05-deep-muse-vm.json
(1212.75 ms). The B01 WAV share is 5986.958 divided by
6703.136 equals 89.3 percent. Barge-in drops are 60 plus 101
plus 4 equals 165. The total column is the sum of the four
stage medians in its row (B18: 120.427 plus 9.058 plus 2.409
plus 1040.608 equals 1172.502).

Jev claim_check gate on the summary claim above: model
jev-1.13.0, question id supported, noul 0.63, route
REVIEW (clear at 0.85 or above, block at 0.10 or below,
review between, in the claim_check bands), 1224 input
tokens, 20 output tokens. Spec and results:
hidden_files/jev-p18-deep-claim-spec-2026-11-05.json and
hidden_files/jev-p18-deep-claim-results-2026-11-05.json in
the goal workspace.

### Add-on probes (experiments/runs/2026-11-07-probes-aarch64.json)

src/run_probes.py adds three cheap probes without
touching experiments/runs/2026-11-05-deep-muse-vm.json: the stage timings re-measured 5
times (between-run spread on one machine), sine-loop synthesis
time for the first word against the whole response (ROADMAP
v1.1 item 1, for the tone loop only), and the frozen keyword
rule scored on 20 held-out paraphrases (experiments/cases/cases_paraphrase.json).
They ran on a different machine from the shipped Deep run (the
machine is recorded in the file), so their absolute timings are
not comparable with the Muse VM numbers above; the stage
ordering and the paraphrase score are what carry over.

### Run it

    python src/run_deep.py
    python src/run_probes.py
    python -m unittest tests.test_deep_voice_agent -v
    python -m unittest discover -s tests -v
    python -m unittest tests.test_layout -v

### Failure modes and limits

- Tail latency on a shared machine: medians are stable, but
  p90 and p99 synthesis times spike by an order of magnitude
  when the shared VM is busy (WAV p99 up to 169298.914
  microseconds on B11 in the shipped run). A budget written
  on p99 would fail on this machine. Any production reading
  of these numbers needs a quiet machine and a tail budget,
  not just a median budget.
- Synthesis before playback: the pipeline synthesizes the
  whole response, then plays it. Response-start latency
  therefore includes the full synthesis time, which grows
  linearly with response length (about 1.1 ms per word at
  the median for short responses, more under load). Long
  answers would breach the 100 ms budget on synthesis
  alone: at the B13 rate (22994.106 microseconds for 17
  words, about 1350 microseconds per word), a response of
  about 74 words would cross 100 ms. That extrapolation is
  arithmetic on one measured case, labelled as such.
- The VAD rule is one fixed RMS threshold (100) tuned to the
  tone synthesis (tone frames near 5657, silence exactly 0).
  On real speech, quiet frames would fall under it and loud
  noise over it; no real-audio VAD accuracy is measured.
- Per-call timing overhead: timing every call with
  perf_counter_ns adds two clock reads per call. For the
  intent and answer stage (median 2.955 microseconds) that
  overhead is a visible share of the reported value, so the
  smallest numbers are upper bounds, not exact costs.
- No real ASR, TTS, or LLM latency exists in this study on
  the local side, and the cloud side is constants, not a
  service: the study budgets the plumbing honestly and
  cannot say how a real speech stack times on either side.
  Swapping in a real recognizer or synthesizer changes every
  row; the method, not the numbers, is what carries over.
- One thread, one session, no device: there is no microphone
  capture, no speaker output, no network transport, and no
  concurrent-session load in the measurements. Playback is
  counted frames, not a sound device, so device and driver
  latency is outside the budget entirely.
- Machine dependence: all numbers are this Muse VM, this
  Python (3.12.3), this run. A faster or quieter machine
  moves every median; the stage ordering (synthesis first,
  VAD second, text stages negligible) is the durable claim.


### What remains (v1.1)

See the v1.1 backlog at the end of this report: streaming synthesis with
time-to-first-frame measurement, a real local ASR and TTS
swap-in behind the same stage interface, a measured (not
modelled) cloud comparison where a free tier allows it,
concurrent sessions, and a tail-latency budget on a quiet
machine.

## Review (formerly docs/research-review.md, 2026-11-07)

Reviewed 2026-11-07 against a research rubric. Scope: the three
levels as shipped (Learn, Build, Deep), the committed results files, and the
changes made on the site/live-dashboard branch. Every number below is quoted
from a committed file; the file is named next to it. The "level READMEs" it
names are now the Stage sections of this report. The rubric's per-criterion
ratings are kept internal under the portfolio standard; the evidence behind each
is below. This was a reading review: under the standard, review means a second
reader re-derives every headline number from experiments/, so the Review stage
stays open.

### Assessment

A careful methods and engineering exercise with an unusually honest scope, and
a weak empirical contribution. The measurement discipline is sound, but the system being measured
is a stand-in for a voice agent (keyword rule, sine-tone synthesis, typed
transcripts), so the headline finding ("synthesis dominates the turn") is a
property of the stand-in, not of real speech stacks.

| Criterion | Evidence and reasoning |
| --- | --- |
| --- | --- |
| Research question | "Where does every millisecond of a voice turn go, local against cloud?" (SPEC.md). Clear and answerable, but answered for a substitute pipeline. |
| Hypotheses | The 100 ms budget and per-stage design shares were fixed in PROPOSAL.md (Deep design) before measuring (good), but no falsifiable hypothesis about stage ordering was written down in advance. |
| Method | Per-call `perf_counter_ns` timing after warmup, pooled over 3 batches, nearest-rank percentiles, untimed setup for stateful barge-in paths (Stage 3 below, Method). Measured and modelled numbers are never mixed. |
| Baselines | The only comparison is a cloud pipeline built from five unsourced constants (80/300/700/100 ms + 5 ms per word, latency_lab.py). No measured baseline exists. |
| Statistics and uncertainty | One recorded run per level, medians only, no intervals; raw samples not saved. This change adds a 5-run repeat with spread and a 95% t interval (experiments/runs/2026-11-07-probes-aarch64.json). |
| Reproducibility | Standard library only, CI on Python 3.11 and 3.12, Build results byte-identical (sha256 prefix ed5699dad566ac56, re-verified by the site build). Deep timings vary by design and say so. |
| Threats to validity | Each level README lists failure modes and named limits. The main threat (construct validity) is disclosed but not mitigated. |
| Related work | DOSSIER.md and NOVELTY.md had no citations. A short, verifiable reference list is added below. |
| Limitations | Stated in every README, the root README, and docs/index.md. |

### Gaps, and what that change did about each

#### Fixed in that change (no GPU, no paid API, each run under a minute)

1. **In-browser numbers could drift from the repo.** The dashboard ports the
   Python rules to JavaScript; `site/src/voice.check.mjs` runs inside
   `npm run build` and replays all Learn cases, all Build single turns
   (intent, response, WAV bytes, frames, streaming trace), the 5 dialogues,
   the 20 noise runs (WER to 4 dp), the 3 barge-in scenarios, every Deep
   modelled-cloud total and ratio, and the README's own arithmetic (89%
   synthesis share, about 74 words to cross 100 ms). Any mismatch fails the
   build.
2. **No sensitivity analysis over the cloud constants.** The dashboard's
   cloud window lets a reader move all five constants and recomputes every
   per-case modelled total and modelled/local ratio. It stays labelled
   "modelled, never measured" and adds no new claim.
3. **No between-run variance.** `src/run_probes.py` re-measures the
   Deep stage timings 5 times with the same code and sample counts and
   writes `experiments/runs/2026-11-07-probes-aarch64.json` (experiments/runs/2026-11-05-deep-muse-vm.json is untouched). On that
   machine the median turn ranged 1313.438 to 1317.71 us, the synthesis share
   of the mean turn was 0.876 to 0.878, and synthesis was the largest stage
   in 20 of 20 cases in every run.
4. **One machine only.** The probes ran on a different machine (aarch64,
   Python 3.12.3, recorded in experiments/runs/2026-11-07-probes-aarch64.json) from the Muse VM. Absolute
   times differ by several times, but the stage ordering replicated. This is
   a second machine for the ordering claim, not for the absolute numbers.
5. **Time to first audio never measured (ROADMAP v1.1 item 1).** The probes
   time synthesis of the first word against the whole reply: the median
   whole reply costs 5.013 times the first word (experiments/runs/2026-11-07-probes-aarch64.json). This
   is for the sine loop only and says nothing about a real TTS voice.
6. **Generalisation unmeasured.** 20 held-out paraphrases
   (`experiments/cases/cases_paraphrase.json`), written after the rule was frozen
   and not used to tune it, are scored by the unchanged rule: 9 of 20
   understood, 11 fell to unknown. This is reported as a negative result,
   and the rule was deliberately not changed to pass them.
7. **Tail fragility.** The recorded Deep run puts 11 of 20 turns over budget
   when per-stage p99s are summed (computed on the dashboard from
   experiments/runs/2026-11-05-deep-muse-vm.json). The probe runs record the same count per run (0 of 20
   on the quieter machine), so the "medians pass, tails fail on a shared VM"
   reading now has a contrast case.
8. **Documentation inconsistency.** The Deep README said frame-and-VAD had
   100 samples per case; experiments/runs/2026-11-05-deep-muse-vm.json records n = 99 (3 batches of 33).
   Corrected in Stage 3 below.

#### Remaining, with the exact compute or data each needs

1. **Construct validity: no real ASR, TTS or LLM.** Needs a real speech
   workload and models behind the existing stage interfaces: a recorded,
   licensed set of spoken utterances with transcripts (for example 50 to 100
   short commands), a CPU speech recognizer and its weights (a small
   Whisper-family model, on the order of 100 MB), a local TTS voice, and a
   small local LLM. This is a new study (ROADMAP v1.1 items 2, 3 and 8), it
   breaks the standard-library-only rule, and the LLM step needs the GPU
   node, so it is out of scope for a fix.
2. **Measured cloud baseline.** Needs accounts on hosted ASR, LLM and TTS
   services and paid or metered API calls (ROADMAP v1.1 item 4). Excluded
   by the no-paid-API rule. The five constants stay labelled modelled.
3. **Confidence intervals on the shipped Deep run.** Raw per-call samples
   were not saved, so intervals cannot be computed after the fact. Needs one
   rerun of run_deep.py with raw-sample output, which would replace the
   committed experiments/runs/2026-11-05-deep-muse-vm.json; that is an Owner decision, not a silent fix.
   The probe file gives run-level intervals in the meantime.
4. **Quiet-machine tail budget.** Needs a dedicated, otherwise idle machine
   and a p99 budget written before measuring (ROADMAP v1.1 item 6).
5. **Claim-check gate records.** The Jev claim_check results cited in the
   level READMEs live in a workspace outside this repo. Needs those spec and
   result JSON files committed (they are named in each README); the gate
   itself is a paid call and NOVELTY.md stays PROPOSED until it passes.
6. **Concurrency, device path, larger workloads.** ROADMAP v1.1 items 5, 7
   and 9: need multi-session load generation, microphone and speaker
   hardware timing, and recorded long-form workloads.

### Strengths worth keeping

- Scope statements are honest and repeated where readers look.
- Budgets were set before measurement; medians are labelled as medians.
- Hand checks in every README are arithmetic a reader can redo.
- Build results are byte-identical across runs and the site build verifies
  the published hash.
- CI runs every level on two Python versions.

## v1.1 backlog (formerly ROADMAP.md: the rest of the v2 Deep scope)

Shipped: v1.0 (2026-11-05). Learn v0.1, Build v0.5, Deep v1.0
under ROADMAP-V3-BATCH and the December Compression Protocol.
Deep as shipped is the compressed Deep: the single hardest
capability in SPEC.md, the latency budget study, built,
tested, and benchmarked in level-3-deep.


Named here at Deep ship time, per the compression protocol.
None of this is claimed as done:

1. Streaming synthesis: synthesize and play frame by frame,
   and measure time to first frame separately from total
   synthesis time, so response-start latency stops carrying
   the whole response cost.
2. Real local ASR swap-in: a real recognizer behind the same
   streaming stage interface, with its latency and word error
   rate measured on real audio, replacing transcript partials.
3. Real local TTS swap-in: a real voice behind the same
   synthesis stage interface, with synthesis latency measured
   the same way, replacing the tone loop.
4. Measured cloud comparison: where a free tier allows it,
   measure a real cloud speech pipeline with the same stage
   split, replacing the modelled constants of v1.0. Modelled
   numbers are never relabelled as measurements.
5. Concurrency and load: many simultaneous sessions, with
   per-stage latency under load and a stated saturation point.
6. Tail-latency budget: a p99 budget next to the median
   budget, measured on a quiet machine, with the shared-VM
   spike behaviour of v1.0 as the baseline problem.
7. Device path: microphone capture and speaker playback
   timing, including device and driver latency, which v1.0
   excludes entirely.
8. An LLM answer step behind the same answer stage
   interface, with first-token and full-answer latency
   measured locally, replacing the keyword rule timing.
9. Larger and real workloads: recorded speech workloads and
   longer responses, beyond the 20 authored turns and 3
   barge-in scenarios of v1.0.

### Standing rules for any v1.1 work

- Measured and modelled numbers stay separate and labelled.
- results files that contain timings are never claimed
  byte-identical; deterministic files must be.
- No level ships on a claim: code, tests, numbers, links.

## Conclusion

The loop runs end to end and its plumbing is measured honestly: in this
stand-in, synthesizing the reply is the largest local cost and the text
stages cost microseconds, on both machines measured. That finding is a
property of a sine-tone synthesizer and a keyword rule, not of a real
speech stack, and the local-against-cloud half of the question is still
unanswered because the cloud side was never measured. The keyword rule
does not generalise (9 of 20 held-out paraphrases). The next step that
would move the verdict is a locked proposal for a confirmatory run with
a real recognizer, voice and model behind the same stage interfaces
(v1.1 items 2, 3, 4 and 8), which needs the Owner's call on models,
hardware and any paid service.
