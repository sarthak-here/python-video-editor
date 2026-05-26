// ── Tab switching ────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.panel).classList.add('active');
  });
});

// ── Toast ────────────────────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `show ${type}`;
  setTimeout(() => el.classList.remove('show'), 3500);
}

// ── Drop-zone labels ─────────────────────────────────────────────────────────
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

// ── Volume slider live label ─────────────────────────────────────────────────
const volSlider = document.getElementById('volume');
const volLabel  = document.getElementById('vol-label');
if (volSlider) {
  volSlider.addEventListener('input', () => {
    volLabel.textContent = parseFloat(volSlider.value).toFixed(1) + '×';
  });
}

// ── Generic form submit helper ───────────────────────────────────────────────
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
