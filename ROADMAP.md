# ROADMAP: voice-agent-lab (P18)

Shipped: v1.0 (2026-11-05). Learn v0.1, Build v0.5, Deep v1.0
under ROADMAP-V3-BATCH and the December Compression Protocol.
Deep as shipped is the compressed Deep: the single hardest
capability in SPEC.md, the latency budget study, built,
tested, and benchmarked in level-3-deep.

## v1.1 backlog (the rest of the v2 Deep scope)

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

## Standing rules for any v1.1 work

- Measured and modelled numbers stay separate and labelled.
- results files that contain timings are never claimed
  byte-identical; deterministic files must be.
- No level ships on a claim: code, tests, numbers, links.
