# 0002: Measure a stand-in loop and say so in every claim

Date: 2026-11-08 (recording choices made 2026-11-05). Status: accepted.

## Context

The scope names speech in, an LLM answer and speech out. On the machine
the stages ran on (the Muse VM, CPU) no ASR model, TTS voice or LLM was
available under the free-only rule, and the measured cloud comparison
would need paid services (PROPOSAL.md, Build design, Substitutions).

## Decision

Build and measure the loop with stand-ins behind the same stage
interfaces: typed transcripts and word partials for ASR, a sine-tone WAV
synthesizer for TTS, a keyword rule over a fixed knowledge base for the
answer. Model the cloud side from five stated constants and label it
modelled everywhere. The verdict counts the stand-in loop as the system
that ran end to end; it does not claim that a real speech stack ran.

## Consequences

The headline ("synthesis dominates the turn") is a property of the
stand-in, stated as such. Swapping in real components changes every
timing row and needs models, hardware and possibly paid APIs: an Owner
decision, and a new locked proposal.
