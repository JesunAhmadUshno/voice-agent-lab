// Known-answer check, run by "npm run build" before vite. Replays every committed case through the JS port
// (voice.js) and the page derivations (derive.js), and fails the build on any mismatch with the repo's files.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import * as V from './voice.js';
import * as D from './derive.js';

const root = new URL('../../', import.meta.url);
const read = (p) => readFileSync(new URL(p, root), 'utf8');
const json = (p) => JSON.parse(read(p));
const learnCases = json('level-1-learn/cases_learn.json');
const learn = json('level-1-learn/results_learn.json');
const build = json('level-2-build/results_build.json');
const buildCases = json('level-2-build/cases_build.json');
const deepCases = json('level-3-deep/cases_deep.json');
const deep = json('level-3-deep/results_deep.json');
const probes = json('level-3-deep/results_probes.json');
let n = 0;
const eq = (a, b, msg) => { assert.deepEqual(a, b, msg); n++; };

// Learn: intent, slots, response, normalized text.
for (const c of learnCases) { const t = V.runTurn(c.transcript); eq([t.intent, t.response], [c.expected_intent, c.expected_response], c.case_id); }
for (const r of learn.cases) { const t = V.runTurn(r.transcript); eq([t.normalized, t.intent, t.slots, t.response], [r.normalized, r.intent, r.slots, r.response], `learn ${r.case_id}`); }

// Deep single cases and Build single turns: intent, response, WAV record, streaming trace.
for (const c of deepCases.single) { const t = V.runTurn(c.transcript); eq([t.intent, t.response], [c.expected_intent, c.expected_response], `deep ${c.case_id}`); }
for (const r of build.single) {
  const t = V.runTurn(r.transcript);
  eq([t.intent, t.response], [r.intent, r.response], `build ${r.case_id}`);
  const { samples, speechMask, ...audio } = V.synthesizeWav(t.response);
  eq(audio, r.audio, `audio ${r.case_id}`);
  eq(V.streamingTrace(r.transcript, t.intent), r.streaming, `streaming ${r.case_id}`);
}
for (const r of deep.cases) {
  const { samples, speechMask, ...audio } = V.synthesizeWav(r.response);
  eq(audio, r.audio, `deep audio ${r.case_id}`);
  eq(V.wordCount(r.response), r.size.words, `deep words ${r.case_id}`);
}
const sumAudio = (k) => build.single.reduce((a, r) => a + V.synthesizeWav(r.response)[k], 0);
eq(sumAudio('wav_bytes'), build.summary.audio_total_wav_bytes, 'total wav bytes');
eq(sumAudio('frame_count'), build.summary.audio_total_frames, 'total frames');
eq(sumAudio('speech_frames'), build.summary.audio_speech_frames, 'speech frames');

// Dialogues: one DialogueSession per dialogue, state carried across turns.
buildCases.dialogues.forEach((d, i) => {
  const s = new V.DialogueSession();
  d.turns.forEach((t, j) => { const got = s.hear(t.transcript); const rec = build.dialogues[i].turns[j]; eq([got.intent, got.response], [rec.intent, rec.response], `${d.dialogue_id} turn ${j + 1}`); });
});

// Simulated ASR noise and WER (Python round-half-even at 4 dp).
for (const r of build.noise) {
  const heard = V.simulateAsr(r.transcript);
  eq([heard, V.wordErrorRate(V.normalize(r.transcript), heard), V.runTurn(heard).intent], [r.asr_heard, r.wer, r.intent], `noise ${r.case_id}`);
}
eq(Number((build.noise.reduce((a, r) => a + r.wer, 0) / build.noise.length).toFixed(4)), build.summary.noise_mean_wer, 'mean WER');
eq(V.wordErrorRate('a b c', 'a x c d'), 0.6667, 'WER hand check');

// Barge-in over audio frames (Build and Deep share the scenarios).
for (const [i, sc] of buildCases.barge_in.entries()) {
  const s = new V.AudioSession();
  s.hear(sc.first_transcript);
  const total = s.frames.length;
  s.playFrames(sc.play_frames);
  const hit = s.interrupt(sc.interrupt_transcript);
  const rec = build.barge_in[i];
  eq([total, hit.played_before, hit.dropped, hit.cancelled, hit.turn?.intent ?? null, hit.turn?.response ?? null, s.state],
    [rec.first_frames_total, rec.frames_played_before_interrupt, rec.frames_dropped, rec.cancelled, rec.new_intent, rec.new_response, rec.state_after], `barge ${sc.scenario_id}`);
  eq(hit.dropped, deep.barge_in[i].frames_dropped, `deep barge ${sc.scenario_id}`);
}

// Modelled cloud: constants recovered from the file reproduce every per-case total and ratio.
const cloud = D.cloudDefaults(deep);
eq(cloud, { rtt: 80, asr: 300, llm: 700, base: 100, perWord: 5 }, 'cloud constants');
for (const r of deep.cases) {
  const total = V.modelledCloudMs(cloud, V.wordCount(r.response));
  eq(total, r.modelled_cloud.total_ms, `cloud ${r.case_id}`);
  eq(D.cloudRatio(total, r.total_median_us), r.modelled_cloud_to_local_ratio, `ratio ${r.case_id}`);
}

// Derived headline numbers match the Deep README's own arithmetic.
const sh = D.deepShares(deep);
eq(Number(sh.wavMean.toFixed(3)), 9832.704, 'mean WAV median (Deep README)');
eq(Math.round(sh.wavShare * 100), 89, 'WAV share of mean total (Deep README)');
eq(Math.round(D.crossingWords(deep).crossing), 74, 'words to cross 100 ms (Deep README)');
eq(D.designShares(deep), { wav_synthesis: 70000, frame_vad: 10000, streaming: 10000, intent_answer: 5000 }, 'design shares');
for (const r of deep.cases) eq(Number(D.STAGES.reduce((a, s) => a + r.stage_us[s].median_us, 0).toFixed(3)), r.total_median_us, `total ${r.case_id}`);

// Grades and deductions parsed from the level READMEs add up.
for (const [p, g] of [['level-1-learn/README.md', 8500], ['level-2-build/README.md', 7500], ['level-3-deep/README.md', 7700]]) {
  const L = D.parseLevelReadme(read(p));
  eq(L.grade, g, `${p} grade`);
  eq(L.deductions.reduce((a, d) => a + d.points, 0), 10000 - g, `${p} deductions sum`);
  assert.ok(L.failures.length >= 5, `${p} failure modes`);
}
eq(D.parseBacklog(read('ROADMAP.md')).length, 9, 'v1.1 backlog items');

// Build results are byte-identical across runs: the README's sha256 prefix matches the committed file.
eq(createHash('sha256').update(readFileSync(new URL('level-2-build/results_build.json', root))).digest('hex').slice(0, 16), D.shaPrefix(read('level-2-build/README.md')), 'build sha256');

// Paraphrase probe replays through the JS rule.
for (const r of probes.paraphrase.cases) eq(V.stageIntent(V.normalize(r.transcript)).intent, r.intent, `paraphrase ${r.case_id}`);

console.log(`voice parity ok: ${n} assertions`);
