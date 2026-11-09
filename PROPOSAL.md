# Proposal: voice-agent-lab (P18)

Status: NOT LOCKED, not pre-registered. This file gathers the plan as it
was written: the scope (SPEC.md, committed 2026-11-04 in cdf3a35 before
any code), the novelty draft, the prior-work notes, and the Build and
Deep designs. Git history shows the Build and Deep designs were committed
in the same commits as their results (873fc4f and fd97883), and the
2026-11-04 scope has no hypotheses or pass lines, so no commit can serve
as a lock (docs/decisions/0001). A confirmatory cycle needs a new locked
proposal, tagged before its first run.

## Question

Where does every millisecond of a voice-agent turn go, stage by stage,
locally against a cloud speech pipeline? (The Deep scope in the section
text below: "a latency budget study (where every millisecond goes, local
against cloud speech models)".)

## Budgets and criteria written before measuring

These were set in the Deep and Build designs before each stage's runner
ran, but committed together with the results, so they are reported as
stated criteria, not as a locked pre-registration:

- Learn: 5000 microseconds for the sum of the four text-stage means of
  one case.
- Build: every single turn and every dialogue turn matches its expected
  intent and exact response; the noise runs are reported, not gated.
- Deep: 100 ms for the sum of the four per-turn stage medians (design
  shares: WAV synthesis 70 ms, frame and VAD 10 ms, streaming 10 ms,
  intent and answer 5 ms, headroom 5 ms); 5 ms for the barge-in drop
  median; a 500 ms hard ceiling on any case total median.

REPORT.md scores each of these, misses included.

## Scope (formerly SPEC.md, 2026-11-04)

Phase skill: spec-driven-development (house engineering pipeline).
Status: Wave 0 scaffold spec, from Roadmap v2 text and the v3 decision pack. Scope and acceptance criteria below are the v2 section text, kept as the source of truth until the project's wave opens its own spec pass.

Fleet node: BlackBox (GPU). Wave: Wave 7.
Hiring evidence: 3 of 5 (xAI Multimodal and Mistral audio only) [confirmed, fleet and scoring pass 2026-11-04, or the decision pack for P23 to P29].

### Project section text (Roadmap v2, or the v3 candidate text for P23 to P29)

voice-agent-lab: KEEP, scope narrowed to audio

Subject: real-time AI. v1 levels carry over: speech in, LLM answer, speech out, in one loop; streaming audio with interruption handling (barge-in); Deep is a latency budget study (where every millisecond goes, local against cloud speech models). Scope note (change 14): the vision-language items once tied to this project (register items 310, 311, 333) move to P22. The audio and media data step (register item 381) and the Build-level bar (item 865) stay here. Seed repo: SonicClear (Section 8).
Fan-out: Book chapter "A Voice With No Lag". Paper angle: the latency budget study. Course module: P18-voice-agent-lab.

### Acceptance criteria (scaffold level)

- Learn closes when the level-1-learn code runs, its README teaches the idea, and a fresh-eyes reader can follow it.
- Build closes when the system runs end to end, tests pass, and one benchmark or result table with method is in the README.
- Deep closes when the Deep scope in the section text is done, the failure modes are written, and the dossier is updated to ship state.
- No level closes on a claim. Evidence only: code, tests, numbers, links.

## Novelty (formerly NOVELTY.md, draft)

Status: DRAFT, PROPOSED. Not verified. This text does not move into any public post, paper, or profile until the Jev claim_check gate passes on the exact text.

### Proposed claim

Against voice agent platforms and the SonicClear seed product: this project aims to differ in the way its scope section text defines (a from-zero or self-hosted build, measured in public, on a named home fleet, with the failure modes written down). The exact difference is stated at the project's wave, after the prior art is re-read.

### Prior art table

| Prior art | What it does | What this project does differently | Measured difference |
| --- | --- | --- | --- |
| voice agent platforms and the SonicClear seed product | See Prior work below | PROPOSED, see the claim above | NO MEASUREMENT YET |

### Honest size

If the novelty proves small, this file will say so and name the real value instead (a cleaner reproduction, a better benchmark, a first public dataset). No novelty is invented to fill this section.

## Prior work (formerly DOSSIER.md, Past and Present)

Prior art for this project is named in the Novelty section above (voice agent platforms and the SonicClear seed product). The history of the problem, the key papers and systems, and what was tried before are recorded in the Roadmap v2 section text in the Scope section above and will be expanded with dated sources at the project's wave, before Build opens.

A short, verifiable reference list (turn-taking timing, telephony delay guidance, ASR and VAD baselines, edit distance) is in REPORT.md, Background (formerly docs/research-review.md, Related work, added 2026-11-07).

Current demand evidence: hiring value 3 of 5 (xAI Multimodal and Mistral audio only) [confirmed, fleet and scoring pass 2026-11-04; for P23 to P29, the decision pack 2026-11-04]. The Round 3 research (2026-11-04) found the market centre at post-training, evals, environments, and inference depth [confirmed as the research finding; the report is at ~/workspace/research_notes/roadmap-v3-revaluation-research-20261104-0949/report.md]. Tools and versions are pinned at Build time, not in this v1.

## Build design (formerly level-2-build/BUILD-SPEC.md)

Status: written before the Build code, 2026-11-05.
Scope source: the Scope section's project section text: speech in, LLM answer,
speech out, in one loop; streaming audio with interruption handling
(barge-in). Build closes when the system runs end to end, tests
pass, and one benchmark or result table with method is in the README.

### What Build adds over Learn

Learn was a single-turn simulated loop: text transcripts in, text
responses out in simulated word frames, a barge-in state machine,
and a text-stage latency budget. Build turns that into an end-to-end
system other people can run:

1. Real WAV audio out. Every response is synthesized into a real
   WAV byte stream (stdlib wave module, 8000 Hz, 16-bit mono) and
   measured: sample count, duration from sample count, byte size,
   and 20 ms frame count. Playback and barge-in run over those
   real audio frames, not over word groups.
2. Voice activity split. The WAV frames are split into speech and
   silence frames by a root-mean-square energy rule, counted per
   response.
3. Streaming intent. Transcripts arrive as cumulative word
   partials. The intent of every partial is classified with the
   Learn classifier, and the runner records the first partial that
   reaches the final intent.
4. Multi-turn dialogue. A DialogueSession reuses the Learn turn by
   import and adds conversation state: weather follow-ups that name
   only a new city, timer slot filling across two turns, and a
   repeat request that replays the last response.
5. ASR noise robustness. A deterministic simulated ASR step maps
   the word weather to whether and drops the word the. The same 20
   cases are scored clean and through that noise, with word error
   rate measured by a word-level edit distance.
6. A larger scored set: 20 single turns, 5 dialogues with 13 turns,
   the 20 noise runs, and 3 barge-in scenarios over audio frames.

### Substitutions, named before any code ran

Availability was checked on this VM on 2026-11-05 before this spec
was written:

- No ASR model is available: no whisper module, no
  speech_recognition module, no torch, no transformers, and no
  network install is attempted under FREE-ONLY. Speech in therefore
  stays a transcript, now delivered as streaming partials and
  through a named deterministic noise map. That is a simulation of
  ASR output and of one ASR error class, not ASR.
- No TTS voice is available: no espeak, espeak-ng, flite, or
  festival binary, and no pyttsx3 or gTTS module. Speech out is
  therefore a deterministic tone synthesis: each word becomes a
  120 ms sine segment at a word-derived frequency, separated by
  40 ms of silence. The output is a real WAV file with real
  duration and energy, but it carries no intelligible speech and
  no voice quality claim is made anywhere.
- No LLM is available on this VM. The answer step stays the Learn
  deterministic intent rule and template knowledge base, reused by
  import. SPEC names an LLM answer; that step is a named
  substitution at Build and stays open.
- Fleet node: BlackBox is the assigned GPU node and was ON this
  cycle (coordinator verified SSH and the RTX 5050). This Build
  scope is CPU teaching work with no GPU step in it, so the run
  executes on the Muse VM CPU, and the fleet-node gap is named as a
  limit, as in prior cycles. No GPU result is
  claimed and NEEDS-BLACKBOX-ON does not apply: the node is on,
  the work simply has no GPU part.

### Determinism rule

results/build.json holds no wall-clock field at all. Every number
in it is a count, a sample count, a duration derived from a sample
count (samples divided by 8000 Hz), a byte size, or a score over
labelled cases. The file must be byte-identical across two runs;
the runner is run twice and the hashes compared before shipping.

### Acceptance

- Full test suite passes locally (Learn tests, Build tests, smoke).
- Runner exits 0: all 20 single turns and all 13 dialogue turns
  match their expected intent and exact response, and the 3
  barge-in scenarios complete. The noise runs are reported, not
  gated: their degradation is a measured result, not a pass mark.
- No em dash character in any touched file.
- Every measured number in the README comes from the committed
  results/build.json of the shipped run.

## Deep design (formerly level-3-deep/DEEP-SPEC.md)

Status: written before the Deep code, 2026-11-05.
Scope source: the Scope section's project section text: Deep is a latency
budget study (where every millisecond goes, local against cloud
speech models). Deep closes when the Deep scope in the section
text is done, the failure modes are written, and the dossier is
updated to ship state.

Compressed Deep (December Compression Protocol): the single
hardest capability in the scope is the latency budget study. It is
built, tested, and benchmarked here. The rest of the v2 Deep
scope goes to the v1.1 backlog in REPORT.md as the named v1.1
backlog.

### What Deep adds over Build

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

### Measurement method (binding)

- Local stages are measured, never estimated: each call is timed
  individually with time.perf_counter_ns, after 3 untimed warmup
  calls, in 3 repeated batches whose per-call samples are pooled.
  Sample counts per case: intent and answer 300, streaming 300,
  frame and VAD 100, WAV synthesis 30, barge-in drop 60, barge-in
  full 20. Per stage and case the runner reports n, mean, median,
  p90, p99, min, and max in microseconds, rounded to 3 decimals.
  Percentiles are nearest-rank.
- experiments/runs/2026-11-05-deep-muse-vm.json therefore contains measured wall-clock
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

### Budget (set here, before measuring)

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

### The cloud side is modelled only

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

### Substitutions, named again at Deep

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

### Acceptance

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
  experiments/runs/2026-11-05-deep-muse-vm.json of the shipped run, and every modelled
  number is labelled modelled.

## Future (formerly DOSSIER.md, Future)

The rest of the v2 Deep scope is the v1.1 backlog in
the v1.1 backlog in REPORT.md: streaming synthesis with
time-to-first-frame measurement, real local ASR and TTS
swap-ins behind the same stage interface, a measured (not
modelled) cloud comparison where a free tier allows it,
concurrent sessions, a tail-latency budget on a quiet
machine, a device path, an LLM answer step, and larger real
workloads. Any forecast about this field is [unverified]
unless a dated primary source is added here.
