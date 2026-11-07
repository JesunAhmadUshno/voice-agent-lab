# Research review: voice-agent-lab

Reviewed 2026-11-07 against a PhD-level research rubric. Scope: the three
levels as shipped (Learn, Build, Deep), the committed results files, and the
changes made on the site/live-dashboard branch. Every number below is quoted
from a committed file; the file is named next to it.

## Verdict

A careful methods and engineering exercise with an unusually honest scope, and
a weak empirical contribution. As a thesis chapter it would pass with major
revisions: the measurement discipline is sound, but the system being measured
is a stand-in for a voice agent (keyword rule, sine-tone synthesis, typed
transcripts), so the headline finding ("synthesis dominates the turn") is a
property of the stand-in, not of real speech stacks.

## Rubric

| Criterion | Grade | Evidence and reasoning |
| --- | --- | --- |
| Research question | Adequate | "Where does every millisecond of a voice turn go, local against cloud?" (SPEC.md). Clear and answerable, but answered for a substitute pipeline. |
| Hypotheses | Weak | The 100 ms budget and per-stage design shares were fixed in DEEP-SPEC.md before measuring (good), but no falsifiable hypothesis about stage ordering was written down in advance. |
| Method | Strong | Per-call `perf_counter_ns` timing after warmup, pooled over 3 batches, nearest-rank percentiles, untimed setup for stateful barge-in paths (level-3-deep/README.md, Method). Measured and modelled numbers are never mixed. |
| Baselines | Weak | The only comparison is a cloud pipeline built from five unsourced constants (80/300/700/100 ms + 5 ms per word, latency_lab.py). No measured baseline exists. |
| Statistics and uncertainty | Weak, partly fixed | One recorded run per level, medians only, no intervals; raw samples not saved. This change adds a 5-run repeat with spread and a 95% t interval (results_probes.json). |
| Reproducibility | Strong | Standard library only, CI on Python 3.11 and 3.12, Build results byte-identical (sha256 prefix ed5699dad566ac56, re-verified by the site build). Deep timings vary by design and say so. |
| Threats to validity | Strong on disclosure | Each level README lists failure modes and named grade deductions. The main threat (construct validity) is disclosed but not mitigated. |
| Related work | Missing, partly fixed | DOSSIER.md and NOVELTY.md had no citations. A short, verifiable reference list is added below. |
| Limitations | Strong | Stated in every README, the root README, and docs/index.md. |

## Gaps, and what this change did about each

### Fixed in this change (no GPU, no paid API, each run under a minute)

1. **In-browser numbers could drift from the repo.** The dashboard ports the
   Python rules to JavaScript; `site/src/voice.check.mjs` runs inside
   `npm run build` and replays all Learn cases, all Build single turns
   (intent, response, WAV bytes, frames, streaming trace), the 5 dialogues,
   the 20 noise runs (WER to 4 dp), the 3 barge-in scenarios, every Deep
   modelled-cloud total and ratio, and the README's own arithmetic (89%
   synthesis share, about 74 words to cross 100 ms). Any mismatch fails the
   build.
2. **No sensitivity analysis over the cloud constants.** The dashboard's
   cloud window lets a reader move all five constants and recomputes every
   per-case modelled total and modelled/local ratio. It stays labelled
   "modelled, never measured" and adds no new claim.
3. **No between-run variance.** `level-3-deep/run_probes.py` re-measures the
   Deep stage timings 5 times with the same code and sample counts and
   writes `results_probes.json` (results_deep.json is untouched). On that
   machine the median turn ranged 1313.438 to 1317.71 us, the synthesis share
   of the mean turn was 0.876 to 0.878, and synthesis was the largest stage
   in 20 of 20 cases in every run.
4. **One machine only.** The probes ran on a different machine (aarch64,
   Python 3.12.3, recorded in results_probes.json) from the Muse VM. Absolute
   times differ by several times, but the stage ordering replicated. This is
   a second machine for the ordering claim, not for the absolute numbers.
5. **Time to first audio never measured (ROADMAP v1.1 item 1).** The probes
   time synthesis of the first word against the whole reply: the median
   whole reply costs 5.013 times the first word (results_probes.json). This
   is for the sine loop only and says nothing about a real TTS voice.
6. **Generalisation unmeasured.** 20 held-out paraphrases
   (`level-3-deep/cases_paraphrase.json`), written after the rule was frozen
   and not used to tune it, are scored by the unchanged rule: 9 of 20
   understood, 11 fell to unknown. This is reported as a negative result,
   and the rule was deliberately not changed to pass them.
7. **Tail fragility.** The recorded Deep run puts 11 of 20 turns over budget
   when per-stage p99s are summed (computed on the dashboard from
   results_deep.json). The probe runs record the same count per run (0 of 20
   on the quieter machine), so the "medians pass, tails fail on a shared VM"
   reading now has a contrast case.
8. **Documentation inconsistency.** The Deep README said frame-and-VAD had
   100 samples per case; results_deep.json records n = 99 (3 batches of 33).
   Corrected in level-3-deep/README.md.

### Remaining, with the exact compute or data each needs

1. **Construct validity: no real ASR, TTS or LLM.** Needs a real speech
   workload and models behind the existing stage interfaces: a recorded,
   licensed set of spoken utterances with transcripts (for example 50 to 100
   short commands), a CPU speech recognizer and its weights (a small
   Whisper-family model, on the order of 100 MB), a local TTS voice, and a
   small local LLM. This is a new study (ROADMAP v1.1 items 2, 3 and 8), it
   breaks the standard-library-only rule, and the LLM step needs the GPU
   node, so it is out of scope for a fix.
2. **Measured cloud baseline.** Needs accounts on hosted ASR, LLM and TTS
   services and paid or metered API calls (ROADMAP v1.1 item 4). Excluded
   by the no-paid-API rule. The five constants stay labelled modelled.
3. **Confidence intervals on the shipped Deep run.** Raw per-call samples
   were not saved, so intervals cannot be computed after the fact. Needs one
   rerun of run_deep.py with raw-sample output, which would replace the
   committed results_deep.json; that is an Owner decision, not a silent fix.
   The probe file gives run-level intervals in the meantime.
4. **Quiet-machine tail budget.** Needs a dedicated, otherwise idle machine
   and a p99 budget written before measuring (ROADMAP v1.1 item 6).
5. **Claim-check gate records.** The Jev claim_check results cited in the
   level READMEs live in a workspace outside this repo. Needs those spec and
   result JSON files committed (they are named in each README); the gate
   itself is a paid call and NOVELTY.md stays PROPOSED until it passes.
6. **Concurrency, device path, larger workloads.** ROADMAP v1.1 items 5, 7
   and 9: need multi-session load generation, microphone and speaker
   hardware timing, and recorded long-form workloads.

## Related work (context only, nothing here is compared like for like)

- Stivers, T., et al. (2009). Universals and cultural variation in
  turn-taking in conversation. *PNAS* 106(26), 10587-10592. Human turn gaps
  cluster around a few hundred milliseconds across languages, which is the
  scale a whole voice-agent turn competes with.
- Levinson, S. C., and Torreira, F. (2015). Timing in turn-taking and its
  implications for processing models of language. *Frontiers in Psychology*
  6, 731. Argues listeners plan responses before the turn ends, the human
  analogue of streaming partial intents.
- ITU-T Recommendation G.114 (2003). One-way transmission time. The
  telephony guidance on mouth-to-ear delay, a standard reference point for
  conversational latency budgets.
- Radford, A., et al. (2023). Robust speech recognition via large-scale weak
  supervision. *ICML 2023* (arXiv:2212.04356). The Whisper models, a
  realistic local ASR candidate for remaining gap 1.
- Sohn, J., Kim, N. S., and Sung, W. (1999). A statistical model-based voice
  activity detector. *IEEE Signal Processing Letters* 6(1), 1-3. A standard
  VAD baseline against which the repo's single RMS threshold is a toy.
- Levenshtein, V. I. (1966). Binary codes capable of correcting deletions,
  insertions, and reversals. *Soviet Physics Doklady* 10(8), 707-710. The
  edit distance behind the repo's word error rate.

## Strengths worth keeping

- Scope statements are honest and repeated where readers look.
- Budgets were set before measurement; medians are labelled as medians.
- Hand checks in every README are arithmetic a reader can redo.
- Build results are byte-identical across runs and the site build verifies
  the published hash.
- CI runs every level on two Python versions.
