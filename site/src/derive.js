// Pure derivations from the committed results and README files. App.jsx and derive.check.mjs both call these,
// so every derived number on the page is asserted at build time.

export const STAGES = ['wav_synthesis', 'frame_vad', 'streaming', 'intent_answer'];
const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;

export function deepShares(deep) {
  const wavMean = mean(deep.cases.map((c) => c.stage_us.wav_synthesis.median_us));
  return { wavMean, wavShare: wavMean / deep.summary.mean_total_median_us };
}

// The per-word and base TTS constants are recovered from two cases with different word counts.
export function cloudDefaults(deep) {
  const cs = deep.cases.map((c) => c.modelled_cloud);
  const a = cs[0], b = cs.find((c) => c.response_words !== a.response_words);
  const perWord = (a.tts_first_audio_ms - b.tts_first_audio_ms) / (a.response_words - b.response_words);
  return { rtt: a.network_rtt_ms, asr: a.asr_final_ms, llm: a.llm_answer_ms, base: a.tts_first_audio_ms - perWord * a.response_words, perWord };
}

// Python round(x, 3) of the ratio, as run_deep.py writes it.
export const cloudRatio = (cloudMs, totalMedianUs) => Number((cloudMs / Number((totalMedianUs / 1000).toFixed(3))).toFixed(3));

// README extrapolation: at the per-word WAV rate of the longest response, how many words cross the budget.
export function crossingWords(deep) {
  const longest = deep.cases.reduce((m, c) => (c.size.words > m.size.words ? c : m));
  const perWordUs = longest.stage_us.wav_synthesis.median_us / longest.size.words;
  return { caseId: longest.case_id, words: longest.size.words, perWordUs, crossing: deep.budget_us / perWordUs };
}

export const designShares = (deep) => Object.fromEntries(STAGES.map((s) => [s, deep.cases[0].stage_shares[s].stage_budget_us]));

export const tailBreaches = (deep, stat) => deep.cases.filter((c) => STAGES.reduce((a, s) => a + c.stage_us[s][stat], 0) > deep.budget_us).length;

// Level README parsing: grade, deductions, failure modes, recorded date and machine.
export function parseLevelReadme(md) {
  const grade = Number(md.match(/^Grade: ([\d,]+) of 10,000/m)[1].replace(/,/g, ''));
  const dedBlock = md.split(/^Deductions[^\n]*\n/m)[1].split(/\n\n/)[0];
  const deductions = dedBlock.split(/\n- /).map((s) => s.replace(/^- /, '').replace(/\s+/g, ' ').trim()).filter(Boolean).map((s) => {
    const m = s.match(/^(.*):\s*minus ([\d,]+)\.?$/);
    return { text: m[1], points: Number(m[2].replace(/,/g, '')) };
  });
  const fmBlock = md.split(/^## Failure modes and limits\n/m)[1].split(/\n## /)[0];
  const failures = fmBlock.split(/\n- /).map((s) => s.replace(/^\s*- /, '').replace(/\s+/g, ' ').trim()).filter(Boolean);
  const rec = md.match(/^## Results \(measured ([\d-]+), ([^,]+), ([^)]+)\)/m);
  return { grade, deductions, failures, recorded: rec && { date: rec[1], machine: rec[2], python: rec[3] } };
}

export function parseBacklog(md) {
  const block = md.split(/^## v1\.1 backlog[^\n]*\n/m)[1].split(/\n## /)[0];
  return block.split(/\n(?=\d+\. )/).filter((s) => /^\d+\. /.test(s)).map((s) => {
    const t = s.replace(/^\d+\. /, '').replace(/\s+/g, ' ').trim();
    const i = t.indexOf(': ');
    return i > 0 ? { title: t.slice(0, i), text: t.slice(i + 2) } : { title: t, text: '' };
  });
}

export const shaPrefix = (md) => md.match(/sha256 ([0-9a-f]{16})/)[1];
