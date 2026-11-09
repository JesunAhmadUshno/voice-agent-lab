# Changelog

All notable changes to this project. Format: Keep a Changelog 1.1.
Versions follow Semantic Versioning. The tags v0.1, v0.5 and v1.0 were
cut under the retired Learn / Build / Deep ladder; they stay as history
and are not a v1.0 Released verdict under the portfolio standard v2.

## [Unreleased]

### Changed
- 2026-11-08: Adopted the portfolio standard v2. README opens with the
  question, headline (with its interval), field, job family and verdict
  (Functional, not pre-registered). PROPOSAL.md gathers SPEC.md,
  NOVELTY.md, DOSSIER.md and the Build and Deep designs, marked not
  locked; REPORT.md gathers the three level READMEs,
  docs/research-review.md, ROADMAP.md and the legacy docs/index.md
  summary, and adds a claims table with the misses. Code moved to src/,
  case sets to experiments/cases/, recorded timed runs to
  experiments/runs/ (dated, content unchanged), Build results to
  results/build.json (byte-identical). Timed runners now write a new
  dated file and refuse to overwrite evidence. Grades and rubric scores
  left the public repo (grades are internal), including the dashboard's
  grades panel. PUBLICITY.md moved to docs/publicity.md. CI gains
  "permissions: contents read", a step that regenerates the Build
  results and fails on any byte change, and tests/test_layout.py
  (required files, no public grade, README headline equals the evidence
  file). CodeQL also scans the site's JavaScript; Dependabot watches the
  site's npm packages. main is protected and merges are squash only.

### Added
- 2026-11-08: docs/decisions/0001 (not pre-registered: why no commit can
  be the lock) and 0002 (stand-in components, and the verdict that
  follows).
- 2026-11-07: Add-on probes (5 repeated runs with 95% t intervals, time
  to first word, 20 held-out paraphrases), the live dashboard with a
  JavaScript port and a build-time parity check, the Pages workflow, and
  the research review.

## [1.0] - 2026-11-05

Deep shipped (formerly DOSSIER.md, shipped state v1.0). A latency budget
study of the Build pipeline: every local stage timed individually with
time.perf_counter_ns on the Muse VM (pooled per-call samples, medians
and nearest-rank percentiles). WAV synthesis is the dominant stage in 20
of 20 cases (median of medians 6109.360 microseconds, about 89 percent
of the mean total); frame and VAD split is second (752.122); streaming
tracing (16.099) and intent plus answer (2.955) are negligible. Median
case total 7255.203 microseconds, max case median 41688.082, 20 of 20
within the 100 ms local budget on medians; tails on the shared VM spike
far above the medians (WAV p99 up to 169298.914 microseconds) and are
written as a failure mode. Barge-in drop medians are at most 75.864
microseconds with 165 frames dropped in total. The cloud side is
modelled only, from stated constants (network 80 ms, ASR final 300 ms,
LLM answer 700 ms, TTS 100 ms plus 5 ms per word; mean modelled total
1212.75 ms, 29.865 to 1010.23 times the measured local totals), never
measured. 70 unit tests plus smoke. Full budget table, failure modes,
and the Jev gate record are in REPORT.md, Stage 3.

## [0.5] - 2026-11-05

Build shipped (formerly DOSSIER.md, shipped state v0.5). An end-to-end
voice loop: streaming transcript partials in, the Learn rule answer
reused by import with dialogue state on top, and tone-synthesized WAV
out (real WAV data at 8000 Hz, no intelligible speech): 20 of 20
single-turn intents and exact responses, 13 of 13 dialogue turns,
intent 16 of 20 through a deterministic simulated ASR noise map (mean
WER 0.0826), 323440 WAV bytes over 1008 frames of 20 ms, 3 barge-in
scenarios dropping 165 frames, 53 unit tests plus smoke. Substitutions
named: no ASR model, no TTS voice, no LLM. Full record in REPORT.md,
Stage 2.

## [0.1] - 2026-11-05

Learn shipped (formerly DOSSIER.md, shipped state v0.1). A simulated
voice agent loop (text transcripts standing in for ASR output,
deterministic keyword intent and template answers over a fixed teaching
knowledge base, text responses standing in for TTS output in simulated
frames of 3 words), a barge-in state machine (IDLE, LISTENING, THINKING,
SPEAKING), and a measured per-stage latency budget: 12 of 12 intents and
exact responses, mean total stage latency 4.835 microseconds and max
6.095 microseconds against a 5000 microsecond budget, 2 barge-in
scenarios dropping 5 frames in total, 30 unit tests plus smoke. All of
it ran on the Muse VM CPU. Named gaps that remained: no real ASR or TTS
model, no real audio, no LLM answer step, no GPU run (BlackBox
unreachable, NEEDS-BLACKBOX-ON), and Build and Deep not started. Full
method, tables, failure modes, and the Jev gate record are in REPORT.md,
Stage 1.

## Scaffold - 2026-11-04

- Scope (SPEC.md), dossier v1, novelty draft and level folders
  (cdf3a35), before any code.
