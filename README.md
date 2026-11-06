# voice-agent-lab

Real-time voice agents: speech in, LLM answer, speech out, a latency budget study.

Status: Learn DONE, Build DONE, and Deep DONE (2026-11-05, ROADMAP-V3-BATCH). v1.0 shipped.
Project: P18. Fleet node: BlackBox (GPU). Wave: Wave 7. Learn ran on the Muse VM (CPU) with BlackBox unreachable. Build and Deep also ran on the Muse VM (CPU): neither scope has a GPU step. See the level READMEs for the named deductions.

## Start here

1. Read SPEC.md for scope and acceptance criteria.
2. Read DOSSIER.md for the past, present, and future of this problem (v1).
3. Read NOVELTY.md for the proposed novelty (DRAFT, pending the Jev claim_check gate).
4. Start at level-1-learn/README.md, then level-2-build, then level-3-deep.

## Level map

- Level 1, Learn: the core idea, built small and clean, with a teaching path. DONE.
- Level 2, Build: a real working system other people can run. DONE.
- Level 3, Deep: benchmarks, optimization, evaluation, hard cases. DONE.

## Benchmarks

### Learn (Level 1)

Measured 2026-11-05 with level-1-learn/run_learn.py on the Muse VM (CPU, Python 3.12.3, standard library only). The loop is simulated: text transcripts stand in for ASR output and text responses stand in for TTS output, with simulated frames of 3 words. No real ASR or TTS model ran. Latency is the measured wall-clock mean per stage (time.perf_counter_ns, 5 batches of 2000 calls, median batch mean), and the budget is 5000 microseconds for the sum of the four text-stage means of one case. Full per-case table, barge-in scenarios, failure modes, and grade (8,500 of 10,000) are in level-1-learn/README.md.

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

Measured 2026-11-05 with level-2-build/run_build.py on the Muse VM (CPU, Python 3.12.3, standard library only). The loop runs end to end: streaming transcript partials in, the Learn rule answer reused by import with dialogue state on top (weather follow-ups, timer slot filling, repeat), and tone-synthesized WAV out (real WAV data at 8000 Hz, no intelligible speech). No ASR model, no TTS model, and no LLM ran; the substitutions are named in level-2-build/BUILD-SPEC.md. The results file holds no wall-clock field and is byte-identical across runs. Full per-case tables, dialogue turns, noise runs, failure modes, and grade (7,500 of 10,000) are in level-2-build/README.md.

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

Measured 2026-11-05 with level-3-deep/run_deep.py on the Muse VM (CPU, Python 3.12.3, standard library only). A latency budget study: every stage that runs locally is timed individually with time.perf_counter_ns (pooled per-call samples over 3 batches, medians and nearest-rank percentiles), and a cloud pipeline built only from stated constants is modelled next to it (modelled only, never measured, no cloud service called). No ASR model, no TTS model, and no LLM ran; the substitutions are named again in level-3-deep/DEEP-SPEC.md. The results file contains measured timings and is not byte-identical across runs; its deterministic fields are identical across runs. The rest of the v2 Deep scope is the v1.1 backlog in ROADMAP.md. Full budget table, failure modes, and grade (7,700 of 10,000) are in level-3-deep/README.md.

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

## Novelty

PROPOSED. See NOVELTY.md. The novelty text is a draft until the Jev claim_check gate passes on it.

## License

Code: Apache-2.0 (see LICENSE). Tutorials: CC BY 4.0. Ruled in D-V3-11, 2026-11-04.
