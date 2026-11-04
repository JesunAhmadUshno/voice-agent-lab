# SPEC: voice-agent-lab (P18)

Phase skill: spec-driven-development (house engineering pipeline).
Status: Wave 0 scaffold spec, from Roadmap v2 text and the v3 decision pack. Scope and acceptance criteria below are the v2 section text, kept as the source of truth until the project's wave opens its own spec pass.

Fleet node: BlackBox (GPU). Wave: Wave 7.
Hiring evidence: 3 of 5 (xAI Multimodal and Mistral audio only) [confirmed, fleet and scoring pass 2026-11-04, or the decision pack for P23 to P29].

## Project section text (Roadmap v2, or the v3 candidate text for P23 to P29)

voice-agent-lab: KEEP, scope narrowed to audio

Subject: real-time AI. v1 levels carry over: speech in, LLM answer, speech out, in one loop; streaming audio with interruption handling (barge-in); Deep is a latency budget study (where every millisecond goes, local against cloud speech models). Scope note (change 14): the vision-language items once tied to this project (register items 310, 311, 333) move to P22. The audio and media data step (register item 381) and the Build-level bar (item 865) stay here. Seed repo: SonicClear (Section 8).
Fan-out: Book chapter "A Voice With No Lag". Paper angle: the latency budget study. Course module: P18-voice-agent-lab.

## Acceptance criteria (scaffold level)

- Learn closes when the level-1-learn code runs, its README teaches the idea, and a fresh-eyes reader can follow it.
- Build closes when the system runs end to end, tests pass, and one benchmark or result table with method is in the README.
- Deep closes when the Deep scope in the section text is done, the failure modes are written, and the dossier is updated to ship state.
- No level closes on a claim. Evidence only: code, tests, numbers, links.
