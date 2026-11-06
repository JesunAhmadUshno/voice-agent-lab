# Where the Milliseconds Go: A Voice Agent Latency Budget, Measured and Modelled

By Jesun Ahmad Ushno
Date: 2026-11-05
Status: DRAFT, written fan-out for P18 voice-agent-lab v1.0. Not posted.

## The problem

A voice agent feels slow long before it is slow on paper. Speech
in, an answer, speech out: every stage adds time, and the user
hears the sum. This project builds that loop three times, small,
working, then measured stage by stage, instead of asserting a
latency story.

Repository: https://github.com/JesunAhmadUshno/voice-agent-lab

## Honest scope, stated first

There is no real ASR model, no real TTS voice, and no LLM in any
level. Speech in is text transcripts (Learn) or transcript
partials replayed from a complete transcript (Build and Deep).
Speech out is text responses in Learn and tone-synthesized WAV
in Build and Deep: real WAV data at 8000 Hz, no intelligible
speech. The answer step is a deterministic keyword rule over a
fixed teaching knowledge base (a fixed clock of 10:30, a fixed
date of 2026-11-05, weather for two cities). The Deep cloud side
is modelled only from stated constants, never measured: no cloud
service was called. Every case set is synthetic and authored for
this project, so the perfect scores are weak evidence.

## What was built

Learn: a simulated voice loop over 12 labelled text cases, with
a barge-in state machine. Intent 12 of 12, exact response 12 of
12, total stage latency mean 4.835 microseconds and max 6.095
microseconds against a 5000 microsecond budget, 2 barge-in
scenarios dropping 5 unplayed frames in total. Grade 8,500 of
10,000.

Build: the end-to-end loop. Streaming transcript partials in,
the Learn rule answer reused by import with dialogue state on
top, tone WAV out, barge-in over real audio frames. Grade 7,500
of 10,000.

Deep: the latency budget study. Every local stage timed
individually, a modelled cloud pipeline next to it. Grade 7,700
of 10,000.

## The main result

On 20 labelled single turns, the Deep latency budget study measured the local stages of the Build voice pipeline on the Muse VM (frame and VAD split, streaming partial intent tracing, Learn rule intent and answer, tone WAV synthesis; no ASR model, no TTS model, no LLM): WAV synthesis was the dominant stage in 20 of 20 cases, the median total local latency was 7255.203 microseconds, the maximum total median was 41688.082 microseconds, and 20 of 20 cases were within the 100 ms local budget.

WAV synthesis is about 89 percent of the mean total (mean stage
medians 9832.704 of 11022.228 microseconds) and grows with
response length: 1040.608 microseconds median for the 1-word
response against 22994.106 for the 17-word response, because the
synthesis loops per sample in Python and the whole response is
synthesized before any frame can play. Frame and VAD split is
second (median of medians 752.122 microseconds). The text stages
are negligible: streaming tracing 16.099 and intent plus answer
2.955 microseconds, median of medians.

Build, on its own sets: single intent and exact response 20 of
20, dialogue intent and response 13 of 13 turns in 5 dialogues,
intent 16 of 20 through a deterministic simulated ASR noise map
(mean WER 0.0826, all 4 failures on weather cases, because
weather becoming whether removes the only weather keyword),
323440 WAV bytes (20160.0 ms, 1008 frames of 20 ms), and 165
unplayed frames dropped across 3 barge-in scenarios. In Deep,
the barge-in drop path median was at most 75.864 microseconds.

The modelled cloud total is mean 1212.75 ms per case (range
1185.0 to 1265.0 ms), from constants only: network 80 ms, ASR
final 300 ms, LLM answer 700 ms, TTS 100 ms plus 5 ms per
response word. That is 29.865 to 1010.23 times the measured
local totals. The ratio compares a measured local sine-loop
pipeline against modelled constants for a real cloud speech
stack: it shows the shape of the trade, and it is not evidence
about any real cloud service, because nothing cloud was
measured.

## The verdict

On this pipeline the plumbing is not the latency problem at
median scale: the audio step dominates locally, the text stages
are noise, and interruption is cheap because dropping is a list
discard. The tails are another story: WAV p90 reaches 83890.506
microseconds and p99 reaches 169298.914 microseconds on the
shared VM, so the 100 ms verdict is a median verdict, stated as
such. The method carries over to a real stack; the numbers do
not, because a real recognizer and a real voice change every
row.

## Limits

- No real ASR, TTS, or LLM: recognition, the largest real
  stage, is absent locally and only a modelled constant on the
  cloud side; the dominant measured stage is a sine loop.
- Cloud side modelled, not measured: no observed cost, latency,
  or quality for any real service.
- Synthetic authored sets: 12 Learn cases, 20 Build and Deep
  turns, 13 dialogue turns, all written for this project.
- Synthesis before playback: response-start latency carries
  the full synthesis time, which grows with response length.
- All levels ran on the Muse VM (CPU), not the assigned
  BlackBox fleet node; this study has no GPU step.

## Future

The v1.1 backlog is ROADMAP.md in the repo: streaming synthesis
with time-to-first-frame measurement, real local ASR and TTS
swap-ins behind the same stage interface, a measured cloud
comparison where a free tier allows it, concurrent sessions, a
tail-latency budget on a quiet machine, a device path, and an
LLM answer step. None of that is claimed as done.

Tests: 70 in total, plus the scaffold smoke test.
