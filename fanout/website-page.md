# Website project page copy: voice-agent-lab

Site: jesunahmadushno.com
Status: COPY ONLY, draft for the project page. Dated 2026-11-05.
Nothing on any website was changed by this file.

## Headline

voice-agent-lab: a voice agent latency budget study, local stages measured, cloud stages modelled, and the two never mixed

## Summary

voice-agent-lab is an open real-time voice agent study built by
Jesun Ahmad Ushno as project P18 in Roadmap v3. It builds the
voice loop three times: a simulated loop with a barge-in state
machine, an end-to-end loop with streaming transcript partials,
dialogue state, tone WAV out and barge-in over audio frames, and
a latency budget study that times every local stage and models
a cloud pipeline from stated constants next to it. It runs on
the Python standard library only.

Two scope facts, stated plainly. There is no real ASR model, no
real TTS voice, and no LLM in any level: speech in is
transcripts, speech out is text or tone WAV with no intelligible
speech, and answers come from a keyword rule over a fixed
teaching knowledge base. The cloud side is modelled only, never
measured.

Status: v1.0, 2026-11-05. Learn, Build, and Deep are done.
Grades on the house 10,000 scale: Learn 8,500, Build 7,500,
Deep 7,700. Total tests: 70, plus the scaffold smoke test.

## Results

| Level | Set | Key result | Notes |
| --- | --- | --- | --- |
| Learn | 12 text cases, 2 barge-in scenarios | Intent 12 of 12, response 12 of 12, mean total stage latency 4.835 microseconds, 5 frames dropped | Simulated audio only; 30 tests |
| Build | 20 single turns, 13 dialogue turns, 3 barge-in scenarios | Single 20 of 20, dialogue 13 of 13, noise intent 16 of 20 (mean WER 0.0826), 323440 WAV bytes, 165 frames dropped | Tone WAV, no intelligible speech; 53 tests in total |
| Deep | 20 turns plus 3 barge-in scenarios | WAV synthesis dominant 20 of 20, median total 7255.203 microseconds, max median 41688.082, 20 of 20 within the 100 ms budget on medians; modelled cloud mean 1212.75 ms | Cloud modelled only, not measured; 70 tests in total |

The perfect intent and response scores are weak evidence: every
set is synthetic and authored for this project.

## Honest limits

- No real ASR, no real TTS voice, no LLM, no microphone, no
  speaker device, and no network transport.
- Cloud quality, cost, and latency not measured; the cloud
  pipeline is stated constants only.
- Synthesis before playback, so response-start latency carries
  the full synthesis time.
- Median budget verdict only; p90 and p99 tails on the shared
  VM spike far above the medians.
- Run on the Muse VM (CPU), not the assigned BlackBox node.

## Links

- GitHub repo: https://github.com/JesunAhmadUshno/voice-agent-lab
- Release v0.1 (Learn): https://github.com/JesunAhmadUshno/voice-agent-lab/releases/tag/v0.1
- Release v0.5 (Build): https://github.com/JesunAhmadUshno/voice-agent-lab/releases/tag/v0.5
- Release v1.0 (Learn, Build, Deep): https://github.com/JesunAhmadUshno/voice-agent-lab/releases/tag/v1.0
- Tutorial: fanout/tutorial.md in the GitHub repo
- Blog post draft: fanout/blog-post.md in the GitHub repo

## License note

Code: Apache-2.0. Tutorials: CC BY 4.0.
