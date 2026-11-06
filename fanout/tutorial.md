# Tutorial: P18 voice-agent-lab, course module

Module: P18-voice-agent-lab
By Jesun Ahmad Ushno
Date: 2026-11-05
License for this tutorial: CC BY 4.0. Code in the repo: Apache-2.0.

## What you will do

You will clone the voice-agent-lab repo, run all three levels,
run the test suite for each level, and read your own results
against the recorded v1.0 numbers. Every command below was
verified by running it in this fan-out cycle. The project needs
Python 3.11 or 3.12 and uses the standard library only. No
model, no API, and no credential are needed.

Two scope facts govern every step. First, there is no real ASR
model, no real TTS voice, and no LLM: speech in is transcripts,
speech out is text or tone WAV with no intelligible speech, and
the answer step is a keyword rule over a fixed teaching
knowledge base. Second, the Deep cloud side is modelled from
stated constants, never measured, and every case set is
synthetic and authored for this project.

## Step 0: Clone and enter the repo

```text
git clone https://github.com/JesunAhmadUshno/voice-agent-lab.git
cd voice-agent-lab
```

Optional smoke check, before the levels:

```text
python tests/test_smoke.py
```

Expected: scaffold smoke test: PASS, 8 files present.

## Step 1: Level 1, Learn, simulated voice loop

Read level-1-learn/README.md first.

```text
python level-1-learn/run_learn.py
python -m unittest tests.test_learn_voice_agent -v
```

Expected: 12 cases; intent 12 of 12, response 12 of 12, within
budget 12 of 12. The recorded run has mean total stage 4.835
microseconds and max 6.095 microseconds against the 5000
microsecond budget; your latency values will differ, because
they are measured wall-clock values. 30 tests pass. The runner
writes level-1-learn/results_learn.json; its correctness fields
are deterministic and its latency fields vary between runs.

## Step 2: Level 2, Build, end-to-end voice loop

Read level-2-build/README.md and level-2-build/BUILD-SPEC.md.

```text
python level-2-build/run_build.py
python -m unittest tests.test_build_voice_agent -v
```

Expected: single intent and response 20 of 20; dialogue intent
and response 13 of 13; noise intent 16 of 20 (mean WER 0.0826);
audio 323440 WAV bytes, 20160.0 ms, 1008 frames; barge-in 3
scenarios, 165 frames dropped. 23 Build tests pass (53 in total
with Learn). The runner writes level-2-build/results_build.json,
which holds no wall-clock field and is byte-identical across
runs.

## Step 3: Level 3, Deep, latency budget study

Read level-3-deep/README.md and level-3-deep/DEEP-SPEC.md.

```text
python level-3-deep/run_deep.py
python -m unittest tests.test_deep_voice_agent -v
```

Expected: intent and response 20 of 20, within budget 20 of 20
on medians, modelled cloud mean 1212.75 ms. The recorded run
has median total 7255.203 microseconds and max total median
41688.082 microseconds; your latency values will differ,
because they are measured wall-clock values, and only the
deterministic fields (intents, responses, frame counts, drops,
audio sizes, modelled totals) are identical across runs. 17
Deep tests pass (70 in total). Cloud figures are modelled only
in this step; nothing is called.

## Step 4: Full suite

```text
python -m unittest discover -s tests -v
python tests/test_smoke.py
```

Expected: 70 tests, all passing, plus the scaffold smoke test.

## If your numbers differ

Check the results files (results_learn.json, results_build.json,
results_deep.json) first. For Learn and Deep, ignore timing
fields when comparing: they vary by machine load. Every
deterministic field should match the recorded v1.0 values on
the same code, and results_build.json should be byte-identical.
