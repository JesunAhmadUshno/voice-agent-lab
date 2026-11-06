# voice-agent-lab

Real-time voice agents: speech in, LLM answer, speech out, a latency budget study.

Status: Learn DONE (2026-11-05, ROADMAP-V3-BATCH). Build and Deep NOT STARTED.
Project: P18. Fleet node: BlackBox (GPU). Wave: Wave 7. Learn ran on the Muse VM (CPU); BlackBox was unreachable this cycle (NEEDS-BLACKBOX-ON). See the Learn README for the named deduction.

## Start here

1. Read SPEC.md for scope and acceptance criteria.
2. Read DOSSIER.md for the past, present, and future of this problem (v1).
3. Read NOVELTY.md for the proposed novelty (DRAFT, pending the Jev claim_check gate).
4. Start at level-1-learn/README.md, then level-2-build, then level-3-deep.

## Level map

- Level 1, Learn: the core idea, built small and clean, with a teaching path. DONE.
- Level 2, Build: a real working system other people can run. Not started.
- Level 3, Deep: benchmarks, optimization, evaluation, hard cases. Not started.

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

## Novelty

PROPOSED. See NOVELTY.md. The novelty text is a draft until the Jev claim_check gate passes on it.

## License

Code: Apache-2.0 (see LICENSE). Tutorials: CC BY 4.0. Ruled in D-V3-11, 2026-11-04.
