# Level 3, Deep: voice-agent-lab

Status: DONE (2026-11-05). A latency budget study of the Build
voice pipeline: where every millisecond goes, stage by stage,
measured locally, with a modelled cloud pipeline next to it.
Built with the Python standard library only, reusing the Learn
and Build code by import. The Deep spec, written before the
code, is DEEP-SPEC.md in this folder.

## Honest scope line

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
Build, so no GPU was used and the grade carries the named
fleet-node deduction.

## Method

1. Workloads. The 20 Build single turns (cases_deep.json, the
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
4. Budget. Set in DEEP-SPEC.md before measuring: 100 ms for
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

The runner writes level-3-deep/results_deep.json (sha256
4aba845adb148f94 for the shipped run). Its latency fields are
measured wall-clock values and vary between runs, so the file
is NOT byte-identical across runs, and no such claim is made.
Its deterministic fields (intents, responses, frame counts,
drops, audio sizes, modelled totals) were verified identical
across two runs of the shipped code.

## Results (measured 2026-11-05, Muse VM, Python 3.12.3)

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
of the 20 per-case modelled totals in results_deep.json
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

## Add-on probes (results_probes.json)

level-3-deep/run_probes.py adds three cheap probes without
touching results_deep.json: the stage timings re-measured 5
times (between-run spread on one machine), sine-loop synthesis
time for the first word against the whole response (ROADMAP
v1.1 item 1, for the tone loop only), and the frozen keyword
rule scored on 20 held-out paraphrases (cases_paraphrase.json).
They ran on a different machine from the shipped Deep run (the
machine is recorded in the file), so their absolute timings are
not comparable with the Muse VM numbers above; the stage
ordering and the paraphrase score are what carry over.

## Run it

    python level-3-deep/run_deep.py
    python level-3-deep/run_probes.py
    python -m unittest tests.test_deep_voice_agent -v
    python -m unittest discover -s tests -v
    python tests/test_smoke.py

## Failure modes and limits

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

## Grade

Grade: 7,700 of 10,000 for this Deep level.

Deductions (they sum to 2,300):
- No real ASR model: recognition, the largest real stage, is
  absent locally and only a modelled constant on the cloud
  side: minus 500.
- No real TTS voice: the dominant measured stage is a sine
  loop, not a speech model, so the headline number times the
  wrong thing honestly: minus 400.
- The cloud comparison is modelled from stated constants,
  not measured against a real service, by design: minus 400.
- No LLM answer step: the answer stage times a keyword rule,
  not inference: minus 300.
- Designed synthetic evaluation sets: 20 turns and 3
  barge-in scenarios, all authored for this project:
  minus 200.
- Run on the shared Muse VM (CPU), not the assigned
  BlackBox fleet node, with noisy tails: minus 200.
- Compressed Deep scope: streaming synthesis, concurrency,
  and device playback timing move to the v1.1 backlog in
  ROADMAP.md: minus 200.
- One session at a time and no persistence in the measured
  pipeline: minus 100.

## What remains (v1.1)

See ROADMAP.md at the repo root: streaming synthesis with
time-to-first-frame measurement, a real local ASR and TTS
swap-in behind the same stage interface, a measured (not
modelled) cloud comparison where a free tier allows it,
concurrent sessions, and a tail-latency budget on a quiet
machine.
