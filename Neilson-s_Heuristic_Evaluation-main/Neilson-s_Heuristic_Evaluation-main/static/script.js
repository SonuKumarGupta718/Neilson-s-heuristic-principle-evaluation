let lastResults = null;

// Allow Enter key to trigger analysis
document.getElementById('urlInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') runAnalysis();
});

async function runAnalysis() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) return;

  const btn = document.getElementById('analyzeBtn');
  const btnText = document.getElementById('btnText');
  const btnSpinner = document.getElementById('btnSpinner');
  const errorMsg = document.getElementById('errorMsg');
  const scoreSection = document.getElementById('scoreSection');
  const resultsGrid = document.getElementById('resultsGrid');

  // Loading state
  btn.disabled = true;
  btnText.textContent = 'Analyzing...';
  btnSpinner.classList.remove('hidden');
  errorMsg.classList.add('hidden');
  scoreSection.classList.add('hidden');
  resultsGrid.classList.add('hidden');

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Analysis failed');

    lastResults = data;
    renderResults(data);
  } catch (err) {
    errorMsg.textContent = '⚠️ ' + err.message;
    errorMsg.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btnText.textContent = 'Analyze';
    btnSpinner.classList.add('hidden');
  }
}

function renderResults(data) {
  const { heuristics, score, url } = data;
  const passed = heuristics.filter(h => h.pass).length;
  const failed = heuristics.length - passed;

  // Score ring animation
  const circumference = 314;
  const offset = circumference - (score / 100) * circumference;
  const ring = document.getElementById('ringProgress');
  const scoreVal = document.getElementById('scoreValue');

  // Color ring by score
  if (score >= 70) ring.style.stroke = '#34d399';
  else if (score >= 40) ring.style.stroke = '#fbbf24';
  else ring.style.stroke = '#f87171';

  ring.style.strokeDashoffset = offset;

  // Animate score number
  animateCount(scoreVal, 0, score, 1200);

  document.getElementById('scoreDesc').textContent = scoreDescription(score);
  document.getElementById('passCount').textContent = `${passed} Passed`;
  document.getElementById('failCount').textContent = `${failed} Issues`;

  // Show score
  document.getElementById('scoreSection').classList.remove('hidden');

  // Render grid
  const grid = document.getElementById('resultsGrid');
  grid.innerHTML = '';
  heuristics.forEach((h, idx) => {
    const card = document.createElement('div');
    card.className = `result-card ${h.pass ? 'pass' : 'fail'}`;
    card.style.animationDelay = `${idx * 0.06}s`;
    card.innerHTML = `
      <div class="card-icon">${h.icon}</div>
      <div class="card-body">
        <div class="card-header">
          <span class="card-id">Heuristic #${h.id}</span>
          <span class="card-status ${h.pass ? 'status-pass' : 'status-fail'}">${h.pass ? '✓ Pass' : '✗ Issue'}</span>
        </div>
        <div class="card-title">${h.title}</div>
        <div class="card-result">${h.result}</div>
      </div>
    `;
    grid.appendChild(card);
  });
  grid.classList.remove('hidden');
}

function scoreDescription(score) {
  if (score >= 80) return 'Excellent usability — the site follows most heuristics well.';
  if (score >= 60) return 'Good usability with some areas for improvement.';
  if (score >= 40) return 'Moderate usability — several heuristics need attention.';
  return 'Poor usability — significant improvements are recommended.';
}

function animateCount(el, from, to, duration) {
  const start = performance.now();
  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + (to - from) * ease);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

async function exportPDF() {
  if (!lastResults) return;
  const res = await fetch('/export-pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lastResults)
  });
  if (!res.ok) { alert('Failed to export PDF'); return; }
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'heuristic_report.pdf';
  a.click();
}
