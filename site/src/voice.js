// JavaScript port of the repo's voice loop, so the playground runs the same rules in the browser.
// Sources: level-1-learn/voice_agent.py (normalize, intent, answer), level-2-build/voice_pipeline.py
// (synthesis, frames, VAD, streaming, dialogue, ASR noise, WER, AudioSession), level-3-deep/latency_lab.py
// (modelled cloud formula). voice.check.mjs replays every committed case through this file at build time.

const KB = {
  time: '10:30',
  date: '2026-11-05',
  weather: { toronto: 'clear, 12 degrees Celsius', dhaka: 'humid, 29 degrees Celsius' },
  default_city: 'toronto',
  name: 'Voice Lab',
};
const HELP_TEXT = 'You can ask for the time, the date, the weather, or a timer.';
const UNKNOWN_TEXT = 'I do not know that yet. Ask for the time, the date, the weather, or a timer.';
const CLARIFY_TIMER = 'For how long should I set the timer?';
const NO_REPEAT = 'There is nothing to repeat yet.';

export const SAMPLE_RATE = 8000;
export const FRAME_SAMPLES = 160;
const WORD_SAMPLES = 960;
const GAP_SAMPLES = 320;
const AMPLITUDE = 8000;
export const VAD_RMS_THRESHOLD = 100;

// Python str.split() with no argument: split on runs of whitespace, drop empties.
const pySplit = (s) => s.split(/\s+/).filter(Boolean);
const stripPunct = (w) => w.replace(/^[.,!?;:]+|[.,!?;:]+$/g, '');
const capitalize = (s) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();

export function normalize(text) {
  return pySplit(text.toLowerCase()).map(stripPunct).filter(Boolean).join(' ');
}

export function extractTimerSeconds(normalized) {
  // ponytail: ASCII digits only; Python isdigit() also accepts other Unicode digits.
  const w = pySplit(normalized).find((x) => /^[0-9]+$/.test(x));
  if (w === undefined) return null;
  const amount = parseInt(w, 10);
  return normalized.includes('minute') ? amount * 60 : amount;
}

export function extractCity(normalized) {
  const words = pySplit(normalized);
  return Object.keys(KB.weather).find((c) => words.includes(c)) ?? KB.default_city;
}

export function stageIntent(normalized) {
  const words = pySplit(normalized);
  if (normalized === 'stop' || normalized === 'cancel') return { intent: 'stop', slots: {} };
  if (words.length && ['hello', 'hi', 'hey'].includes(words[0])) return { intent: 'greeting', slots: {} };
  if (words.includes('timer')) return { intent: 'timer', slots: { seconds: extractTimerSeconds(normalized) } };
  if (words.includes('weather')) return { intent: 'weather', slots: { city: extractCity(normalized) } };
  if (words.includes('time')) return { intent: 'time', slots: {} };
  if (words.includes('date')) return { intent: 'date', slots: {} };
  if (words.includes('your') && words.includes('name')) return { intent: 'name', slots: {} };
  if (words.includes('help') || normalized === 'what can you do') return { intent: 'help', slots: {} };
  if (words.includes('goodbye') || words.includes('bye')) return { intent: 'goodbye', slots: {} };
  return { intent: 'unknown', slots: {} };
}

export function stageAnswer(intent, slots) {
  switch (intent) {
    case 'greeting': return 'Hello. How can I help?';
    case 'time': return `The time is ${KB.time}.`;
    case 'date': return `The date is ${KB.date}.`;
    case 'weather': return `The weather in ${capitalize(slots.city)} is ${KB.weather[slots.city]}.`;
    case 'timer': return slots.seconds == null ? 'I need a number for the timer.' : `Timer set for ${slots.seconds} seconds.`;
    case 'name': return `My name is ${KB.name}, a teaching voice agent.`;
    case 'help': return HELP_TEXT;
    case 'goodbye': return 'Goodbye.';
    case 'stop': return 'Stopped.';
    default: return UNKNOWN_TEXT;
  }
}

export function runTurn(transcript) {
  const normalized = normalize(transcript);
  const { intent, slots } = stageIntent(normalized);
  return { transcript, normalized, intent, slots, response: stageAnswer(intent, slots) };
}

export function partialsOf(transcript) {
  const words = pySplit(normalize(transcript));
  return words.map((_, i) => words.slice(0, i + 1).join(' '));
}

export function streamingTrace(transcript, expectedIntent) {
  const partials = partialsOf(transcript);
  const intents = partials.map((p) => stageIntent(p).intent);
  const idx = intents.indexOf(expectedIntent);
  const first = idx < 0 ? null : idx + 1;
  const stable = first !== null && intents.slice(first - 1).every((x) => x === expectedIntent);
  return { partials: partials.length, partial_intents: intents, first_correct_partial: first, stable_from_first: stable, final_intent: intents.length ? intents[intents.length - 1] : 'unknown' };
}

const encoder = new TextEncoder();
export function wordFrequency(word) {
  return 300 + (encoder.encode(word).reduce((a, b) => a + b, 0) % 400);
}

export function synthesizeSamples(text) {
  const words = pySplit(text);
  const n = words.length ? words.length * WORD_SAMPLES + (words.length - 1) * GAP_SAMPLES : 0;
  const out = new Int16Array(n); // gaps stay 0
  let k = 0;
  words.forEach((word, wi) => {
    const f = wordFrequency(word);
    for (let i = 0; i < WORD_SAMPLES; i++) out[k++] = Math.trunc(AMPLITUDE * Math.sin(2.0 * Math.PI * f * i / SAMPLE_RATE));
    if (wi < words.length - 1) k += GAP_SAMPLES;
  });
  return out;
}

export function audioFrames(samples) {
  const frames = [];
  for (let i = 0; i < samples.length; i += FRAME_SAMPLES) frames.push(samples.subarray(i, i + FRAME_SAMPLES));
  return frames;
}

export function frameRms(frame) {
  if (!frame.length) return 0;
  let s = 0;
  for (const x of frame) s += x * x;
  return Math.sqrt(s / frame.length);
}

export const frameIsSpeech = (frame) => frameRms(frame) > VAD_RMS_THRESHOLD;

// Python round(x, 3) and round(x, 4): toFixed rounds the exact binary value, as Python does.
const round = (x, d) => Number(x.toFixed(d));

export function synthesizeWav(text) {
  const samples = synthesizeSamples(text);
  const frames = audioFrames(samples);
  const speechMask = frames.map(frameIsSpeech);
  const speech = speechMask.filter(Boolean).length;
  return {
    samples, speechMask,
    wav_bytes: 44 + 2 * samples.length, // RIFF header plus 16-bit mono samples
    sample_count: samples.length,
    duration_ms: round(samples.length * 1000 / SAMPLE_RATE, 3),
    frame_count: frames.length, speech_frames: speech, silence_frames: frames.length - speech,
  };
}

const NOISE_SUBSTITUTIONS = { weather: 'whether' };
const NOISE_DROPS = new Set(['the']);
export const NOISE_RULES = { substitutions: NOISE_SUBSTITUTIONS, drops: [...NOISE_DROPS] };

export function simulateAsr(transcript, { substitute = true, drop = true } = {}) {
  return pySplit(normalize(transcript))
    .filter((w) => !(drop && NOISE_DROPS.has(w)))
    .map((w) => (substitute && NOISE_SUBSTITUTIONS[w]) || w)
    .join(' ');
}

export function wordErrorRate(reference, hypothesis) {
  const ref = pySplit(reference), hyp = pySplit(hypothesis);
  if (!ref.length) return hyp.length ? 1.0 : 0.0;
  let prev = Array.from({ length: hyp.length + 1 }, (_, j) => j);
  ref.forEach((r, i) => {
    const cur = [i + 1];
    hyp.forEach((h, j) => { cur[j + 1] = Math.min(prev[j + 1] + 1, cur[j] + 1, prev[j] + (r === h ? 0 : 1)); });
    prev = cur;
  });
  return round(prev[hyp.length] / ref.length, 4);
}

export class DialogueSession {
  constructor() { this.last_intent = null; this.last_city = null; this.last_response = null; this.pending_slot = null; this.turns = 0; }

  followupCity(normalized) {
    const words = pySplit(normalized);
    if (!words.length || !['and', 'what'].includes(words[0])) return null;
    return ['toronto', 'dhaka'].find((c) => words.includes(c)) ?? null;
  }

  hear(transcript) {
    const normalized = normalize(transcript);
    this.turns += 1;
    if (this.pending_slot === 'timer_seconds') {
      const seconds = extractTimerSeconds(normalized ? 'timer ' + normalized : 'timer');
      this.pending_slot = null;
      if (seconds !== null) return this.finish('timer', `Timer set for ${seconds} seconds.`);
      return this.finish('timer_pending', CLARIFY_TIMER, { pending: 'timer_seconds' });
    }
    if (normalized === 'repeat' || normalized === 'say that again') {
      if (this.last_response === null) return this.finish('repeat', NO_REPEAT);
      return this.finish('repeat', this.last_response, { keepLast: true });
    }
    const city = this.followupCity(normalized);
    if (city !== null && this.last_intent === 'weather') {
      const t = runTurn('What is the weather in ' + city);
      return this.finish(t.intent, t.response, { city });
    }
    const t = runTurn(transcript);
    if (t.intent === 'timer' && t.slots.seconds == null) return this.finish('timer_pending', CLARIFY_TIMER, { pending: 'timer_seconds' });
    return this.finish(t.intent, t.response, { city: t.intent === 'weather' ? t.slots.city : null });
  }

  finish(intent, response, { city = null, pending = null, keepLast = false } = {}) {
    this.last_intent = intent;
    if (city !== null) this.last_city = city;
    if (!keepLast) this.last_response = response;
    this.pending_slot = pending;
    return { intent, response };
  }
}

export class AudioSession {
  constructor() { this.dialogue = new DialogueSession(); this.frames = []; this.frames_played = 0; this.interruptions = 0; this.frames_dropped_total = 0; this.state = 'IDLE'; this.last_audio = null; }

  hear(transcript) {
    if (this.state === 'SPEAKING') throw new Error('use interrupt() while SPEAKING');
    const result = this.dialogue.hear(transcript);
    const audio = synthesizeWav(result.response);
    this.last_audio = audio;
    this.frames = audioFrames(audio.samples);
    this.frames_played = 0;
    this.state = this.frames.length ? 'SPEAKING' : 'IDLE';
    return result;
  }

  playFrames(count) {
    let played = 0;
    while (played < count && this.state === 'SPEAKING') {
      this.frames_played += 1; played += 1;
      if (this.frames_played >= this.frames.length) this.state = 'IDLE';
    }
    return played;
  }

  interrupt(transcript) {
    if (this.state !== 'SPEAKING') return null;
    const dropped = this.frames.length - this.frames_played;
    const played = this.frames_played;
    this.frames_dropped_total += dropped;
    this.interruptions += 1;
    this.frames = []; this.frames_played = 0; this.state = 'IDLE';
    if (['stop', 'cancel'].includes(normalize(transcript))) return { dropped, played_before: played, cancelled: true, turn: null };
    return { dropped, played_before: played, cancelled: false, turn: this.hear(transcript) };
  }
}

// latency_lab.modelled_cloud: rtt + asr + llm + tts_base + tts_per_word * words. MODELLED, never measured.
export function modelledCloudMs(c, words) {
  return c.rtt + c.asr + c.llm + c.base + c.perWord * words;
}
export const wordCount = (text) => pySplit(text).length;
