import { useMemo, useState, useEffect, useRef, useId, useCallback } from 'react';
import build from '../../level-2-build/results_build.json';
import buildCases from '../../level-2-build/cases_build.json';
import deep from '../../level-3-deep/results_deep.json';
import probes from '../../level-3-deep/results_probes.json';
import learnMd from '../../level-1-learn/README.md?raw';
import buildMd from '../../level-2-build/README.md?raw';
import deepMd from '../../level-3-deep/README.md?raw';
import roadmapMd from '../../ROADMAP.md?raw';
import * as V from './voice.js';
import * as D from './derive.js';

const REPO = 'https://github.com/JesunAhmadUshno/voice-agent-lab';
const blob = (p) => `${REPO}/blob/main/${p}`;
const ms = (us, d = 2) => (us / 1000).toFixed(d);
const pct = (x, d = 0) => `${(x * 100).toFixed(d)}%`;

const LEVELS = [['Learn', 'level-1-learn', D.parseLevelReadme(learnMd)], ['Build', 'level-2-build', D.parseLevelReadme(buildMd)], ['Deep', 'level-3-deep', D.parseLevelReadme(deepMd)]];
const DEEP_README = LEVELS[2][2];
const REC = DEEP_README.recorded;
const RECORDED = `recorded ${REC.date}, ${REC.machine}, CPU`;
const SHARES = D.deepShares(deep);
const CLOUD0 = D.cloudDefaults(deep);
const CROSS = D.crossingWords(deep);
const DESIGN = D.designShares(deep);
const S = deep.summary;
const N = deep.cases.length;
const PRESETS = deep.cases.map((c) => c.transcript);
const STAGE_META = {
  wav_synthesis: ['WAV synthesis', 'var(--primary)'],
  frame_vad: ['Frame and VAD split', 'var(--warn)'],
  streaming: ['Streaming partial intents', 'var(--good)'],
  intent_answer: ['Intent and answer', 'var(--bad)'],
};

const SECTIONS = [['top', 'Overview', '◎'], ['talk', 'Talk to it', '◉'], ['barge', 'Barge-in', '⏹'], ['noise', 'ASR noise', '≈'], ['budget', 'Budget', '▥'], ['cloud', 'Local vs cloud', '☁'], ['scaling', 'Scaling', '⟋'], ['probes', 'Probes', '±'], ['grades', 'Grades', '✓'], ['reproduce', 'Reproduce', '❯_']];

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) { els.forEach((e) => e.classList.add('in')); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.08 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, []);
}

function MenuBar() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 30000); return () => clearInterval(t); }, []);
  return (
    <div className="menubar" role="banner">
      <span className="apple" aria-hidden="true">◆</span>
      <a className="app" href="#top">Voice Agent Lab</a>
      <a className="m" href={blob('SPEC.md')}>Spec</a>
      <a className="m" href={blob('level-3-deep/README.md')}>Deep study</a>
      <a className="m" href={blob('docs/research-review.md')}>Research review</a>
      <span className="spacer" />
      <span className="status"><i /> {S.intent_correct}/{S.cases} cases pass</span>
      <a href={REPO}>GitHub ↗</a>
      <span className="clock">{now.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' })}</span>
    </div>
  );
}

function Dock() {
  const [active, setActive] = useState('top');
  useEffect(() => {
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && setActive(e.target.id)), { rootMargin: '-45% 0px -50% 0px' });
    SECTIONS.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
    return () => io.disconnect();
  }, []);
  return (
    <nav className="dock" aria-label="Sections">
      {SECTIONS.map(([id, label, icon]) => (
        <a key={id} href={`#${id}`} className={active === id ? 'on' : ''} aria-current={active === id ? 'true' : undefined}>
          <span className="ico" aria-hidden="true">{icon}</span><span className="lbl">{label}</span>
        </a>
      ))}
    </nav>
  );
}

function Range({ label, value, min, max, step, onChange, show }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label} <span>{show}</span></label>
      <input id={id} type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(+e.target.value)} />
    </div>
  );
}

// ---- audio: one AudioContext, created on the first click only ----
let audioCtx = null;
function startPlayback(samples) {
  const AC = typeof window !== 'undefined' && (window.AudioContext || window.webkitAudioContext);
  if (!AC || !samples.length) return null;
  try {
    audioCtx ??= new AC();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const buf = audioCtx.createBuffer(1, samples.length, V.SAMPLE_RATE);
    const ch = buf.getChannelData(0);
    for (let i = 0; i < samples.length; i++) ch[i] = samples[i] / 32768;
    const src = audioCtx.createBufferSource();
    const gain = audioCtx.createGain();
    gain.gain.value = 0.3;
    src.buffer = buf;
    src.connect(gain).connect(audioCtx.destination);
    src.start();
    const t0 = audioCtx.currentTime;
    return { elapsed: () => audioCtx.currentTime - t0, stop: () => { try { src.stop(); } catch { /* already ended */ } src.disconnect(); gain.disconnect(); } };
  } catch {
    return null;
  }
}

// Plays samples and reports the 20 ms frame index reached, so strips can follow playback.
function usePlayer() {
  const [frame, setFrame] = useState(null);
  const cur = useRef(null);
  const raf = useRef(0);
  const stop = useCallback(() => {
    cancelAnimationFrame(raf.current);
    const p = cur.current; cur.current = null;
    if (!p) return 0;
    const reached = Math.floor(p.elapsed() * 1000 / 20);
    p.stop();
    return Math.min(reached, p.frames);
  }, []);
  const play = useCallback((samples, onEnd) => {
    stop();
    const frames = Math.ceil(samples.length / V.FRAME_SAMPLES);
    const audio = startPlayback(samples);
    const t0 = performance.now();
    const p = { frames, elapsed: audio ? audio.elapsed : () => (performance.now() - t0) / 1000, stop: audio ? audio.stop : () => {} };
    cur.current = p;
    const tick = () => {
      if (cur.current !== p) return;
      const f = Math.floor(p.elapsed() * 1000 / 20);
      if (f >= frames) { setFrame(frames); cur.current = null; p.stop(); onEnd?.(); return; }
      setFrame(f);
      raf.current = requestAnimationFrame(tick);
    };
    tick();
  }, [stop]);
  useEffect(() => () => stop(), [stop]);
  return { frame, play, stop, setFrame, playing: () => cur.current !== null };
}

function FrameStrip({ mask, played = null, dropFrom = null, label }) {
  const n = mask.length, w = 6, H = 26;
  return (
    <svg className="chart strip" viewBox={`0 0 ${Math.max(n, 1) * w} ${H}`} preserveAspectRatio="none" role="img" aria-label={label}>
      {mask.map((sp, i) => {
        const dropped = dropFrom !== null && i >= dropFrom;
        const fill = dropped ? 'var(--bad)' : sp ? 'var(--primary)' : 'var(--grid)';
        const op = dropped ? 0.35 : played === null || i < played ? 1 : 0.3;
        return <rect key={i} x={i * w + 0.5} y={sp ? 2 : 9} width={w - 1} height={sp ? H - 4 : H - 18} rx="1.5" fill={fill} opacity={op} />;
      })}
    </svg>
  );
}

export default function App() {
  useReveal();
  return (
    <div className="wrap">
      <MenuBar />
      <div className="glow" aria-hidden="true" />
      <Hero />
      <Talk />
      <Barge />
      <Noise />
      <Budget />
      <Cloud />
      <Scaling />
      <Probes />
      <Grades />
      <Reproduce />
      <Dock />
      <footer>
        Code: Apache-2.0. Every number on this page is read from the committed <code>level-*/results_*.json</code> and README files at build time,
        and a build-time check replays all {buildCases.single.length} Build turns, {buildCases.dialogues.length} dialogues and {buildCases.barge_in.length} barge-in scenarios through the in-browser port before the page is published.
      </footer>
    </div>
  );
}

function Hero() {
  return (
    <header className="card hero window" id="top" data-title="voice-agent-lab — README">
      <div className="head">
        <p className="eyebrow">Latency budget study · CPU voice loop</p>
        <span className="pill good">● {S.within_budget}/{N} within budget</span>
      </div>
      <h1>In this voice loop, the <em>audio</em>, not the answer, eats the budget.</h1>
      <p className="sub">
        Synthesizing the reply takes about {pct(SHARES.wavShare)} of each turn&rsquo;s measured latency, the thinking step takes microseconds,
        and all {S.within_budget} of {N} turns finish inside a {ms(deep.budget_us, 0)} ms budget at the median.
        Talk to the agent below: the same rules run in your browser, and the timing charts replay the recorded Python runs.
      </p>
      <div className="scope" role="note">
        <b>Honest scope.</b> No ASR model, no TTS voice, no LLM. Typed transcripts stand in for speech recognition, a sine-tone synthesizer
        stands in for the voice, and a keyword rule over a fixed knowledge base answers. The study budgets the plumbing, not a speech stack.
      </div>
      <div className="actions">
        <a className="btn primary" href="#talk">Talk to it</a>
        <a className="btn ghost" href="#budget">See where the time goes</a>
        <span className="hint">Timings: {RECORDED}</span>
      </div>
      <div className="tiles">
        <div className="tile"><div className="num">{ms(S.median_total_median_us)} ms</div><div className="cap">Median turn, sum of four stage medians</div></div>
        <div className="tile"><div className="num">{ms(S.max_total_median_us, 1)} ms</div><div className="cap">Slowest turn ({deep.cases.find((c) => c.total_median_us === S.max_total_median_us).case_id}) at the median</div></div>
        <div className="tile"><div className="num">{pct(SHARES.wavShare)}</div><div className="cap">WAV synthesis share of the mean turn ({ms(SHARES.wavMean)} of {ms(S.mean_total_median_us)} ms)</div></div>
        <div className="tile"><div className="num">{S.dominant_stage_cases}/{N}</div><div className="cap">Turns where synthesis is the largest stage</div></div>
      </div>
    </header>
  );
}

function Talk() {
  const session = useRef(new V.DialogueSession());
  const [text, setText] = useState(PRESETS[3]);
  const makeTurn = (transcript) => {
    const got = session.current.hear(transcript);
    const rule = V.runTurn(transcript);
    return { transcript, ...got, slots: rule.slots, trace: V.streamingTrace(transcript, rule.intent), audio: V.synthesizeWav(got.response), state: { ...session.current } };
  };
  const [turns, setTurns] = useState(() => [makeTurn(PRESETS[3])]);
  const player = usePlayer();
  const say = (t) => {
    const transcript = (t ?? text).trim();
    if (!transcript) return;
    player.stop(); player.setFrame(null);
    const turn = makeTurn(transcript);
    setTurns((ts) => [turn, ...ts].slice(0, 6));
  };
  const reset = () => { session.current = new V.DialogueSession(); player.stop(); setTurns([]); };
  const last = turns[0];
  return (
    <section id="talk" className="card window reveal" data-title="voice_agent.py — Playground">
      <div className="head">
        <div>
          <p className="eyebrow">Live in your browser</p>
          <h2>Talk to it. The <em>same rules</em> answer here.</h2>
          <p className="sub">
            A line-for-line JavaScript port of <a href={blob('level-1-learn/voice_agent.py')}>voice_agent.py</a> and the dialogue state in <a href={blob('level-2-build/voice_pipeline.py')}>voice_pipeline.py</a>.
            Watch the intent settle word by word, then hear the reply as the repo&rsquo;s tone synthesis. Follow-ups keep context: try a city on its own, a timer with no amount, or &ldquo;say that again&rdquo;.
          </p>
        </div>
        <span className="pill info">● live</span>
      </div>
      <form className="say" onSubmit={(e) => { e.preventDefault(); say(); }}>
        <div className="field grow">
          <label htmlFor="say-text">Transcript (what the ASR would have heard)</label>
          <input id="say-text" type="text" value={text} maxLength={160} onChange={(e) => setText(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="say-preset">Or pick a test case</label>
          <select id="say-preset" value="" onChange={(e) => { if (e.target.value) { setText(e.target.value); say(e.target.value); } }}>
            <option value="">Choose…</option>
            {deep.cases.map((c) => <option key={c.case_id} value={c.transcript}>{c.case_id} · {c.transcript}</option>)}
          </select>
        </div>
        <button className="btn primary" type="submit">Send turn</button>
      </form>
      <div className="chips" aria-label="Follow-up suggestions">
        {['And in Dhaka', 'Set a timer', '5 minutes', 'Say that again', 'What is your name'].map((s) => <button key={s} type="button" className="chip" onClick={() => { setText(s); say(s); }}>{s}</button>)}
        <button type="button" className="chip ghost" onClick={reset}>Reset conversation</button>
      </div>
      {last ? (
        <div className="grid2 turn">
          <div>
            <h3>Streaming partial intents</h3>
            <ol className="partials">
              {last.trace.partial_intents.map((it, i) => (
                <li key={i} className={it === 'unknown' ? '' : 'hit'}><span className="mono">{V.partialsOf(last.transcript)[i].split(' ').slice(-1)[0]}</span><small>{it}</small></li>
              ))}
            </ol>
            <p className="hint">{last.trace.final_intent === 'unknown' ? `The keyword rule finds no intent in these words${last.intent !== 'unknown' ? '; the dialogue state supplied it.' : '.'}` : last.trace.first_correct_partial ? `Intent settled at word ${last.trace.first_correct_partial} of ${last.trace.partials}${last.trace.stable_from_first ? ' and stayed stable.' : ', then changed.'}` : 'No partial reached a known intent.'}</p>
            <table className="kv">
              <tbody>
                <tr><th>Dialogue intent</th><td><span className={`pill ${last.intent === 'unknown' ? 'warn' : 'good'}`}>{last.intent}</span></td></tr>
                <tr><th>Rule slots</th><td className="mono">{JSON.stringify(last.slots)}</td></tr>
                <tr><th>Session state</th><td className="mono">city {last.state.last_city ?? '–'} · pending {last.state.pending_slot ?? '–'} · turn {last.state.turns}</td></tr>
              </tbody>
            </table>
          </div>
          <div>
            <h3>Response</h3>
            <blockquote className="reply">{last.response}</blockquote>
            <div className="actions" style={{ marginTop: 8 }}>
              <button className="btn ghost" type="button" onClick={() => player.play(last.audio.samples)}>▶ Play tone WAV</button>
              <span className="hint">{last.audio.wav_bytes.toLocaleString()} bytes · {last.audio.duration_ms} ms · {last.audio.frame_count} frames</span>
            </div>
            <FrameStrip mask={last.audio.speechMask} played={player.frame} label={`VAD frame strip: ${last.audio.speech_frames} speech and ${last.audio.silence_frames} silence frames of 20 ms`} />
            <div className="legend"><span><i style={{ background: 'var(--primary)' }} />speech frame (RMS &gt; {V.VAD_RMS_THRESHOLD})</span><span><i style={{ background: 'var(--grid)' }} />silence frame</span></div>
          </div>
        </div>
      ) : <p className="hint empty">Send a turn to see the trace. Nothing is sent anywhere: it all runs on this page.</p>}
      {turns.length > 1 && (
        <div className="history">
          <h3>Earlier turns</h3>
          <ul>{turns.slice(1).map((t, i) => <li key={i}><span className="mono">{t.transcript}</span> → <b>{t.intent}</b>: {t.response}</li>)}</ul>
        </div>
      )}
    </section>
  );
}

function Barge() {
  const sc0 = buildCases.barge_in[0];
  const [first, setFirst] = useState(sc0.first_transcript);
  const [cut, setCut] = useState(sc0.interrupt_transcript);
  const [view, setView] = useState({ state: 'IDLE', mask: [], dropFrom: null, hit: null, log: [] });
  const session = useRef(null);
  const player = usePlayer();
  const speak = () => {
    const s = new V.AudioSession();
    s.hear(first);
    session.current = s;
    setView({ state: s.state, mask: s.last_audio.speechMask, dropFrom: null, hit: null, log: ['IDLE → LISTENING → THINKING → SPEAKING (inside hear())'] });
    player.play(s.last_audio.samples, () => { s.playFrames(s.frames.length); setView((v) => ({ ...v, state: s.state, log: [...v.log, 'last frame played → IDLE'] })); });
  };
  const interrupt = () => {
    const s = session.current;
    if (!s || s.state !== 'SPEAKING') return;
    const reached = player.stop();
    s.playFrames(reached);
    const mask = s.last_audio.speechMask;
    const hit = s.interrupt(cut);
    if (!hit) return;
    setView({ state: s.state, mask, dropFrom: hit.played_before, hit, ctx: { ...s.dialogue }, log: [`barge-in at frame ${hit.played_before}: ${hit.dropped} unplayed frames dropped`, hit.cancelled ? 'stop → playback cancelled → IDLE' : 'new turn → SPEAKING'] });
    if (!hit.cancelled) player.play(s.last_audio.samples, () => { s.playFrames(s.frames.length); setView((v) => ({ ...v, state: s.state })); });
  };
  const replays = useMemo(() => buildCases.barge_in.map((sc, i) => {
    const s = new V.AudioSession();
    s.hear(sc.first_transcript); const total = s.frames.length; s.playFrames(sc.play_frames);
    const hit = s.interrupt(sc.interrupt_transcript);
    const rec = build.barge_in[i];
    return { sc, total, hit, match: hit.dropped === rec.frames_dropped && total === rec.first_frames_total, d: deep.barge_in[i] };
  }), []);
  const speaking = view.state === 'SPEAKING';
  return (
    <section id="barge" className="card window reveal" data-title="AudioSession — barge-in">
      <div className="head">
        <div>
          <p className="eyebrow">Live, plus recorded timings</p>
          <h2>Interrupt it mid-sentence. Unplayed frames are <em>dropped</em>, context survives.</h2>
          <p className="sub">
            Press speak, then barge in while the tone is playing. The port of <code>AudioSession.play_frames</code> and <code>interrupt</code> stops real playback,
            counts the frames you heard and the ones dropped, and runs your interruption through the same dialogue session.
          </p>
        </div>
        <div className="states" aria-label="Session state">
          {['IDLE', 'LISTENING', 'THINKING', 'SPEAKING'].map((st) => <span key={st} className={`pill ${view.state === st ? (st === 'SPEAKING' ? 'info' : 'good') : 'off'}`}>{st}</span>)}
        </div>
      </div>
      <div className="controls two">
        <div className="field"><label htmlFor="b-first">Agent is asked</label><input id="b-first" type="text" value={first} maxLength={160} onChange={(e) => setFirst(e.target.value)} /></div>
        <div className="field"><label htmlFor="b-cut">You barge in with</label><input id="b-cut" type="text" value={cut} maxLength={160} onChange={(e) => setCut(e.target.value)} /></div>
      </div>
      <div className="actions" style={{ marginTop: 0 }}>
        <button className="btn ghost" type="button" onClick={speak}>▶ Speak</button>
        <button className="btn primary" type="button" onClick={interrupt} disabled={!speaking || view.hit !== null}>⏹ Barge in now</button>
        <span className="hint">{speaking && player.frame !== null ? `playing frame ${Math.min(player.frame + 1, view.mask.length)} of ${view.mask.length}` : view.log.join(' · ') || 'Idle.'}</span>
      </div>
      {view.mask.length > 0 && <FrameStrip mask={view.mask} played={view.hit ? view.hit.played_before : player.frame} dropFrom={view.dropFrom} label={`Frames of the first response: ${view.hit ? `${view.hit.played_before} played, ${view.hit.dropped} dropped` : 'playing'}`} />}
      {view.hit && (
        <div className="tiles small">
          <div className="tile"><div className="num">{view.hit.played_before}</div><div className="cap">frames played before you cut in</div></div>
          <div className="tile"><div className="num">{view.hit.dropped}</div><div className="cap">unplayed frames dropped</div></div>
          <div className="tile"><div className="num">{view.hit.cancelled ? 'stop' : view.hit.turn.intent}</div><div className="cap">{view.hit.cancelled ? 'playback cancelled, no new reply' : `new reply: “${view.hit.turn.response}”`}</div></div>
          <div className="tile"><div className="num">{view.ctx?.last_city ?? '–'}</div><div className="cap">remembered city after the barge-in</div></div>
        </div>
      )}
      <h3 style={{ marginTop: 24 }}>Recorded scenarios A1 to A3 <span className="pill warn">{RECORDED}</span></h3>
      <div className="scroll-x">
        <table>
          <thead><tr><th>Scenario</th><th>First frames</th><th>Played</th><th>Dropped</th><th>Replayed here</th><th>Drop median µs</th><th>Drop p90 µs</th><th>Full median µs</th><th>Full p90 µs</th></tr></thead>
          <tbody>
            {replays.map(({ sc, total, hit, match, d }) => (
              <tr key={sc.scenario_id}><td><b>{sc.scenario_id}</b> <span className="hint">“{sc.first_transcript}” → “{sc.interrupt_transcript}”</span></td><td>{total}</td><td>{hit.played_before}</td><td>{hit.dropped}</td>
                <td className={match ? 'ok' : 'no'}>{match ? '✓ matches' : '✗ differs'}</td><td>{d.drop_us.median_us}</td><td>{d.drop_us.p90_us}</td><td>{d.full_us.median_us}</td><td>{d.full_us.p90_us}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="hint">{S.barge_in_frames_dropped} frames dropped across the three scenarios ({replays.map((r) => r.hit.dropped).join(' + ')}). The drop path is a list discard and a state change; the full path runs a whole new turn. Timings are the Python run, not your browser.</p>
    </section>
  );
}

function Noise() {
  const [text, setText] = useState(build.noise[3].transcript);
  const [sub, setSub] = useState(true);
  const [drop, setDrop] = useState(true);
  const ref = V.normalize(text);
  const heard = V.simulateAsr(text, { substitute: sub, drop });
  const wer = V.wordErrorRate(ref, heard);
  const clean = V.runTurn(text).intent, noisy = V.runTurn(heard).intent;
  const words = ref.split(' ').filter(Boolean);
  const W = 960, H = 220, pad = { l: 40, r: 10, t: 14, b: 30 };
  const ymax = Math.max(0.3, ...build.noise.map((r) => r.wer));
  const bw = (W - pad.l - pad.r) / build.noise.length;
  const y = (v) => pad.t + (1 - v / ymax) * (H - pad.t - pad.b);
  return (
    <section id="noise" className="card window reveal" data-title="simulate_asr — WER">
      <div className="head">
        <div>
          <p className="eyebrow">Live noise lab</p>
          <h2>One misheard word can <em>erase</em> the intent.</h2>
          <p className="sub">
            The repo&rsquo;s simulated ASR applies one deterministic error map: <span className="mono">weather → whether</span> and the word <span className="mono">the</span> is dropped.
            Switch each rule, type any transcript, and the word-level Levenshtein WER and the intent update live.
          </p>
        </div>
      </div>
      <div className="say">
        <div className="field grow"><label htmlFor="n-text">Transcript</label><input id="n-text" type="text" value={text} maxLength={160} onChange={(e) => setText(e.target.value)} /></div>
        <div className="field"><label htmlFor="n-case">Test case</label>
          <select id="n-case" value={build.noise.some((r) => r.transcript === text) ? text : ''} onChange={(e) => e.target.value && setText(e.target.value)}>
            <option value="">Custom</option>
            {build.noise.map((r) => <option key={r.case_id} value={r.transcript}>{r.case_id} · {r.transcript}</option>)}
          </select>
        </div>
      </div>
      <div className="chips">
        <label className="check"><input type="checkbox" checked={sub} onChange={(e) => setSub(e.target.checked)} /> weather → whether</label>
        <label className="check"><input type="checkbox" checked={drop} onChange={(e) => setDrop(e.target.checked)} /> drop “the”</label>
      </div>
      <div className="grid2" style={{ marginTop: 12 }}>
        <div>
          <h3>What the recognizer heard</h3>
          <p className="words">
            {words.map((w, i) => (drop && w === 'the') ? <s key={i}>{w}</s> : (sub && w === 'weather') ? <mark key={i}>whether</mark> : <span key={i}>{w}</span>)}
          </p>
        </div>
        <div className="tiles small two">
          <div className="tile"><div className="num">{wer.toFixed(4)}</div><div className="cap">word error rate (edits ÷ {words.length} reference words)</div></div>
          <div className="tile"><div className="num">{noisy}</div><div className="cap">intent through noise (clean: {clean}) {clean !== noisy ? <span className="pill bad">flipped</span> : <span className="pill good">survived</span>}</div></div>
        </div>
      </div>
      <h3 style={{ marginTop: 20 }}>Recorded WER for all {build.noise.length} Build cases <span className="pill warn">recorded</span></h3>
      <div className="scroll-x">
        <svg className="chart wide" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Bar chart of word error rate per case, mean ${build.summary.noise_mean_wer}`}>
          {Array.from({ length: Math.floor(ymax * 10 + 1e-9) + 1 }, (_, i) => i / 10).map((t) => <g key={t}><line className="axis" x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} /><text x={pad.l - 6} y={y(t) + 4} textAnchor="end">{t.toFixed(1)}</text></g>)}
          <line x1={pad.l} x2={W - pad.r} y1={y(build.summary.noise_mean_wer)} y2={y(build.summary.noise_mean_wer)} stroke="var(--text)" strokeDasharray="5 4" opacity="0.6" />
          <text x={W - pad.r} y={y(build.summary.noise_mean_wer) - 6} textAnchor="end">mean {build.summary.noise_mean_wer}</text>
          {build.noise.map((r, i) => (
            <g key={r.case_id} onClick={() => setText(r.transcript)} style={{ cursor: 'pointer' }}>
              <rect x={pad.l + i * bw + 4} y={y(r.wer)} width={bw - 8} height={Math.max(1, y(0) - y(r.wer))} rx="3" fill={r.intent_correct ? 'var(--primary)' : 'var(--bad)'} opacity={r.transcript === text ? 1 : 0.7} />
              <text x={pad.l + i * bw + bw / 2} y={H - 10} textAnchor="middle">{r.case_id.slice(1)}</text>
            </g>
          ))}
        </svg>
      </div>
      <div className="legend"><span><i style={{ background: 'var(--primary)' }} />intent survived</span><span><i style={{ background: 'var(--bad)' }} />intent lost ({build.noise.filter((r) => !r.intent_correct).map((r) => r.case_id).join(', ')})</span><span>{build.summary.noise_intent_correct}/{build.summary.noise_cases} survive · click a bar to load it</span></div>
    </section>
  );
}

function Budget() {
  const [stat, setStat] = useState('median_us');
  const [hover, setHover] = useState(null);
  const rows = deep.cases.map((c) => ({ c, parts: D.STAGES.map((s) => c.stage_us[s][stat]) }));
  const totals = rows.map((r) => r.parts.reduce((a, b) => a + b, 0));
  const xmax = Math.max(deep.budget_us * 1.15, ...totals);
  const W = 960, rowH = 22, pad = { l: 46, r: 16, t: 8, b: 28 }, H = pad.t + rows.length * rowH + pad.b;
  const x = (us) => pad.l + (us / xmax) * (W - pad.l - pad.r);
  const breaches = D.tailBreaches(deep, stat);
  const ticks = Array.from({ length: Math.floor(xmax / 50000) + 1 }, (_, i) => i * 50000);
  const statLabel = { median_us: 'median', p90_us: 'p90', p99_us: 'p99' }[stat];
  return (
    <section id="budget" className="card window reveal" data-title="latency_lab.py — Budget">
      <div className="head">
        <div>
          <p className="eyebrow">Recorded replay</p>
          <h2>Where every <em>microsecond</em> goes.</h2>
          <p className="sub">
            Each bar is one test turn: the four measured stage timings stacked against the {ms(deep.budget_us, 0)} ms budget set in DEEP-SPEC.md before measuring.
            At the median every turn fits. Switch to p90 or p99 and the tails of the synthesis loop on a shared VM break through.
          </p>
        </div>
        <div className="seg" role="group" aria-label="Statistic">
          {[['median_us', 'Median'], ['p90_us', 'p90'], ['p99_us', 'p99']].map(([k, l]) => <button key={k} type="button" aria-pressed={stat === k} onClick={() => setStat(k)}>{l}</button>)}
        </div>
      </div>
      <div className="legend" style={{ marginBottom: 10 }}>
        {D.STAGES.map((s) => <span key={s}><i style={{ background: STAGE_META[s][1] }} />{STAGE_META[s][0]} · design share {ms(DESIGN[s], 0)} ms</span>)}
        <span className="pill warn">{RECORDED}</span>
      </div>
      <div className="scroll-x">
        <svg className="chart wide" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Stacked bars of per-stage ${statLabel} latency for ${N} turns against a ${ms(deep.budget_us, 0)} ms budget`} onMouseLeave={() => setHover(null)}>
          {ticks.map((t) => <g key={t}><line className="axis" x1={x(t)} x2={x(t)} y1={pad.t} y2={H - pad.b} /><text x={x(t)} y={H - 10} textAnchor="middle">{ms(t, 0)} ms</text></g>)}
          {rows.map(({ c, parts }, i) => {
            let acc = 0;
            return (
              <g key={c.case_id} onMouseEnter={() => setHover({ c, parts, total: totals[i] })}>
                <rect x={0} y={pad.t + i * rowH} width={W} height={rowH} fill="transparent" />
                <text x={pad.l - 8} y={pad.t + i * rowH + 15} textAnchor="end">{c.case_id}</text>
                {parts.map((v, k) => { const r = <rect key={k} x={x(acc)} y={pad.t + i * rowH + 4} width={Math.max(0.5, x(acc + v) - x(acc))} height={rowH - 8} fill={STAGE_META[D.STAGES[k]][1]} opacity={hover && hover.c !== c ? 0.35 : 0.9} />; acc += v; return r; })}
              </g>
            );
          })}
          <line x1={x(deep.budget_us)} x2={x(deep.budget_us)} y1={pad.t - 4} y2={H - pad.b} stroke="var(--text)" strokeWidth="2" strokeDasharray="6 4" />
          <text x={x(deep.budget_us) + 6} y={pad.t + 10} style={{ fill: 'var(--text)' }}>budget {ms(deep.budget_us, 0)} ms</text>
        </svg>
      </div>
      <div className="tip" aria-live="polite">
        {hover ? <><b>{hover.c.case_id}</b> “{hover.c.transcript}”: {D.STAGES.map((s, k) => `${STAGE_META[s][0]} ${ms(hover.parts[k], 3)} ms`).join(' · ')} · total {ms(hover.total, 2)} ms</> : 'Hover a bar to read its stages.'}
      </div>
      <div className="bars" style={{ marginTop: 12 }}>
        <div className="bar-row">
          <div className="lab"><span>Turns whose summed {statLabel}s exceed the budget</span><b>{breaches} of {N}</b></div>
          <div className="track"><div className="fill" style={{ width: `${(breaches / N) * 100}%`, background: breaches ? 'var(--bad)' : 'var(--good)' }} /></div>
        </div>
      </div>
      <p className="hint">The summed p90 and p99 bars add per-stage tails, which overstates a true turn tail; they show how fragile a median-only verdict is. Largest WAV p99: {ms(Math.max(...deep.cases.map((c) => c.stage_us.wav_synthesis.p99_us)), 1)} ms.</p>
    </section>
  );
}

function Cloud() {
  const [c, setC] = useState(CLOUD0);
  const set = (k) => (v) => setC((o) => ({ ...o, [k]: v }));
  const rows = deep.cases.map((r) => { const total = V.modelledCloudMs(c, V.wordCount(r.response)); return { r, total, local: r.total_median_us / 1000, ratio: D.cloudRatio(total, r.total_median_us) }; });
  const meanCloud = rows.reduce((a, x) => a + x.total, 0) / rows.length;
  const ratios = rows.map((x) => x.ratio);
  const W = 960, rowH = 20, pad = { l: 46, r: 20, t: 10, b: 30 }, H = pad.t + rows.length * rowH + pad.b;
  const lo = -0.3, hi = Math.max(3.7, Math.log10(Math.max(...rows.map((x) => x.total)) * 1.2));
  const x = (v) => pad.l + ((Math.log10(Math.max(v, 0.5)) - lo) / (hi - lo)) * (W - pad.l - pad.r);
  const isDefault = Object.keys(CLOUD0).every((k) => c[k] === CLOUD0[k]);
  return (
    <section id="cloud" className="card window reveal" data-title="cloud_model — Modelled">
      <div className="head">
        <div>
          <p className="eyebrow">Live calculator over recorded local data</p>
          <h2>Local compute is not the problem. The <em>modelled</em> cloud steps are.</h2>
          <p className="sub">
            The repo never called a cloud service. It writes down five constants and the formula from <a href={blob('level-3-deep/latency_lab.py')}>latency_lab.py</a>:
            network + ASR + LLM + TTS base + TTS per word × words. Move them and the modelled totals and ratios recompute against the recorded local medians.
          </p>
        </div>
        <span className="pill bad">modelled, never measured</span>
      </div>
      <div className="controls">
        <Range label="Network round trip" value={c.rtt} min={0} max={400} step={5} onChange={set('rtt')} show={`${c.rtt} ms`} />
        <Range label="ASR final result" value={c.asr} min={0} max={1000} step={10} onChange={set('asr')} show={`${c.asr} ms`} />
        <Range label="LLM answer" value={c.llm} min={0} max={2000} step={10} onChange={set('llm')} show={`${c.llm} ms`} />
        <Range label="TTS base" value={c.base} min={0} max={500} step={5} onChange={set('base')} show={`${c.base} ms`} />
        <Range label="TTS per word" value={c.perWord} min={0} max={50} step={1} onChange={set('perWord')} show={`${c.perWord} ms`} />
      </div>
      <div className="actions" style={{ marginTop: 0, marginBottom: 12 }}>
        <button className="btn ghost" type="button" onClick={() => setC(CLOUD0)} disabled={isDefault}>Reset to the repo&rsquo;s constants</button>
        <span className="hint">{isDefault ? `Defaults are read from results_deep.json; mean ${meanCloud} ms matches the recorded ${S.modelled_cloud_mean_ms} ms.` : 'Your what-if: still a model, not a measurement.'}</span>
      </div>
      <div className="tiles small">
        <div className="tile"><div className="num">{+meanCloud.toFixed(2)} ms</div><div className="cap">mean modelled cloud turn</div></div>
        <div className="tile"><div className="num">{ms(S.median_total_median_us)} ms</div><div className="cap">median measured local turn ({REC.machine})</div></div>
        <div className="tile"><div className="num">{Math.min(...ratios).toFixed(1)}×</div><div className="cap">smallest modelled ÷ local ratio</div></div>
        <div className="tile"><div className="num">{Math.max(...ratios).toFixed(0)}×</div><div className="cap">largest modelled ÷ local ratio</div></div>
      </div>
      <div className="scroll-x" style={{ marginTop: 16 }}>
        <svg className="chart wide" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Per-turn measured local total against modelled cloud total, log scale in milliseconds">
          {[1, 10, 100, 1000].filter((t) => Math.log10(t) <= hi).map((t) => <g key={t}><line className="axis" x1={x(t)} x2={x(t)} y1={pad.t} y2={H - pad.b} /><text x={x(t)} y={H - 10} textAnchor="middle">{t >= 1000 ? `${t / 1000} s` : `${t} ms`}</text></g>)}
          {rows.map(({ r, total, local }, i) => {
            const yy = pad.t + i * rowH + rowH / 2;
            return (
              <g key={r.case_id}>
                <text x={pad.l - 8} y={yy + 4} textAnchor="end">{r.case_id}</text>
                <line x1={x(local)} x2={x(total)} y1={yy} y2={yy} stroke="var(--grid)" strokeWidth="3" />
                <circle cx={x(local)} cy={yy} r="5" fill="var(--primary)" />
                <rect x={x(total) - 5} y={yy - 5} width="10" height="10" fill="none" stroke="var(--bad)" strokeWidth="2" strokeDasharray="2 1.5" />
              </g>
            );
          })}
        </svg>
      </div>
      <div className="legend"><span><i style={{ background: 'var(--primary)', borderRadius: '50%' }} />measured local, sum of stage medians ({RECORDED})</span><span><i style={{ border: '2px dashed var(--bad)', background: 'transparent' }} />modelled cloud, from your constants</span></div>
    </section>
  );
}

function Scaling() {
  const pts = deep.cases.map((c) => ({ id: c.case_id, w: c.size.words, us: c.stage_us.wav_synthesis.median_us }));
  const W = 960, H = 300, pad = { l: 52, r: 16, t: 14, b: 34 };
  const xmax = Math.ceil(CROSS.crossing / 10) * 10 + 5, ymax = deep.budget_us * 1.15;
  const x = (w) => pad.l + (w / xmax) * (W - pad.l - pad.r);
  const y = (us) => pad.t + (1 - us / ymax) * (H - pad.t - pad.b);
  const [pick, setPick] = useState(deep.cases.reduce((m, c) => (c.size.words > m.size.words ? c : m)).case_id);
  const [timing, setTiming] = useState(null);
  const runStopwatch = () => {
    const resp = deep.cases.find((c) => c.case_id === pick).response;
    const first = resp.split(/\s+/)[0];
    // Browsers coarsen performance.now(), so each of the 30 samples times enough repeats to last about 2 ms.
    const med = (fn) => {
      let reps = 1;
      for (let a = performance.now(); performance.now() - a < 2; reps++) fn();
      const t = [];
      for (let i = 0; i < 30; i++) { const a = performance.now(); for (let r = 0; r < reps; r++) fn(); t.push((performance.now() - a) / reps); }
      t.sort((p, q) => p - q);
      return (t[14] + t[15]) / 2;
    };
    med(() => V.synthesizeSamples(resp));
    setTiming({ id: pick, words: V.wordCount(resp), full: med(() => V.synthesizeSamples(resp)), head: med(() => V.synthesizeSamples(first)) });
  };
  return (
    <section id="scaling" className="card window reveal" data-title="synthesize_wav — Scaling">
      <div className="head">
        <div>
          <p className="eyebrow">Recorded · plus an extrapolation</p>
          <h2>Longer replies cost <em>linearly</em> more, because the whole reply is synthesized first.</h2>
          <p className="sub">
            WAV synthesis median against response length for the {N} turns. At the rate of the longest reply ({CROSS.caseId}: {ms(CROSS.perWordUs, 2)} ms per word),
            a reply of about {Math.round(CROSS.crossing)} words would cross the budget on synthesis alone. That line is arithmetic on one case, labelled as such.
          </p>
        </div>
        <span className="pill warn">{RECORDED}</span>
      </div>
      <div className="scroll-x">
        <svg className="chart wide" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Scatter of response words against WAV synthesis median, with a one-case extrapolation to the budget">
          {[0, 25000, 50000, 75000, 100000].map((t) => <g key={t}><line className="axis" x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} /><text x={pad.l - 6} y={y(t) + 4} textAnchor="end">{ms(t, 0)} ms</text></g>)}
          {Array.from({ length: Math.floor(xmax / 10) + 1 }, (_, i) => i * 10).map((t) => <text key={t} x={x(t)} y={H - 12} textAnchor="middle">{t}</text>)}
          <text x={W - pad.r} y={H - 12 - 14} textAnchor="end">response words</text>
          <line x1={pad.l} x2={W - pad.r} y1={y(deep.budget_us)} y2={y(deep.budget_us)} stroke="var(--text)" strokeWidth="1.5" strokeDasharray="6 4" />
          <text x={pad.l + 6} y={y(deep.budget_us) - 6} style={{ fill: 'var(--text)' }}>budget {ms(deep.budget_us, 0)} ms</text>
          <line x1={x(0)} y1={y(0)} x2={x(CROSS.crossing)} y2={y(deep.budget_us)} stroke="var(--warn)" strokeWidth="2" strokeDasharray="3 4" />
          <circle cx={x(CROSS.crossing)} cy={y(deep.budget_us)} r="5" fill="none" stroke="var(--warn)" strokeWidth="2" />
          <text x={x(CROSS.crossing) - 8} y={y(deep.budget_us) + 18} textAnchor="end" style={{ fill: 'var(--warn)' }}>extrapolation: ≈{Math.round(CROSS.crossing)} words</text>
          {pts.map((p) => <circle key={p.id} cx={x(p.w)} cy={y(p.us)} r="5.5" fill="var(--primary)" opacity="0.85"><title>{`${p.id}: ${p.w} words, ${ms(p.us, 3)} ms`}</title></circle>)}
        </svg>
      </div>
      <div className="stopwatch">
        <div>
          <h3>Optional: time the JS synthesizer on your device</h3>
          <p className="hint">Synthesis of the whole reply against the first word only (the first 6 frames you would hear with streaming). Measured in this browser, in JavaScript; not comparable with the Python numbers above.</p>
        </div>
        <div className="say">
          <div className="field"><label htmlFor="sw-case">Reply to time</label>
            <select id="sw-case" value={pick} onChange={(e) => setPick(e.target.value)}>
              {deep.cases.map((c) => <option key={c.case_id} value={c.case_id}>{c.case_id} · {c.size.words} words</option>)}
            </select>
          </div>
          <button className="btn ghost" type="button" onClick={runStopwatch}>Run stopwatch</button>
        </div>
        <p className="tip" aria-live="polite">{timing ? <>Your browser, {timing.id} ({timing.words} words): whole reply {timing.full.toFixed(3)} ms, first word {timing.head.toFixed(3)} ms (median of 30). <span className="pill info">browser measurement</span></> : 'Not run yet.'}</p>
      </div>
    </section>
  );
}

function Probes() {
  const rr = probes.repeated_runs, tt = probes.time_to_first_word, pp = probes.paraphrase;
  const sp = rr.spread.median_total_median_us;
  const W = 480, H = 280, pad = { l: 44, r: 10, t: 12, b: 30 };
  const wmax = Math.max(...tt.cases.map((c) => c.words)) + 1;
  const ymax = Math.max(...tt.cases.map((c) => c.full_median_us)) * 1.1;
  const x = (w) => pad.l + (w / wmax) * (W - pad.l - pad.r);
  const y = (us) => pad.t + (1 - us / ymax) * (H - pad.t - pad.b);
  const yt = [0, 0.25, 0.5, 0.75, 1].map((f) => f * ymax);
  return (
    <section id="probes" className="card window reveal" data-title="run_probes.py — Probes">
      <div className="head">
        <div>
          <p className="eyebrow">Recorded add-on probes</p>
          <h2>Three cheap checks on the study&rsquo;s <em>weak spots</em>.</h2>
          <p className="sub">
            Repeated runs (is the median stable between runs?), time to first word (what would streaming synthesis save?), and a held-out paraphrase set (does the rule generalise?).
            These ran on a different machine from the Deep study, <span className="mono">{probes.machine.machine}</span>, Python {probes.machine.python}, so compare shapes, not absolute times.
          </p>
        </div>
        <span className="pill warn">recorded · {probes.machine.machine}</span>
      </div>
      <div className="grid2">
        <div>
          <h3>Repeated runs: {rr.runs} full re-measurements</h3>
          <div className="scroll-x">
            <table>
              <thead><tr><th>Run</th><th>Median turn ms</th><th>Mean turn ms</th><th>WAV share</th><th>Synthesis largest</th></tr></thead>
              <tbody>{rr.per_run.map((r, i) => <tr key={i}><td>{i + 1}</td><td>{ms(r.median_total_median_us, 3)}</td><td>{ms(r.mean_total_median_us, 3)}</td><td>{pct(r.wav_share_of_mean_total, 1)}</td><td>{r.dominant_stage_cases}/{N}</td></tr>)}</tbody>
            </table>
          </div>
          <p className="hint">Median turn spread {ms(sp.min, 3)} to {ms(sp.max, 3)} ms (sd {sp.stdev} µs). The stage ordering held in every run; one machine only, so this is between-run, not between-machine, variance.</p>
        </div>
        <div>
          <h3>Time to first word: median whole reply is {tt.median_full_over_first}× the first word</h3>
          <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Whole-reply against first-word synthesis median by response length">
            {yt.map((t) => <g key={t}><line className="axis" x1={pad.l} x2={W - pad.r} y1={y(t)} y2={y(t)} /><text x={pad.l - 8} y={y(t) + 4} textAnchor="end">{ms(t, 1)}</text></g>)}
            {tt.cases.map((c) => <g key={c.case_id}><line x1={x(c.words)} x2={x(c.words)} y1={y(c.first_word_median_us)} y2={y(c.full_median_us)} stroke="var(--grid)" strokeWidth="3" /><circle cx={x(c.words)} cy={y(c.full_median_us)} r="5" fill="var(--primary)" /><circle cx={x(c.words)} cy={y(c.first_word_median_us)} r="5" fill="var(--good)" /></g>)}
            <text x={W - pad.r} y={H - 4} textAnchor="end">response words → · ms ↑</text>
          </svg>
          <div className="legend"><span><i style={{ background: 'var(--primary)' }} />whole reply</span><span><i style={{ background: 'var(--good)' }} />first word only</span></div>
        </div>
      </div>
      <h3 style={{ marginTop: 20 }}>Held-out paraphrases: {pp.intent_correct} of {pp.n} understood, {pp.fell_to_unknown} fell to unknown</h3>
      <div className="para">
        {pp.cases.map((c) => (
          <div key={c.case_id} className={`pcase ${c.intent_correct ? 'hit' : 'miss'}`}>
            <span className="mono">{c.case_id}</span> “{c.transcript}”
            <small>wanted {c.expected_intent} · got <b>{c.intent}</b></small>
          </div>
        ))}
      </div>
      <p className="hint">The 100% scores on the authored sets come from a rule written for those sets. On rewordings it misses most of the time: an honest negative result on generalisation.</p>
    </section>
  );
}

// "Title: rest" bullets get a bold title; bullets without a short title stay plain.
function Titled({ text }) {
  const i = text.indexOf(': ');
  return i > 0 && i < 60 ? <li><b>{text.slice(0, i)}.</b> {text.charAt(i + 2).toUpperCase() + text.slice(i + 3)}</li> : <li>{text}</li>;
}

function Grades() {
  const backlog = D.parseBacklog(roadmapMd);
  return (
    <section id="grades" className="card window reveal" data-title="GRADES.md">
      <p className="eyebrow">Grades, deductions and limits</p>
      <h2>Graded by its own README, with every <em>deduction</em> named.</h2>
      <div className="grades">
        {LEVELS.map(([name, dir, L]) => (
          <div className="tile" key={name}>
            <div className="head" style={{ marginBottom: 4 }}><h3>{name}</h3><a className="hint" href={blob(`${dir}/README.md`)}>README ↗</a></div>
            <div className="num">{L.grade.toLocaleString('en-US')}<small> / 10,000</small></div>
            <ul className="ded">{L.deductions.map((d) => <li key={d.text}><b>−{d.points}</b> {d.text}</li>)}</ul>
          </div>
        ))}
      </div>
      <div className="grid2" style={{ marginTop: 20 }}>
        <div>
          <h3>Failure modes and limits (Deep)</h3>
          <ul className="limits">{DEEP_README.failures.map((f) => <Titled key={f} text={f} />)}</ul>
        </div>
        <div>
          <h3>v1.1 backlog (ROADMAP.md, none claimed done)</h3>
          <ol className="limits">{backlog.map((b) => <Titled key={b.title} text={b.text ? `${b.title}: ${b.text}` : b.title} />)}</ol>
        </div>
      </div>
    </section>
  );
}

function Reproduce() {
  const docs = [
    ['SPEC.md', 'Spec', 'Scope and acceptance criteria'],
    ['level-3-deep/DEEP-SPEC.md', 'Deep spec', 'Budget set before measuring'],
    ['docs/research-review.md', 'Research review', 'PhD-rubric grade and gaps'],
    ['DOSSIER.md', 'Dossier', 'Past, present and future'],
    ['NOVELTY.md', 'Novelty', 'Proposed, draft'],
    ['ROADMAP.md', 'Roadmap', 'v1.1 backlog'],
  ];
  return (
    <section id="reproduce" className="card window reveal" data-title="Terminal — reproduce">
      <p className="eyebrow">Reproduce it</p>
      <h2>Standard library only. Every level reruns on a laptop.</h2>
      <ol className="steps" style={{ marginTop: 16 }}>
        <li><span className="n">1</span><div><b>Run the tests</b><div className="hint"><code>python -m unittest discover -s tests -v && python tests/test_smoke.py</code></div></div></li>
        <li><span className="n">2</span><div><b>Rerun the levels</b><div className="hint"><code>python level-2-build/run_build.py && python level-3-deep/run_deep.py && python level-3-deep/run_probes.py</code></div></div></li>
        <li><span className="n">3</span><div><b>Check Build is byte-identical</b><div className="hint">results_build.json holds no timing, so its sha256 must start <code>{D.shaPrefix(buildMd)}</code>. The Deep and probe files carry timings and vary by run and machine.</div></div></li>
        <li><span className="n">4</span><div><b>Rebuild this page</b><div className="hint"><code>cd site && npm ci && npm run build</code> replays every case through the JS port first and stops on any mismatch.</div></div></li>
      </ol>
      <p className="hint" style={{ marginTop: 12 }}>CI runs every level on Python 3.11 and 3.12: <a href={`${REPO}/actions/workflows/ci.yml`}>CI status ↗</a></p>
      <div className="docs" style={{ marginTop: 16 }}>
        {docs.map(([p, t, d]) => <a key={p} href={blob(p)}><b>{t}</b><small>{d}</small></a>)}
      </div>
    </section>
  );
}
