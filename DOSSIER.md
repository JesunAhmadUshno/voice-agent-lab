# DOSSIER: voice-agent-lab (P18) v1, 2026-11-04

Written under the documentation and publishing standard (past, present, future). Updated at ship time.

## Past

Prior art for this project is named in NOVELTY.md (voice agent platforms and the SonicClear seed product). The history of the problem, the key papers and systems, and what was tried before are recorded in the Roadmap v2 section text in SPEC.md and will be expanded with dated sources at the project's wave, before Build opens.

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

## Future

Open problems and the project's next steps sit in the Deep level scope in SPEC.md. Any forecast about this field is [unverified] unless a dated primary source is added here at the wave update.
