/**
 * Settings and Diagnostics Controller for VAANI.
 * Manages user preference persistence, live diagnostics rendering,
 * connectivity latency testing, and demo resets.
 */

let currentSettings = {};

function switchSettingsTab(tabName) {
  const shopTab = document.getElementById("tabShopkeeper");
  const diagTab = document.getElementById("tabDiagnostics");
  const btnShop = document.getElementById("tabBtnShopkeeper");
  const btnDiag = document.getElementById("tabBtnDiagnostics");

  if (tabName === "shopkeeper") {
    shopTab.classList.add("active");
    diagTab.classList.remove("active");
    btnShop.classList.add("active");
    btnDiag.classList.remove("active");
  } else {
    diagTab.classList.add("active");
    shopTab.classList.remove("active");
    btnDiag.classList.add("active");
    btnShop.classList.remove("active");
    loadDiagnostics();
  }
}

function showToast(message, isError = false) {
  const toast = document.getElementById("toastMsg");
  const icon = document.getElementById("toastIcon");
  const text = document.getElementById("toastText");

  icon.textContent = isError ? "⚠️" : "✓";
  text.textContent = message;
  toast.style.background = isError ? "#B71C1C" : "var(--aubergine)";
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3200);
}

async function loadSettings() {
  try {
    const res = await fetch("/api/v1/settings");
    if (!res.ok) throw new Error("Failed to load settings");
    currentSettings = await res.json();

    if (currentSettings.language) document.getElementById("prefLanguage").value = currentSettings.language;
    if (currentSettings.voice_hi) document.getElementById("prefVoice").value = currentSettings.voice_hi;
    if (currentSettings.speech_rate) document.getElementById("prefRate").value = currentSettings.speech_rate;
    if (currentSettings.confirm_threshold) document.getElementById("prefConfirmThreshold").value = currentSettings.confirm_threshold;
    if (currentSettings.snooze_duration_mins) document.getElementById("prefSnooze").value = currentSettings.snooze_duration_mins;
    if (currentSettings.privacy_mode) document.getElementById("prefPrivacy").value = currentSettings.privacy_mode;

    const isDemo = currentSettings.demo_mode === "true" || currentSettings.demo_mode === true;
    const demoIndicator = document.getElementById("demoModeIndicator");
    const demoText = document.getElementById("demoModeText");
    if (demoIndicator && demoText) {
      demoText.textContent = isDemo ? "Demo Mode: ON" : "Production Mode";
      demoIndicator.style.background = isDemo ? "#E8F5E9" : "var(--ice-50)";
    }
  } catch (err) {
    console.error("Error loading settings:", err);
  }
}

async function saveShopkeeperSettings() {
  const payload = {
    settings: {
      language: document.getElementById("prefLanguage").value,
      voice_hi: document.getElementById("prefVoice").value,
      voice_mr: document.getElementById("prefVoice").value,
      voice_en: document.getElementById("prefVoice").value,
      speech_rate: document.getElementById("prefRate").value,
      confirm_threshold: document.getElementById("prefConfirmThreshold").value,
      snooze_duration_mins: document.getElementById("prefSnooze").value,
      privacy_mode: document.getElementById("prefPrivacy").value
    }
  };

  try {
    const res = await fetch("/api/v1/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error("Could not update settings");
    showToast("Preferences saved successfully!");
  } catch (err) {
    showToast("Error saving preferences: " + err.message, true);
  }
}

async function loadDiagnostics() {
  try {
    const res = await fetch("/api/v1/settings/diagnostics");
    if (!res.ok) throw new Error("Failed to load diagnostics");
    const data = await res.json();

    // AI Readiness - STT
    const stt = data.ai_readiness.stt;
    const badgeStt = document.getElementById("badgeStt");
    const sttMode = document.getElementById("sttMode");
    const sttKey = document.getElementById("sttKey");
    sttMode.textContent = stt.mode.toUpperCase();
    sttKey.textContent = data.masked_credentials.GNANI_API_KEY || "Not Configured";
    if (stt.configured) {
      badgeStt.className = "status-badge live";
      badgeStt.textContent = "Live Cloud";
    } else {
      badgeStt.className = "status-badge fallback";
      badgeStt.textContent = "Web Speech Fallback";
    }

    // AI Readiness - Intent
    const evon = data.ai_readiness.intent_understanding;
    const badgeIntent = document.getElementById("badgeIntent");
    const intentMode = document.getElementById("intentMode");
    const intentKey = document.getElementById("intentKey");
    intentMode.textContent = evon.mode.toUpperCase();
    intentKey.textContent = data.masked_credentials.EVON_API_KEY || "Not Configured";
    if (evon.configured) {
      badgeIntent.className = "status-badge live";
      badgeIntent.textContent = "Live Evon v3.3";
    } else {
      badgeIntent.className = "status-badge fallback";
      badgeIntent.textContent = "Deterministic Rules Active";
    }

    // AI Readiness - TTS
    const tts = data.ai_readiness.tts;
    const badgeTts = document.getElementById("badgeTts");
    const ttsMode = document.getElementById("ttsMode");
    ttsMode.textContent = tts.mode.toUpperCase();
    if (tts.configured) {
      badgeTts.className = "status-badge live";
      badgeTts.textContent = "Live Timbre v2.5";
    } else {
      badgeTts.className = "status-badge fallback";
      badgeTts.textContent = "Browser Web Speech Fallback";
    }

    // Market Feed
    const market = data.ai_readiness.market_data;
    const badgeMarket = document.getElementById("badgeMarket");
    const marketSource = document.getElementById("marketSource");
    marketSource.textContent = market.provider.toUpperCase();
    if (market.is_sample) {
      badgeMarket.className = "status-badge sample";
      badgeMarket.textContent = "Sample Fixture Data";
    } else {
      badgeMarket.className = "status-badge live";
      badgeMarket.textContent = "Live Feeds";
    }

    // Database Architecture
    const db = data.database;
    const badgeDbWal = document.getElementById("badgeDbWal");
    const dbPathVal = document.getElementById("dbPathVal");
    const dbFkStatus = document.getElementById("dbFkStatus");
    if (db.wal_mode) {
      badgeDbWal.className = "status-badge live";
      badgeDbWal.textContent = "WAL Mode Active (" + db.journal_mode.toUpperCase() + ")";
    } else {
      badgeDbWal.className = "status-badge fallback";
      badgeDbWal.textContent = db.journal_mode.toUpperCase();
    }
    dbPathVal.textContent = db.path;
    dbFkStatus.textContent = db.foreign_keys ? "Enforced (ON)" : "Disabled (OFF)";
    dbFkStatus.style.color = db.foreign_keys ? "#2E7D32" : "#B71C1C";

    // Row Counts
    const counts = db.row_counts || {};
    document.getElementById("cntCustomers").textContent = counts.customers ?? 0;
    document.getElementById("cntEntries").textContent = counts.ledger_entries ?? 0;
    document.getElementById("cntPrescriptions").textContent = counts.prescriptions ?? 0;
    document.getElementById("cntReminders").textContent = counts.reminders ?? 0;
    document.getElementById("cntWatchlist").textContent = counts.watchlist ?? 0;

  } catch (err) {
    console.error("Error loading diagnostics:", err);
  }
}

async function runConnectivityTest() {
  const btn = document.getElementById("btnTestConn");
  const resBox = document.getElementById("connectivityResult");
  btn.disabled = true;
  btn.textContent = "Testing...";
  resBox.style.display = "block";
  resBox.textContent = "Pinging SQLite database, Yahoo Finance market feed, and AI services...";

  try {
    const res = await fetch("/api/v1/settings/test-connectivity", { method: "POST" });
    if (!res.ok) throw new Error("Connectivity ping failed");
    const data = await res.json();
    const db = data.results.database;
    const mkt = data.results.market_data;
    const ai = data.results.ai_services;

    resBox.innerHTML = `
      <div style="padding: 10px; background: #FFFFFF; border: 1px solid var(--border); border-radius: 4px; margin-top: 8px;">
        <div><strong>Database:</strong> ${db.status.toUpperCase()} (${db.latency_ms} ms) — ${db.message}</div>
        <div><strong>Market Feed:</strong> ${mkt.status.toUpperCase()} (${mkt.latency_ms} ms) — Symbol: ${mkt.symbol}, Source: ${mkt.source} (Sample: ${mkt.is_sample})</div>
        <div><strong>STT Engine:</strong> Mode: ${ai.stt.mode} (Configured: ${ai.stt.configured})</div>
        <div><strong>Evon Intent Parser:</strong> Mode: ${ai.intent_understanding.mode} (Configured: ${ai.intent_understanding.configured})</div>
        <div><strong>Voice Synthesis:</strong> Mode: ${ai.tts.mode} (Configured: ${ai.tts.configured})</div>
      </div>
    `;
    showToast("Subsystem latency ping completed!");
  } catch (err) {
    resBox.innerHTML = `<span style="color:#B71C1C;">Ping error: ${err.message}</span>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "⚡ Test Subsystem Latency";
  }
}

function openResetModal() {
  document.getElementById("resetModal").classList.add("open");
}

function closeResetModal() {
  document.getElementById("resetModal").classList.remove("open");
}

async function executeResetDemo() {
  closeResetModal();
  try {
    const res = await fetch("/api/v1/settings/reset-demo", { method: "POST" });
    if (!res.ok) throw new Error("Failed to reset demo data");
    showToast("Demo data reseeded successfully!");
    loadDiagnostics();
  } catch (err) {
    showToast("Reset failed: " + err.message, true);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  loadDiagnostics();
});

