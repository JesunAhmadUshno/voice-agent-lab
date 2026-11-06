# voice-agent-lab

A real-time voice agent study: speech in, answer, speech out, with a latency budget study. The local side is measured and the cloud side is modelled, and the two are never mixed. There is no real ASR model, no real TTS voice, and no LLM in any level: speech in is text transcripts or transcript partials, speech out is text responses in Learn and tone-synthesized WAV in Build and Deep, and the answer step is a deterministic keyword rule over a fixed teaching knowledge base.

- Learn: simulated voice loop over 12 labelled text cases, intent accuracy 12 of 12, exact response match 12 of 12, total stage latency mean 4.835 microseconds and max 6.095 microseconds against a 5000 microsecond budget, 2 barge-in scenarios dropping 5 unplayed frames in total. Grade 8,500 of 10,000.
- Build: end-to-end loop over 20 labelled single turns and 13 dialogue turns in 5 dialogues, intent and exact response 20 of 20 single and 13 of 13 dialogue, intent 16 of 20 through simulated ASR noise (mean WER 0.0826, all 4 failures on weather cases), 323440 WAV bytes (20160.0 ms, 1008 frames of 20 ms), 3 barge-in scenarios dropping 165 unplayed audio frames in total. Grade 7,500 of 10,000.
- Deep: latency budget study. WAV synthesis dominant in 20 of 20 cases, total local latency median case 7255.203 microseconds and max case median 41688.082 microseconds, 20 of 20 within the 100 ms local budget on medians, barge-in drop path median at most 75.864 microseconds with 165 frames dropped in total. Modelled cloud total only: mean 1212.75 ms, 29.865 to 1010.23 times the local totals. Cloud was never measured and no cloud service was called. Grade 7,700 of 10,000.

The perfect intent and response scores are weak evidence: every case set is synthetic and authored for this project, the knowledge base is fixed (a fixed clock, a fixed date, weather for two cities), and the dominant Deep stage times a sine loop, not a speech model.

Grades on record (of 10,000): Learn 8,500, Build 7,500, Deep 7,700.

Every number above is already published in this repo (README.md, DOSSIER.md, and the three level READMEs and results files) and reproduced by the runners in this repo, checked in CI.

Releases: https://github.com/JesunAhmadUshno/voice-agent-lab/releases
