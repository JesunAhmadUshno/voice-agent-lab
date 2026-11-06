# DEEP-SPEC: voice-agent-lab Level 3 (Deep)

Status: written before the Deep code, 2026-11-05.
Scope source: SPEC.md project section text: Deep is a latency
budget study (where every millisecond goes, local against cloud
speech models). Deep closes when the Deep scope in the section
text is done, the failure modes are written, and the dossier is
updated to ship state.

Compressed Deep (December Compression Protocol): the single
hardest capability in the SPEC is the latency budget study. It is
built, tested, and benchmarked here. The rest of the v2 Deep
scope goes to ROADMAP.md at the repo root as the named v1.1
backlog.

## What Deep adds over Build

Build proved the loop runs end to end and reported audio
duration from sample counts. Duration is content length, not
system latency. Deep measures the system latency of every stage
that actually runs locally, stage by stage, and puts a modelled
cloud pipeline next to it:

1. Frame and VAD split: splitting a response WAV sample list
   into 20 ms frames and classifying each frame speech or
   silence by the Build RMS rule.
2. Streaming partial intent tracing: replaying a transcript as
   cumulative word partials and classifying every partial with
   the Learn classifier (the Build streaming trace).
3. Intent and answer: the Learn intent classifier plus the
   template answer over the fixed teaching knowledge base.
4. WAV synthesis: the Build tone synthesis of the response
   (samples, WAV packing, framing, and its internal VAD count).
5. Barge-in handling, two shapes: the drop path (interrupt with
   stop on a playing session, setup untimed, only the interrupt
   call timed) and the full path (interrupt with a new question,
   which drops the unplayed frames and runs a whole new turn).

## Measurement method (binding)

- Local stages are measured, never estimated: each call is timed
  individually with time.perf_counter_ns, after 3 untimed warmup
  calls, in 3 repeated batches whose per-call samples are pooled.
  Sample counts per case: intent and answer 300, streaming 300,
  frame and VAD 100, WAV synthesis 30, barge-in drop 60, barge-in
  full 20. Per stage and case the runner reports n, mean, median,
  p90, p99, min, and max in microseconds, rounded to 3 decimals.
  Percentiles are nearest-rank.
- results_deep.json therefore contains measured wall-clock
  values and is NOT byte-identical across runs. That is stated
  here, in the runner, and in the level README, and no
  byte-identical claim is made for it. The deterministic fields
  (intents, responses, frame counts, drops, audio sizes, and all
  modelled totals) must be identical across runs, and the runner
  gates its exit code on them.
- The machine is named in every result: Muse VM, CPU, Python
  version recorded by the runner label. BlackBox is the assigned
  fleet node, but this study has no GPU step: every stage is
  CPU code from Learn and Build. No GPU result is claimed.

## Budget (set here, before measuring)

A conversational agent should start its reply within about
300 ms of the user finishing. This study allocates 100 ms of
that to local compute for one turn: the sum of the four
per-turn stage medians (frame and VAD, streaming, intent and
answer, WAV synthesis). Design shares of the 100 ms: WAV
synthesis 70 ms, frame and VAD 10 ms, streaming 10 ms, intent
and answer 5 ms, headroom 5 ms. Barge-in drop handling gets
its own 5 ms budget for the interrupt call median, because a
slow drop is heard as the agent talking over the user.

The budget is a reported study result per case. The runner exit
gate uses the deterministic correctness fields plus a hard
ceiling of 500 ms on any case total median, because shared CI
machines vary and a budget miss is a finding, not a crash. Both
numbers are named wherever the budget result is reported.

## The cloud side is modelled only

No cloud speech service is called, no network is used, and no
cloud latency is measured. The cloud pipeline is a model built
from stated constants, labelled modelled in every file:

- network round trip: 80 ms (stated constant)
- cloud ASR final transcript: 300 ms (stated constant)
- cloud LLM answer: 700 ms (stated constant)
- cloud TTS to first audio: 100 ms plus 5 ms per response word
  (stated formula)

Modelled total for a case: 1180 plus 5 times the response word
count, in milliseconds. Hand check: a 1-word response models to
1185 ms; a 5-word response models to 1205 ms. These constants
are illustrative modelling choices for this study, not sourced
measurements of any real service, and no real service is named
as measured anywhere.

## Substitutions, named again at Deep

Deep inherits the Build substitutions and adds none of its own:

- No real ASR model: speech in is still transcript partials and
  the one deterministic simulated noise map from Build. The
  latency of real recognition is not measured locally; on the
  cloud side it appears only as a modelled constant.
- No real TTS voice: speech out is still the Build tone
  synthesis. Its synthesis time is really measured here, but it
  is the cost of a sine loop, not of a speech model, and no
  voice quality is claimed.
- No LLM: the answer step is still the Learn rule intent and
  fixed teaching knowledge base, reused by import. Its measured
  microseconds are the cost of a keyword rule, not of model
  inference; the cloud LLM figure is modelled only.

## Acceptance

- Full test suite passes locally (Learn, Build, Deep tests, and
  the scaffold smoke test).
- Runner exits 0: all 20 single turns match expected intent and
  exact response, all deterministic audio and streaming fields
  match the Build results for the same cases, the 3 barge-in
  scenarios drop the expected frame counts, and no case total
  median exceeds the 500 ms hard ceiling.
- The budget table (per case and per stage, measured local
  medians and percentiles, modelled cloud totals) and the
  failure modes section are in the level README.
- No em dash character in any touched file.
- Every measured number in the README comes from the committed
  results_deep.json of the shipped run, and every modelled
  number is labelled modelled.
