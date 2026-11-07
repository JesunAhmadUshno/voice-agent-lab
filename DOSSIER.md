# DOSSIER: voice-agent-lab (P18) v1, 2026-11-04

Written under the documentation and publishing standard (past, present, future). Updated at ship time.

## Past

Prior art for this project is named in NOVELTY.md (voice agent platforms and the SonicClear seed product). The history of the problem, the key papers and systems, and what was tried before are recorded in the Roadmap v2 section text in SPEC.md and will be expanded with dated sources at the project's wave, before Build opens.

A short, verifiable reference list (turn-taking timing, telephony delay guidance, ASR and VAD baselines, edit distance) is in docs/research-review.md, Related work, added 2026-11-07.

## Present

Current demand evidence: hiring value 3 of 5 (xAI Multimodal and Mistral audio only) [confirmed, fleet and scoring pass 2026-11-04; for P23 to P29, the decision pack 2026-11-04]. The Round 3 research (2026-11-04) found the market centre at post-training, evals, environments, and inference depth [confirmed as the research finding; the report is at ~/workspace/research_notes/roadmap-v3-revaluation-research-20261104-0949/report.md]. Tools and versions are pinned at Build time, not in this v1.

Shipped state (2026-11-05, v0.1): Learn is DONE. A simulated
voice agent loop (text transcripts standing in for ASR output,
deterministic keyword intent and template answers over a fixed
teaching knowledge base, text responses standing in for TTS
output in simulated frames of 3 words), a barge-in state machine
(IDLE, LISTENING, THINKING, SPEAKING), and a measured per-stage
latency budget: 12 of 12 intents and exact responses, mean total
stage latency 4.835 microseconds and max 6.095 microseconds
against a 5000 microsecond budget, 2 barge-in scenarios dropping
5 frames in total, 30 unit tests plus smoke (grade 8,500 of
10,000). All of it ran on the Muse VM CPU. Named gaps that
remain: no real ASR or TTS model, no real audio, no LLM answer
step, no GPU run (BlackBox unreachable, NEEDS-BLACKBOX-ON), and
Build and Deep are not started. Full method, tables, failure
modes, and the Jev gate record are in level-1-learn/README.md.

Shipped state (2026-11-05, v0.5): Build is DONE. An end-to-end
voice loop: streaming transcript partials in, the Learn rule
answer reused by import with dialogue state on top, and
tone-synthesized WAV out (real WAV data at 8000 Hz, no
intelligible speech): 20 of 20 single-turn intents and exact
responses, 13 of 13 dialogue turns, intent 16 of 20 through a
deterministic simulated ASR noise map (mean WER 0.0826), 323440
WAV bytes over 1008 frames of 20 ms, 3 barge-in scenarios
dropping 165 frames, 53 unit tests plus smoke (grade 7,500 of
10,000). Substitutions named: no ASR model, no TTS voice, no
LLM. Full record in level-2-build/README.md.

Shipped state (2026-11-05, v1.0): Deep is DONE, and v1.0 is
the ship state of the project. A latency budget study of the
Build pipeline: every local stage timed individually with
time.perf_counter_ns on the Muse VM (pooled per-call samples,
medians and nearest-rank percentiles). WAV synthesis is the
dominant stage in 20 of 20 cases (median of medians 6109.360
microseconds, about 89 percent of the mean total); frame and
VAD split is second (752.122); streaming tracing (16.099) and
intent plus answer (2.955) are negligible. Median case total
7255.203 microseconds, max case median 41688.082, 20 of 20
within the 100 ms local budget on medians; tails on the
shared VM spike far above the medians (WAV p99 up to
169298.914 microseconds) and are written as a failure mode.
Barge-in drop medians are at most 75.864 microseconds with
165 frames dropped in total. The cloud side is modelled only,
from stated constants (network 80 ms, ASR final 300 ms, LLM
answer 700 ms, TTS 100 ms plus 5 ms per word; mean modelled
total 1212.75 ms, 29.865 to 1010.23 times the measured local
totals), never measured. 70 unit tests plus smoke (grade
7,700 of 10,000). Full budget table, failure modes, and the
Jev gate record are in level-3-deep/README.md.

## Future

The rest of the v2 Deep scope is the v1.1 backlog in
ROADMAP.md at the repo root: streaming synthesis with
time-to-first-frame measurement, real local ASR and TTS
swap-ins behind the same stage interface, a measured (not
modelled) cloud comparison where a free tier allows it,
concurrent sessions, a tail-latency budget on a quiet
machine, a device path, an LLM answer step, and larger real
workloads. Any forecast about this field is [unverified]
unless a dated primary source is added here.
