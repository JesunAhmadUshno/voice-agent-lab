# Release notes: voice-agent-lab (P18)

One section per release line. Every number below comes from the
level README of that release and the release text on GitHub,
verified with gh release list on 2026-11-05. There is no real
ASR model, no real TTS voice, and no LLM in any release, and the
Deep cloud side is modelled from stated constants, never
measured. The full release text lives on the GitHub releases
page:
https://github.com/JesunAhmadUshno/voice-agent-lab/releases

## v0.1, Learn (2026-11-05)

- What shipped: a simulated voice agent loop (text transcripts
  in, text responses out in simulated frames of 3 words), a
  deterministic keyword intent rule over a fixed teaching
  knowledge base, a four-state barge-in machine, and a measured
  per-stage latency budget, plus 30 unit tests and the scaffold
  smoke test.
- Measured result: 12 labelled cases, intent 12 of 12, exact
  response 12 of 12, total stage latency mean 4.835 microseconds
  and max 6.095 microseconds against a 5000 microsecond budget,
  2 barge-in scenarios dropping 5 unplayed frames in total.
- Release: https://github.com/JesunAhmadUshno/voice-agent-lab/releases/tag/v0.1

## v0.5, Build (2026-11-05)

- What shipped: the end-to-end voice loop: streaming transcript
  partials in, the Learn rule answer reused by import with
  dialogue state on top, tone-synthesized WAV out at 8000 Hz,
  a deterministic simulated ASR noise run, and barge-in over
  real audio frames, plus 23 new tests (53 unit tests in total
  with Learn).
- Measured result: single intent and response 20 of 20,
  dialogue intent and response 13 of 13 turns in 5 dialogues,
  intent 16 of 20 through simulated ASR noise (mean WER 0.0826,
  all 4 failures on weather cases), 323440 WAV bytes (20160.0
  ms, 1008 frames of 20 ms), 3 barge-in scenarios dropping 165
  unplayed frames in total.
- Release: https://github.com/JesunAhmadUshno/voice-agent-lab/releases/tag/v0.5

## v1.0, Learn, Build, and Deep (2026-11-05)

- What shipped: the latency budget study on top of Learn and
  Build, plus 17 new tests (70 unit tests in total, plus the
  scaffold smoke test). The rest of the v2 scope is named in
  REPORT.md (v1.1 backlog) as the v1.1 backlog.
- Measured and modelled result: WAV synthesis dominant in 20 of
  20 cases, total local latency median case 7255.203
  microseconds and max case median 41688.082 microseconds, 20
  of 20 within the 100 ms local budget on medians, barge-in
  drop path median at most 75.864 microseconds with 165 frames
  dropped in total; modelled cloud total mean 1212.75 ms per
  case (29.865 to 1010.23 times the local totals), from stated
  constants only. Cloud quality and latency not measured.
- Release: https://github.com/JesunAhmadUshno/voice-agent-lab/releases/tag/v1.0

## Held channels

- Social posts for every release above: HELD under the standing
  platform rules. The loop prepares drafts and never posts;
  Threads needs Jesun's one tap per post.
- The v1.1 backlog lives in REPORT.md (v1.1 backlog): streaming synthesis, a
  real local ASR and TTS swap-in, a measured cloud comparison,
  concurrency, a tail-latency budget, a device path, an LLM
  answer step, and larger real workloads.
