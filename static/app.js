// ── Tab switching ─────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.panel).classList.add('active');
  });
});

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `show ${type}`;
  setTimeout(() => el.classList.remove('show'), 3500);
}

// ── Drop-zone labels ──────────────────────────────────────────────────────────
document.querySelectorAll('.drop-zone input[type=file]').forEach(input => {
  input.addEventListener('change', () => {
    const files = [...input.files].map(f => f.name).join(', ');
    input.closest('.drop-zone').querySelector('.dz-files').textContent = files || '';
  });
});

document.querySelectorAll('.drop-zone').forEach(zone => {
  zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop',      e => { e.preventDefault(); zone.classList.remove('dragover'); });
});

// ── Volume slider live label ──────────────────────────────────────────────────
const volSlider = document.getElementById('volume');
const volLabel  = document.getElementById('vol-label');
if (volSlider) {
  volSlider.addEventListener('input', () => {
    volLabel.textContent = parseFloat(volSlider.value).toFixed(1) + '×';
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// VideoPreview  —  frame-by-frame scrubber with In / Out point marking
// ═══════════════════════════════════════════════════════════════════════════════
class VideoPreview {
  /**
   * @param {object} opts
   * @param {HTMLElement} opts.container  – where the preview block is injected
   * @param {Function}    opts.onIn       – called with (seconds) when In is set
   * @param {Function}    opts.onOut      – called with (seconds) when Out is set
   */
  constructor({ container, onIn, onOut }) {
    this.container = container;
    this.onIn  = onIn  || (() => {});
    this.onOut = onOut || (() => {});

    this.fps      = 30;
    this.inPoint  = 0;
    this.outPoint = 0;
    this._active  = false;   // true when this panel's tab is shown

    this._buildDOM();
    this._bindEvents();
  }

  // ── DOM construction ────────────────────────────────────────────────────────
  _buildDOM() {
    const wrap = document.createElement('div');
    wrap.className = 'pv-wrap';
    wrap.style.display = 'none';
    wrap.innerHTML = `
      <div class="pv-header">
        <span class="pv-title">🎞️ Frame Preview</span>
        <div class="pv-header-right">
          <label class="pv-fps-label">FPS
            <select class="pv-fps">
              <option value="24">24</option>
              <option value="25">25</option>
              <option value="30" selected>30</option>
              <option value="60">60</option>
            </select>
          </label>
          <button class="pv-mute-btn" title="Toggle mute">🔊</button>
        </div>
      </div>

      <video class="pv-video"></video>

      <div class="pv-tl-outer">
        <div class="pv-tl" title="Click or drag to seek">
          <div class="pv-tl-range"></div>
          <div class="pv-tl-in"  title="In point"></div>
          <div class="pv-tl-out" title="Out point"></div>
          <div class="pv-tl-head"></div>
        </div>
        <div class="pv-tl-meta">
          <span class="pv-cur-time">0:00.000</span>
          <span class="pv-frame-info">Frame 0 / 0</span>
          <span class="pv-dur">0:00.000</span>
        </div>
      </div>

      <div class="pv-controls">
        <button class="btn btn-outline pv-prev" title="Previous frame (← arrow)">◀ Prev</button>
        <button class="btn btn-outline pv-play" title="Play / Pause (Space)">▶ Play</button>
        <button class="btn btn-outline pv-next" title="Next frame (→ arrow)">Next ▶</button>
      </div>

      <div class="pv-marks">
        <div class="pv-mark-side">
          <button class="btn pv-mark-in"  title="Set In at current frame">⬅ Mark In</button>
          <span class="pv-in-val  badge-in">0.000s</span>
        </div>
        <div class="pv-mark-middle">
          <span class="pv-range-dur"></span>
        </div>
        <div class="pv-mark-side pv-mark-side--right">
          <span class="pv-out-val badge-out">0.000s</span>
          <button class="btn pv-mark-out" title="Set Out at current frame">Mark Out ➡</button>
        </div>
      </div>

      <p class="pv-hint">← → arrow keys: step one frame &nbsp;·&nbsp; Space: play / pause &nbsp;·&nbsp; Click timeline to seek</p>
    `;

    // Cache refs
    this.wrap        = wrap;
    this.video       = wrap.querySelector('.pv-video');
    this.tl          = wrap.querySelector('.pv-tl');
    this.tlRange     = wrap.querySelector('.pv-tl-range');
    this.tlHead      = wrap.querySelector('.pv-tl-head');
    this.tlInM       = wrap.querySelector('.pv-tl-in');
    this.tlOutM      = wrap.querySelector('.pv-tl-out');
    this.curTimeEl   = wrap.querySelector('.pv-cur-time');
    this.durEl       = wrap.querySelector('.pv-dur');
    this.frameEl     = wrap.querySelector('.pv-frame-info');
    this.inValEl     = wrap.querySelector('.pv-in-val');
    this.outValEl    = wrap.querySelector('.pv-out-val');
    this.rangeDurEl  = wrap.querySelector('.pv-range-dur');
    this.playBtn     = wrap.querySelector('.pv-play');
    this.muteBtn     = wrap.querySelector('.pv-mute-btn');
    this.fpsSelect   = wrap.querySelector('.pv-fps');

    this.container.appendChild(wrap);
  }

  // ── Event binding ────────────────────────────────────────────────────────────
  _bindEvents() {
    const v = this.video;

    // FPS selector
    this.fpsSelect.addEventListener('change', () => {
      this.fps = parseInt(this.fpsSelect.value);
      this._updateUI();
    });

    // Mute toggle
    this.muteBtn.addEventListener('click', () => {
      v.muted = !v.muted;
      this.muteBtn.textContent = v.muted ? '🔇' : '🔊';
    });

    // Frame-step buttons
    this.wrap.querySelector('.pv-prev').addEventListener('click', () => this.stepFrame(-1));
    this.wrap.querySelector('.pv-next').addEventListener('click', () => this.stepFrame(1));

    // Play / pause
    this.playBtn.addEventListener('click', () => this.togglePlay());

    // Mark In / Out
    this.wrap.querySelector('.pv-mark-in') .addEventListener('click', () => this.markIn());
    this.wrap.querySelector('.pv-mark-out').addEventListener('click', () => this.markOut());

    // Video events
    v.addEventListener('timeupdate',     () => this._updateUI());
    v.addEventListener('loadedmetadata', () => {
      this.outPoint = v.duration;
      this.inPoint  = 0;
      this.fps      = parseInt(this.fpsSelect.value);
      this._updateUI();
    });
    v.addEventListener('play',  () => { this.playBtn.textContent = '⏸ Pause'; });
    v.addEventListener('pause', () => { this.playBtn.textContent = '▶ Play'; });
    v.addEventListener('ended', () => { this.playBtn.textContent = '▶ Play'; });

    // Timeline: click + drag to seek
    let dragging = false;
    const seek = e => {
      if (!v.duration) return;
      const rect = this.tl.getBoundingClientRect();
      const pct  = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      v.currentTime = pct * v.duration;
    };
    this.tl.addEventListener('mousedown', e => { dragging = true; seek(e); });
    document.addEventListener('mousemove', e => { if (dragging) seek(e); });
    document.addEventListener('mouseup',   () => { dragging = false; });

    // Touch support
    this.tl.addEventListener('touchstart', e => {
      seek({ clientX: e.touches[0].clientX });
    }, { passive: true });
    this.tl.addEventListener('touchmove', e => {
      seek({ clientX: e.touches[0].clientX });
    }, { passive: true });

    // Keyboard (only when this panel's tab is the active one)
    document.addEventListener('keydown', e => {
      if (!this._active || !v.src) return;
      const tag = document.activeElement.tagName;
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(tag)) return;
      if (e.key === 'ArrowLeft')  { e.preventDefault(); this.stepFrame(-1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); this.stepFrame(1); }
      if (e.key === ' ')          { e.preventDefault(); this.togglePlay(); }
      if (e.key === 'i')          { this.markIn(); }
      if (e.key === 'o')          { this.markOut(); }
    });
  }

  // ── Helpers ──────────────────────────────────────────────────────────────────
  _fmt(t) {
    if (!isFinite(t)) return '0:00.000';
    const m = Math.floor(t / 60);
    const s = (t % 60).toFixed(3).padStart(6, '0');
    return `${m}:${s}`;
  }

  _pctStr(t) {
    const dur = this.video.duration;
    return (dur && isFinite(dur)) ? ((t / dur) * 100).toFixed(3) + '%' : '0%';
  }

  _updateUI() {
    const v   = this.video;
    const dur = (v.duration && isFinite(v.duration)) ? v.duration : 0;
    const cur = v.currentTime || 0;

    // Time / frame display
    this.curTimeEl.textContent = this._fmt(cur);
    this.durEl.textContent     = this._fmt(dur);
    const frame = Math.round(cur * this.fps);
    const total = Math.round(dur * this.fps);
    this.frameEl.textContent   = `Frame ${frame} / ${total}`;

    // Playhead
    this.tlHead.style.left = this._pctStr(cur);

    // Range highlight + In/Out markers
    if (dur > 0) {
      const inPct  = (this.inPoint  / dur * 100).toFixed(3);
      const outPct = (this.outPoint / dur * 100).toFixed(3);
      this.tlRange.style.left  = inPct  + '%';
      this.tlRange.style.width = Math.max(0, outPct - inPct) + '%';
      this.tlInM .style.left   = inPct  + '%';
      this.tlOutM.style.left   = outPct + '%';
    }

    // Badge values
    this.inValEl .textContent = this.inPoint .toFixed(3) + 's';
    this.outValEl.textContent = this.outPoint.toFixed(3) + 's';

    // Selection duration
    const selDur = Math.max(0, this.outPoint - this.inPoint);
    this.rangeDurEl.textContent = selDur > 0 ? `⟵ ${selDur.toFixed(3)}s selected ⟶` : '';
  }

  // ── Public API ───────────────────────────────────────────────────────────────
  stepFrame(dir) {
    const v = this.video;
    if (!v.duration) return;
    v.pause();
    v.currentTime = Math.max(0, Math.min(v.duration, v.currentTime + dir / this.fps));
  }

  togglePlay() {
    if (this.video.paused) this.video.play();
    else this.video.pause();
  }

  markIn() {
    this.inPoint = this.video.currentTime;
    this._updateUI();
    this.onIn(this.inPoint);
  }

  markOut() {
    this.outPoint = this.video.currentTime;
    this._updateUI();
    this.onOut(this.outPoint);
  }

  /** Load a File object directly (no upload needed — uses createObjectURL). */
  loadFile(file) {
    const old = this.video.src;
    if (old && old.startsWith('blob:')) URL.revokeObjectURL(old);
    this.video.src = URL.createObjectURL(file);
    this.video.load();
    this.wrap.style.display = 'block';
    this.wrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  /** Tell the preview whether its parent tab is the focused one (for keyboard). */
  setActive(flag) { this._active = flag; }
}


// ═══════════════════════════════════════════════════════════════════════════════
// Wire VideoPreview to Trim and Add-Text panels
// ═══════════════════════════════════════════════════════════════════════════════
(function setupPreviews() {

  // ── helper: set a form field and flash it green ───────────────────────────
  function flashSet(selector, value) {
    const el = document.querySelector(selector);
    if (!el) return;
    el.value = value;
    el.classList.remove('field-flash');
    // force reflow so re-adding the class triggers the animation again
    void el.offsetWidth;
    el.classList.add('field-flash');
  }

  // ── Trim panel ────────────────────────────────────────────────────────────
  const trimForm = document.getElementById('form-trim');
  const trimPVSlot = document.createElement('div');
  // insert after the first form-group (the drop-zone row)
  const trimFirstGroup = trimForm.querySelector('.form-group');
  trimForm.insertBefore(trimPVSlot, trimFirstGroup.nextSibling);

  const trimPV = new VideoPreview({
    container: trimPVSlot,
    onIn:  t => flashSet('#form-trim [name=start]', t.toFixed(3)),
    onOut: t => flashSet('#form-trim [name=end]',   t.toFixed(3)),
  });
  trimPV.setActive(true);   // Trim is the default active tab

  document.querySelector('#form-trim [name=file]').addEventListener('change', function () {
    if (this.files[0]) trimPV.loadFile(this.files[0]);
  });

  // ── Add-Text panel ────────────────────────────────────────────────────────
  const textForm = document.getElementById('form-text');
  const textPVSlot = document.createElement('div');
  // insert after the first form-group (the drop-zone row)
  const textFirstGroup = textForm.querySelector('.form-group');
  textForm.insertBefore(textPVSlot, textFirstGroup.nextSibling);

  const textPV = new VideoPreview({
    container: textPVSlot,
    onIn:  t => flashSet('#form-text [name=start]', t.toFixed(3)),
    onOut: t => flashSet('#form-text [name=end]',   t.toFixed(3)),
  });

  document.querySelector('#form-text [name=file]').addEventListener('change', function () {
    if (this.files[0]) textPV.loadFile(this.files[0]);
  });

  // ── Keep setActive in sync with tab switching ─────────────────────────────
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      trimPV.setActive(btn.dataset.panel === 'panel-trim');
      textPV.setActive(btn.dataset.panel === 'panel-text');
    });
  });

})();


// ── Generic form submit helper ────────────────────────────────────────────────
async function submitForm(formId, endpoint, resultId, spinnerId) {
  const form    = document.getElementById(formId);
  const result  = document.getElementById(resultId);
  const spinner = document.getElementById(spinnerId);
  const btn     = form.querySelector('button[type=submit]');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    spinner.classList.add('show');
    result.classList.remove('show');
    btn.disabled = true;

    try {
      const res  = await fetch(endpoint, { method: 'POST', body: new FormData(form) });
      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || 'Server error');

      // fill result
      const video = result.querySelector('video');
      const dl    = result.querySelector('.dl-btn');
      if (video) { video.src = data.url; video.load(); }
      if (dl)    { dl.href = `/download/${data.filename}`; dl.download = data.filename; }

      result.classList.add('show');
      toast('Done! Your video is ready ✅');
    } catch (err) {
      toast('Error: ' + err.message, 'error');
    } finally {
      spinner.classList.remove('show');
      btn.disabled = false;
    }
  });
}

// Wire up all four forms
submitForm('form-trim',  '/trim',     'result-trim',  'spin-trim');
submitForm('form-merge', '/merge',    'result-merge', 'spin-merge');
submitForm('form-text',  '/add-text', 'result-text',  'spin-text');
submitForm('form-audio', '/audio',    'result-audio', 'spin-audio');
