# Paper candidate brief: a latency budget study of a teaching voice pipeline

Project: P18 voice-agent-lab
Status: CANDIDATE, brief dated 2026-11-05
Submission note: submission is Jesun's tap. Nothing is submitted by
this brief, and no venue has been contacted.

## Working title

Budgeting the voice loop: measured local stage latencies of a
standard-library voice pipeline, with a modelled cloud pipeline
kept separate

## Candidate claim, in one line

On a small synthetic teaching pipeline, per-stage timing shows
the audio synthesis step dominating the local latency budget
while the text stages are negligible and interruption is cheap;
the claim is the stage-split method and the measured-versus-
modelled discipline, not production voice performance, because
there is no real ASR, TTS, or LLM in the pipeline and the cloud
side is modelled, not measured.

## Abstract draft

Based only on the measured v1.0 results recorded in the repo.
Scope limits are stated inside the abstract, not after it.

Real-time voice agents are usually reported as one end-to-end
latency number, which hides where the time goes. This candidate
reports a three level open study that times each stage of a
teaching voice pipeline separately. Learn built a simulated
loop over 12 labelled text cases and scored intent and exact
response 12 of 12, with mean total stage latency 4.835
microseconds against a 5000 microsecond budget and 5 unplayed
frames dropped across 2 barge-in scenarios. Build ran the loop
end to end (streaming transcript partials in, a keyword rule
answer with dialogue state, tone-synthesized WAV out) and
scored 20 of 20 single turns, 13 of 13 dialogue turns, and 16
of 20 under a deterministic simulated ASR noise map (mean WER
0.0826), synthesizing 323440 WAV bytes over 1008 frames and
dropping 165 frames across 3 barge-in scenarios. Deep timed
every local stage with per-call sampling: WAV synthesis was
dominant in 20 of 20 cases (median of medians 6109.360
microseconds, about 89 percent of the mean total), the median
total was 7255.203 microseconds, the maximum case median was
41688.082 microseconds, and 20 of 20 cases were within a 100 ms
budget on medians, while WAV p99 reached 169298.914
microseconds on a shared machine. A cloud pipeline built only
from stated constants (network 80 ms, ASR final 300 ms, LLM
answer 700 ms, TTS 100 ms plus 5 ms per word) modelled a mean
total of 1212.75 ms and was never measured. There is no real
ASR model, TTS voice, or LLM in the local pipeline, every case
set is synthetic and authored for this project, and the
measured synthesis stage is a sine loop, not a speech model.
The candidate claims the reproducible stage budget, the
barge-in drop timing, and the measured-versus-modelled
separation on these sets, not real-world voice agent latency.

## Method outline

1. Learn loop. Transcript normalization and framing by word
   groups, a fixed priority keyword intent rule, template
   answers over a fixed teaching knowledge base, a four-state
   barge-in machine, and per-stage timing with
   time.perf_counter_ns (5 batches of 2000 calls, median batch
   mean).
2. Build pipeline. Cumulative word partials with first-correct
   and stability tracking, dialogue state (one pending slot,
   remembered city and response), tone WAV synthesis (960
   samples per word plus 320 per gap, 8000 Hz, 20 ms frames,
   RMS speech threshold 100), a deterministic ASR noise map
   scored with word error rate, and barge-in over audio frames.
3. Deep study. Per-call timing of each stage after warmup, 3
   batches with pooled samples, medians and nearest-rank
   percentiles, a 100 ms median budget set before measuring,
   and a cloud total computed in code from stated constants.
4. Determinism. Build results are byte-identical across runs;
   Learn and Deep deterministic fields are identical across
   runs and only their timing fields vary.

## Results table

Measured 2026-11-05, Muse VM, Python 3.12.3, from the level
READMEs and results files in the repo.

| Item | Result |
| --- | --- |
| Learn | 12 cases, intent and response 12 of 12, mean total stage 4.835 us, 5 frames dropped |
| Build | 20 single 20 of 20, 13 dialogue 13 of 13, noise 16 of 20 (WER 0.0826), 323440 WAV bytes, 165 frames dropped |
| Deep local | WAV dominant 20 of 20, median total 7255.203 us, max median 41688.082 us, 20 of 20 within 100 ms on medians |
| Deep barge-in | Drop medians 10.121 to 75.864 us, 165 frames dropped in total |
| Deep cloud (modelled) | Mean 1212.75 ms per case, 29.865 to 1010.23 times the local totals, never measured |
| Tests | 70 in total, plus the scaffold smoke test |

## Limits a reviewer will raise, stated first

- No real ASR, TTS, or LLM: the largest real stage is absent
  and the dominant measured stage times a sine loop.
- Cloud side modelled from illustrative constants, not
  measured against any real service.
- Synthetic authored sets: 20 turns and 3 barge-in scenarios
  in Deep, all written for this project.
- Median budget only: tails on the shared VM breach the
  budget, and a p99 budget would fail on this machine.
- Synthesis before playback inflates response-start latency
  by design of the teaching pipeline.
- Single site: Muse VM on CPU, not the assigned fleet node.

## What would strengthen the candidate

Each item is v1.1 backlog in ROADMAP.md, not done work:
streaming synthesis with time-to-first-frame measurement, real
local ASR and TTS swap-ins behind the same stage interface, a
measured cloud comparison where a free tier allows it,
concurrent sessions, and a tail-latency budget on a quiet
machine.

## Venue note

No venue is named as submitted or contacted. Venue choice and
any submission click are Jesun's tap only.
