const BACKEND_URL = "http://127.0.0.1:8000";

document.getElementById("scanBtn").addEventListener("click", async () => {
  const resultDiv = document.getElementById("result");
  const btn = document.getElementById("scanBtn");
  const badge = document.getElementById("riskBadge");

  btn.disabled = true;
  btn.textContent = "Scanning...";
  badge.innerHTML = "";
  resultDiv.innerHTML = `
    <div class="scanning">
      <div class="spinner"></div>
      <strong>Reading the fine print...</strong>
      <small>Gemini AI is analyzing clauses</small>
    </div>`;

  try {
    const screenshotUrl = await new Promise((resolve, reject) => {
      chrome.tabs.captureVisibleTab(null, { format: "png", quality: 100 }, (dataUrl) => {
        if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
        else resolve(dataUrl);
      });
    });

    const base64 = screenshotUrl.split(",")[1];
    const binary = atob(base64);
    const array = [];
    for (let i = 0; i < binary.length; i++) array.push(binary.charCodeAt(i));
    const blob = new Blob([new Uint8Array(array)], { type: "image/png" });

    const formData = new FormData();
    formData.append("file", blob, "screenshot.png");

    const res = await fetch(`${BACKEND_URL}/analyze`, { method: "POST", body: formData });
    if (!res.ok) throw new Error(`Server error ${res.status}`);

    const data = await res.json();
    displayResult(data);

  } catch (err) {
    resultDiv.innerHTML = `
      <div class="error-box">
        Connection failed
        <small>Make sure backend is running on port 8000</small>
      </div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "🔍 Scan Again";
  }
});

function displayResult(data) {
  const resultDiv = document.getElementById("result");
  const badge = document.getElementById("riskBadge");

  const score = data.trust_score;
  const scoreColor = score >= 70 ? "#22c55e" : score >= 40 ? "#f97316" : "#ef4444";
  const radius = 28;
  const circ = 2 * Math.PI * radius;
  const filled = (score / 100) * circ;

  const verdict = score >= 70 ? "LOW RISK" : score >= 40 ? "MEDIUM RISK" : "HIGH RISK";
  const badgeClass = score >= 70 ? "risk-low" : score >= 40 ? "risk-medium" : "risk-high";

  badge.innerHTML = `<span class="risk-badge ${badgeClass}">${verdict}</span>`;

  const dangerCount  = data.flags.filter(f => f.level === "danger").length;
  const warningCount = data.flags.filter(f => f.level === "warning").length;
  const safeCount    = data.flags.filter(f => f.level === "safe").length;

  let flagsHtml = "";
  data.flags.forEach(flag => {
    const tag = flag.level === "danger" ? "Danger" : flag.level === "warning" ? "Warning" : "Safe";
    flagsHtml += `
      <div class="flag ${flag.level}">
        <div class="flag-header">
          <div class="dot"></div>
          <div class="flag-title">${flag.clause}</div>
          <span class="flag-tag">${tag}</span>
        </div>
        <div class="flag-desc">${flag.explanation}</div>
      </div>`;
  });

  resultDiv.innerHTML = `
    <div style="margin-top:12px">
      <div class="score-card">
        <div class="score-ring">
          <svg width="72" height="72" viewBox="0 0 72 72">
            <circle cx="36" cy="36" r="${radius}" fill="none" stroke="#1e293b" stroke-width="7"/>
            <circle cx="36" cy="36" r="${radius}" fill="none" stroke="${scoreColor}" stroke-width="7"
              stroke-dasharray="${filled.toFixed(1)} ${circ.toFixed(1)}"
              stroke-linecap="round" transform="rotate(-90 36 36)"/>
          </svg>
          <div class="score-text">
            <div class="num" style="color:${scoreColor}">${score}</div>
            <div class="denom">/100</div>
          </div>
        </div>
        <div class="score-info">
          <h3>Trust Score</h3>
          <div class="badges">
            <span class="badge danger">${dangerCount} Danger</span>
            <span class="badge warning">${warningCount} Warning</span>
            <span class="badge safe">${safeCount} Safe</span>
          </div>
        </div>
      </div>

      <div class="summary">${data.summary}</div>

      <div class="section-label">Flagged Clauses</div>
      ${flagsHtml}
    </div>`;
}