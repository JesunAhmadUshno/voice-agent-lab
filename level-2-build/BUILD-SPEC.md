# BUILD-SPEC: voice-agent-lab Level 2 (Build)

Status: written before the Build code, 2026-11-05.
Scope source: SPEC.md project section text: speech in, LLM answer,
speech out, in one loop; streaming audio with interruption handling
(barge-in). Build closes when the system runs end to end, tests
pass, and one benchmark or result table with method is in the README.

## What Build adds over Learn

Learn was a single-turn simulated loop: text transcripts in, text
responses out in simulated word frames, a barge-in state machine,
and a text-stage latency budget. Build turns that into an end-to-end
system other people can run:

1. Real WAV audio out. Every response is synthesized into a real
   WAV byte stream (stdlib wave module, 8000 Hz, 16-bit mono) and
   measured: sample count, duration from sample count, byte size,
   and 20 ms frame count. Playback and barge-in run over those
   real audio frames, not over word groups.
2. Voice activity split. The WAV frames are split into speech and
   silence frames by a root-mean-square energy rule, counted per
   response.
3. Streaming intent. Transcripts arrive as cumulative word
   partials. The intent of every partial is classified with the
   Learn classifier, and the runner records the first partial that
   reaches the final intent.
4. Multi-turn dialogue. A DialogueSession reuses the Learn turn by
   import and adds conversation state: weather follow-ups that name
   only a new city, timer slot filling across two turns, and a
   repeat request that replays the last response.
5. ASR noise robustness. A deterministic simulated ASR step maps
   the word weather to whether and drops the word the. The same 20
   cases are scored clean and through that noise, with word error
   rate measured by a word-level edit distance.
6. A larger scored set: 20 single turns, 5 dialogues with 13 turns,
   the 20 noise runs, and 3 barge-in scenarios over audio frames.

## Substitutions, named before any code ran

Availability was checked on this VM on 2026-11-05 before this spec
was written:

- No ASR model is available: no whisper module, no
  speech_recognition module, no torch, no transformers, and no
  network install is attempted under FREE-ONLY. Speech in therefore
  stays a transcript, now delivered as streaming partials and
  through a named deterministic noise map. That is a simulation of
  ASR output and of one ASR error class, not ASR.
- No TTS voice is available: no espeak, espeak-ng, flite, or
  festival binary, and no pyttsx3 or gTTS module. Speech out is
  therefore a deterministic tone synthesis: each word becomes a
  120 ms sine segment at a word-derived frequency, separated by
  40 ms of silence. The output is a real WAV file with real
  duration and energy, but it carries no intelligible speech and
  no voice quality claim is made anywhere.
- No LLM is available on this VM. The answer step stays the Learn
  deterministic intent rule and template knowledge base, reused by
  import. SPEC names an LLM answer; that step is a named
  substitution at Build and stays open.
- Fleet node: BlackBox is the assigned GPU node and was ON this
  cycle (coordinator verified SSH and the RTX 5050). This Build
  scope is CPU teaching work with no GPU step in it, so the run
  executes on the Muse VM CPU and the grade carries the named
  fleet-node deduction, as in prior cycles. No GPU result is
  claimed and NEEDS-BLACKBOX-ON does not apply: the node is on,
  the work simply has no GPU part.

## Determinism rule

results_build.json holds no wall-clock field at all. Every number
in it is a count, a sample count, a duration derived from a sample
count (samples divided by 8000 Hz), a byte size, or a score over
labelled cases. The file must be byte-identical across two runs;
the runner is run twice and the hashes compared before shipping.

## Acceptance

- Full test suite passes locally (Learn tests, Build tests, smoke).
- Runner exits 0: all 20 single turns and all 13 dialogue turns
  match their expected intent and exact response, and the 3
  barge-in scenarios complete. The noise runs are reported, not
  gated: their degradation is a measured result, not a pass mark.
- No em dash character in any touched file.
- Every measured number in the README comes from the committed
  results_build.json of the shipped run.
