# LinkedIn post draft: P18 voice-agent-lab v1.0

Status: DRAFT NOT POSTED
Date drafted: 2026-11-05
Author: Jesun Ahmad Ushno
Rule for this platform: the link goes in the first comment, not in the
post body. The first comment line is at the end of this file.

## Post body

Where does a voice agent actually spend its time? I built the
loop three times and measured every stage, instead of guessing.

voice-agent-lab v1.0 is done: Learn, Build, and Deep, all open,
all measured, Python standard library only.

The scope, up front: there is no real ASR model, no real TTS
voice, and no LLM in this project. Speech in is transcripts.
Speech out is text, then tone WAV with no intelligible speech.
Answers come from a keyword rule over a fixed teaching knowledge
base. The cloud side of the study is modelled from stated
constants, never measured.

Learn: 12 cases, intent and exact response 12 of 12, mean total
stage latency 4.835 microseconds against a 5000 microsecond
budget, 5 unplayed frames dropped across 2 barge-in scenarios.

Build: 20 single turns at 20 of 20, 13 dialogue turns at 13 of
13, intent 16 of 20 through simulated ASR noise (mean WER
0.0826, all 4 failures on weather cases), 323440 WAV bytes over
1008 frames, 165 frames dropped across 3 barge-in scenarios.

Deep: WAV synthesis was the dominant stage in 20 of 20 cases.
Median total local latency 7255.203 microseconds, max case
median 41688.082, 20 of 20 within the 100 ms budget on medians.
Barge-in drop path median at most 75.864 microseconds. Modelled
cloud total: mean 1212.75 ms, from constants only.

The honest limit, in the post: the case sets are synthetic and
authored for this project, the dominant stage times a sine loop
rather than a speech model, and the budget verdict is a median
verdict, because the p99 tails on a shared machine spike far
above it.

Grades, house scale: Learn 8,500, Build 7,500, Deep 7,700 of
10,000. 70 tests in total, plus the smoke test.

Which stage would you measure first in a production voice
agent: recognition, the model, or synthesis?

## First comment (post this as the first comment, per the standing rule)

Repo, releases v0.1, v0.5, and v1.0, and the full tutorial: https://github.com/JesunAhmadUshno/voice-agent-lab
