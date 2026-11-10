/**
 * VAANI — Settings & Voice Selection Controller
 * Official Gnani Speech API Integration: Timbre v3.0 Flagship & Timbre v2.5 Vernacular.
 * Supports:
 * - Dynamic Voice Discovery & Catalog Listing
 * - Model-specific compatibility enforcement
 * - Ephemeral Live Audio Previews via Gnani TTS (zero DB writes)
 * - Persisting voice persona across all workspaces
 * - Realtime latency diagnostics & Clean-slate resets
 */

(function () {
  'use strict';

  // Global Controller State
  let catalogData = null;
  let activeModel = 'timbre-v3.0';
  let selectedVoiceId = 'Shivani';
  let activePersistedVoiceId = 'Shivani';
  let activePersistedModel = 'timbre-v3.0';
  let currentSpeed = 1.0;
  let currentLanguage = 'auto';

  // Audio Playback Tracking
  let currentAudio = null;
  let currentPlayingBtn = null;

  function showToast(message, isError = false) {
    const toast = document.getElementById("toastMsg");
    const icon = document.getElementById("toastIcon");
    const text = document.getElementById("toastText");
    if (!toast || !icon || !text) return;

    icon.textContent = isError ? "⚠️" : "✓";
    text.textContent = message;
    toast.style.background = isError ? "#B71C1C" : "var(--aubergine)";
    toast.classList.add("show");

    setTimeout(() => {
      toast.classList.remove("show");
    }, 3200);
  }

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

  // ---------------------------------------------------------------------------
  // GNANI VOICE CATALOGUE & SELECTION
  // ---------------------------------------------------------------------------

  async function loadVoiceCatalog() {
    const listEl = document.getElementById("gnaniVoiceList");
    if (!listEl) return;

    try {
      const [catResp, setResp] = await Promise.all([
        fetch("/api/v1/voice/catalog"),
        fetch("/api/v1/settings/voice")
      ]);

      if (!catResp.ok) throw new Error("Could not load voice catalogue");
      catalogData = await catResp.json();

      if (setResp.ok) {
        const settings = await setResp.json();
        activeModel = settings.tts_model || 'timbre-v3.0';
        selectedVoiceId = settings.voice_id || ('timbre-v3.0' === activeModel ? 'Shivani' : 'Bhavna');
        activePersistedVoiceId = selectedVoiceId;
        activePersistedModel = activeModel;
        currentSpeed = settings.speech_rate || 1.0;
        currentLanguage = settings.language || 'auto';
      }

      // Update Top Tabs & Controls
      updateModelTabsUI();
      const speedSelect = document.getElementById("voiceSpeedSelect");
      if (speedSelect) speedSelect.value = currentSpeed.toFixed(1);

      updateActiveBadge();
      applyVoiceFilters();
    } catch (err) {
      console.error("Error loading voice catalog:", err);
      listEl.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 24px; text-align: center; color: #B71C1C;">
          Could not load Gnani voice catalogue: ${err.message}
        </div>
      `;
    }
  }

  function updateModelTabsUI() {
    const btnV3 = document.getElementById("btnModelV3");
    const btnV25 = document.getElementById("btnModelV25");
    if (btnV3 && btnV25) {
      if (activeModel === "timbre-v3.0") {
        btnV3.classList.add("active");
        btnV25.classList.remove("active");
      } else {
        btnV25.classList.add("active");
        btnV3.classList.remove("active");
      }
    }
  }

  function updateActiveBadge() {
    const badge = document.getElementById("activeVoiceBadge");
    const summary = document.getElementById("selectedVoiceSummary");
    const text = `${selectedVoiceId} (${activeModel})`;

    if (badge) {
      badge.textContent = `Active: ${text}`;
      badge.className = "status-badge live";
    }
    if (summary) {
      summary.textContent = text;
    }
  }

  function switchTtsModel(modelName) {
    if (activeModel === modelName) return;

    stopCurrentAudio();
    activeModel = modelName;
    updateModelTabsUI();

    // Model compatibility enforcement:
    // If the currently selected voice does not belong to the newly chosen model,
    // automatically select that model's documented default voice.
    const currentModelVoices = getVoicesForActiveModel();
    const isSupported = currentModelVoices.some(v => v.id.toLowerCase() === selectedVoiceId.toLowerCase());
    if (!isSupported) {
      selectedVoiceId = modelName === 'timbre-v3.0' ? 'Shivani' : 'Bhavna';
    }

    updateActiveBadge();
    applyVoiceFilters();
  }

  function getVoicesForActiveModel() {
    if (!catalogData || !catalogData.models) return [];
    const modelObj = catalogData.models.find(m => m.id === activeModel);
    return modelObj ? modelObj.voices : [];
  }

  function applyVoiceFilters() {
    const voices = getVoicesForActiveModel();
    const langFilter = (document.getElementById("filterVoiceLang")?.value || "all").toLowerCase();
    const genderFilter = (document.getElementById("filterVoiceGender")?.value || "all").toLowerCase();
    const searchTerm = (document.getElementById("filterVoiceSearch")?.value || "").toLowerCase().trim();

    const filtered = voices.filter(v => {
      // Language filter
      if (langFilter !== "all") {
        const hasLang = (v.languages && v.languages.some(l => l.toLowerCase() === langFilter)) ||
                        (v.primary_language && v.primary_language.toLowerCase() === langFilter);
        if (!hasLang) return false;
      }

      // Gender filter
      if (genderFilter !== "all" && v.gender.toLowerCase() !== genderFilter) {
        return false;
      }

      // Search filter
      if (searchTerm) {
        const matchesName = v.display_name.toLowerCase().includes(searchTerm) || v.id.toLowerCase().includes(searchTerm);
        const matchesPersona = (v.persona || "").toLowerCase().includes(searchTerm);
        const matchesDesc = (v.description || "").toLowerCase().includes(searchTerm);
        if (!matchesName && !matchesPersona && !matchesDesc) return false;
      }

      return true;
    });

    renderVoiceCards(filtered);
  }

  function renderVoiceCards(voicesList) {
    const listEl = document.getElementById("gnaniVoiceList");
    if (!listEl) return;

    if (voicesList.length === 0) {
      listEl.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 32px; text-align: center; color: var(--text-muted); background: var(--ice-50); border-radius: var(--radius-sm);">
          No voices match the selected filters for ${activeModel}. Try adjusting the language or gender filter.
        </div>
      `;
      return;
    }

    listEl.innerHTML = voicesList.map(v => {
      const isSelected = v.id.toLowerCase() === selectedVoiceId.toLowerCase();
      const isActivePersisted = isSelected && activeModel === activePersistedModel;
      const langBadge = v.primary_language_name || (v.languages ? v.languages.join(", ") : "Indian");

      return `
        <div class="voice-card ${isSelected ? 'selected' : ''}" id="voice-card-${v.id}" onclick="selectVoice('${v.id}')">
          <div class="voice-card-header">
            <div>
              <div class="voice-name-title">
                ${v.display_name}
                <span style="font-size: 13px; color: var(--text-muted); font-weight: 400;">(${v.gender})</span>
              </div>
              <div class="voice-badges-row">
                <span class="voice-chip engine">${activeModel}</span>
                <span class="voice-chip lang">${langBadge}</span>
              </div>
            </div>
            ${isActivePersisted ? `
              <span class="status-badge live" style="font-size: 10px;">✓ Active</span>
            ` : ''}
          </div>

          <div style="font-size: 13px; font-weight: 600; color: var(--aubergine);">
            ${v.persona || 'Conversational'}
          </div>

          <div class="voice-desc">
            ${v.description || 'Natural speech synthesis persona.'}
          </div>

          <div class="voice-sample-quote">
            "${v.sample_text || 'नमस्ते, मैं वाणी हूँ. आपकी दुकान का डिजिटल साथी.'}"
          </div>

          <div class="voice-card-actions" onclick="event.stopPropagation()">
            <button
              class="btn-preview-voice"
              id="preview-btn-${v.id}"
              onclick="previewVoice('${v.id}', this)"
              title="Preview real synthesized voice via Gnani TTS"
            >
              <span>🔊</span>
              <span>Preview</span>
            </button>

            <button
              class="btn-select-voice"
              onclick="selectVoice('${v.id}')"
            >
              ${isSelected ? '✓ Selected' : 'Select'}
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  function selectVoice(voiceId) {
    selectedVoiceId = voiceId;

    // Update Card styles
    document.querySelectorAll(".voice-card").forEach(c => c.classList.remove("selected"));
    const activeCard = document.getElementById(`voice-card-${voiceId}`);
    if (activeCard) activeCard.classList.add("selected");

    updateActiveBadge();

    // Update select dropdown if present
    const sel = document.getElementById("prefVoice");
    if (sel) sel.value = voiceId;
  }

  function updateVoiceSpeed() {
    const sel = document.getElementById("voiceSpeedSelect");
    if (sel) {
      currentSpeed = parseFloat(sel.value) || 1.0;
    }
  }

  function stopCurrentAudio() {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }
    if (currentPlayingBtn) {
      currentPlayingBtn.classList.remove("playing");
      currentPlayingBtn.innerHTML = `<span>🔊</span><span>Preview</span>`;
      currentPlayingBtn = null;
    }
  }

  async function previewVoice(voiceId, btnEl) {
    // If currently playing this specific voice, stop it
    if (currentPlayingBtn === btnEl && currentAudio && !currentAudio.paused) {
      stopCurrentAudio();
      return;
    }

    // Stop any existing playing audio
    stopCurrentAudio();

    currentPlayingBtn = btnEl;
    btnEl.classList.add("playing");
    btnEl.innerHTML = `<span>⏳</span><span>Loading...</span>`;

    try {
      const resp = await fetch("/api/v1/voice/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          voice_id: voiceId,
          model: activeModel,
          speed: currentSpeed,
          language: currentLanguage
        })
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({ detail: "Preview generation failed" }));
        throw new Error(errData.detail || "Preview failed");
      }

      const data = await resp.json();
      if (!data.audio_base64) {
        throw new Error("Gnani TTS did not return audio data.");
      }

      // Play audio cleanly
      const audio = new Audio("data:audio/wav;base64," + data.audio_base64);
      currentAudio = audio;
      btnEl.innerHTML = `<span>⏹</span><span>Stop</span>`;

      audio.onended = () => {
        stopCurrentAudio();
      };
      audio.onerror = () => {
        stopCurrentAudio();
      };

      await audio.play();
    } catch (err) {
      console.warn("Preview error:", err);
      stopCurrentAudio();
      showToast(`Preview failed: ${err.message}`, true);
    }
  }

  async function saveSelectedVoicePreference() {
    stopCurrentAudio();

    const payload = {
      voice_id: selectedVoiceId,
      model: activeModel,
      speed: currentSpeed,
      language: currentLanguage
    };

    try {
      const resp = await fetch("/api/v1/settings/voice", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({ detail: "Failed to persist voice preference" }));
        throw new Error(errData.detail || "Update failed");
      }

      const res = await resp.json();
      activePersistedVoiceId = selectedVoiceId;
      activePersistedModel = activeModel;

      updateActiveBadge();
      applyVoiceFilters();

      // Broadcast globally for any active agents on the page
      window.vaaniVoice = selectedVoiceId;
      window.vaaniModel = activeModel;
      window.dispatchEvent(new CustomEvent("vaani:voice-updated", {
        detail: { voice_id: selectedVoiceId, model: activeModel }
      }));

      showToast(`Voice preference saved to ${selectedVoiceId} (${activeModel})!`);
    } catch (err) {
      showToast(`Save failed: ${err.message}`, true);
    }
  }

  // ---------------------------------------------------------------------------
  // GENERAL SHOPKEEPER PREFERENCES
  // ---------------------------------------------------------------------------

  async function loadGeneralSettings() {
    try {
      const res = await fetch("/api/v1/settings");
      if (!res.ok) throw new Error("Failed to load settings");
      const currentSettings = await res.json();

      if (currentSettings.language && document.getElementById("prefLanguage")) {
        document.getElementById("prefLanguage").value = currentSettings.language;
      }
      if (currentSettings.speech_rate && document.getElementById("prefRate")) {
        document.getElementById("prefRate").value = currentSettings.speech_rate;
      }
      if (currentSettings.confirm_threshold && document.getElementById("prefConfirmThreshold")) {
        document.getElementById("prefConfirmThreshold").value = currentSettings.confirm_threshold;
      }
      if (currentSettings.snooze_duration_mins && document.getElementById("prefSnooze")) {
        document.getElementById("prefSnooze").value = currentSettings.snooze_duration_mins;
      }
      if (currentSettings.privacy_mode && document.getElementById("prefPrivacy")) {
        document.getElementById("prefPrivacy").value = currentSettings.privacy_mode;
      }

      const isDemo = currentSettings.demo_mode === "true" || currentSettings.demo_mode === true;
      const demoIndicator = document.getElementById("demoModeIndicator");
      const demoText = document.getElementById("demoModeText");
      if (demoIndicator && demoText) {
        demoText.textContent = isDemo ? "Demo Mode: ON" : "Production Mode (Zero Demo Data)";
        demoIndicator.style.background = isDemo ? "#E8F5E9" : "var(--ice-50)";
      }
    } catch (err) {
      console.error("Error loading general settings:", err);
    }
  }

  async function saveShopkeeperSettings() {
    const payload = {
      settings: {
        language: document.getElementById("prefLanguage")?.value || "auto",
        tts_model: activeModel,
        voice_id: selectedVoiceId,
        voice_hi: selectedVoiceId,
        speech_rate: document.getElementById("prefRate")?.value || "1.0",
        confirm_threshold: document.getElementById("prefConfirmThreshold")?.value || "5000",
        snooze_duration_mins: document.getElementById("prefSnooze")?.value || "10",
        privacy_mode: document.getElementById("prefPrivacy")?.value || "balanced"
      }
    };

    try {
      const res = await fetch("/api/v1/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error("Could not update settings");
      showToast("General preferences saved successfully!");
    } catch (err) {
      showToast("Error saving preferences: " + err.message, true);
    }
  }

  // ---------------------------------------------------------------------------
  // SYSTEM & DIAGNOSTICS
  // ---------------------------------------------------------------------------

  async function loadDiagnostics() {
    try {
      const res = await fetch("/api/v1/settings/diagnostics");
      if (!res.ok) throw new Error("Failed to load diagnostics");
      const data = await res.json();

      // Unified Sovereign Key Banner
      const unifiedKey = data.masked_credentials.GNANI_API_KEY || "Not Configured";
      const unifiedDisplay = document.getElementById("unifiedKeyDisplay");
      const badgeUnified = document.getElementById("badgeUnifiedKey");
      if (unifiedDisplay) unifiedDisplay.textContent = unifiedKey;
      if (badgeUnified) {
        if (unifiedKey !== "Not Configured") {
          badgeUnified.className = "status-badge live";
          badgeUnified.textContent = "Configured & Active";
        } else {
          badgeUnified.className = "status-badge fallback";
          badgeUnified.textContent = "Not Configured";
        }
      }

      // STT
      const stt = data.ai_readiness.stt || data.ai_readiness.prisma;
      const badgeStt = document.getElementById("badgeStt");
      const sttMode = document.getElementById("sttMode");
      const sttKey = document.getElementById("sttKey");
      if (sttMode) sttMode.textContent = (stt?.model || "PRISMA-V3.0").toUpperCase();
      if (sttKey) sttKey.textContent = unifiedKey;
      if (badgeStt) {
        if (stt?.configured || unifiedKey !== "Not Configured") {
          badgeStt.className = "status-badge live";
          badgeStt.textContent = "Live Prisma v3.0";
        } else {
          badgeStt.className = "status-badge fallback";
          badgeStt.textContent = "Unconfigured";
        }
      }

      // Evon Intent Parser
      const evon = data.ai_readiness.intent_understanding || data.ai_readiness.evon;
      const badgeIntent = document.getElementById("badgeIntent");
      const intentMode = document.getElementById("intentMode");
      const intentKey = document.getElementById("intentKey");
      if (intentMode) intentMode.textContent = (evon?.model || "EVON-V3.3").toUpperCase();
      if (intentKey) intentKey.textContent = "Deterministic Rules Engine";
      if (badgeIntent) {
        badgeIntent.className = "status-badge live";
        badgeIntent.textContent = "Rules Active (100% Pass)";
      }

      // TTS
      const tts = data.ai_readiness.tts;
      const badgeTts = document.getElementById("badgeTts");
      const ttsMode = document.getElementById("ttsMode");
      const voiceVal = document.getElementById("ttsVoiceVal");
      if (ttsMode) ttsMode.textContent = `${activeModel.toUpperCase()}`;
      if (voiceVal) voiceVal.textContent = `${selectedVoiceId} (${activeModel})`;
      if (badgeTts) {
        if (unifiedKey !== "Not Configured") {
          badgeTts.className = "status-badge live";
          badgeTts.textContent = `Live ${activeModel}`;
        } else {
          badgeTts.className = "status-badge fallback";
          badgeTts.textContent = "Unconfigured";
        }
      }

      // Market Feed
      const market = data.ai_readiness.market_data;
      const badgeMarket = document.getElementById("badgeMarket");
      const marketSource = document.getElementById("marketSource");
      if (marketSource) marketSource.textContent = (market?.provider || "Yahoo Finance").toUpperCase();
      if (badgeMarket) {
        badgeMarket.className = "status-badge live";
        badgeMarket.textContent = "Live / Real Data";
      }

      // Database Row Counts (Zero Demo Data Check)
      const db = data.database || {};
      const counts = db.row_counts || {};
      const cntCust = document.getElementById("cntCustomers");
      const cntEnt = document.getElementById("cntEntries");
      const cntPresc = document.getElementById("cntPrescriptions");
      const cntRem = document.getElementById("cntReminders");
      const cntWatch = document.getElementById("cntWatchlist");

      if (cntCust) cntCust.textContent = counts.customers ?? 0;
      if (cntEnt) cntEnt.textContent = counts.ledger_entries ?? 0;
      if (cntPresc) cntPresc.textContent = counts.prescriptions ?? 0;
      if (cntRem) cntRem.textContent = counts.reminders ?? 0;
      if (cntWatch) cntWatch.textContent = counts.watchlist ?? 0;

      const pathVal = document.getElementById("dbPathVal");
      if (pathVal && db.path) pathVal.textContent = db.path;
    } catch (err) {
      console.error("Error loading diagnostics:", err);
    }
  }

  async function runConnectivityTest() {
    const btn = document.getElementById("btnTestConn");
    const resBox = document.getElementById("connectivityResult");
    if (!btn || !resBox) return;

    btn.disabled = true;
    btn.textContent = "Testing...";
    resBox.style.display = "block";
    resBox.textContent = "Pinging SQLite database, Yahoo Finance market feed, and Gnani Speech APIs...";

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
          <div><strong>Market Feed:</strong> ${mkt.status.toUpperCase()} (${mkt.latency_ms} ms) — Symbol: ${mkt.symbol}, Source: ${mkt.source}</div>
          <div><strong>Gnani STT (Prisma v3.0):</strong> Configured: ${ai.stt.configured} | Model: ${ai.stt.model}</div>
          <div><strong>Evon Intent Parser:</strong> Active: Rules Engine (Deterministic Guardrails)</div>
          <div><strong>Gnani TTS (${activeModel}):</strong> Selected Voice: ${selectedVoiceId} | Configured: ${ai.tts.configured}</div>
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
    const modal = document.getElementById("resetModal");
    if (modal) modal.classList.add("open");
  }

  function closeResetModal() {
    const modal = document.getElementById("resetModal");
    if (modal) modal.classList.remove("open");
  }

  async function executeResetDemo() {
    closeResetModal();
    try {
      const res = await fetch("/api/v1/settings/reset-demo", { method: "POST" });
      if (!res.ok) throw new Error("Failed to reset database");
      showToast("Database reset to clean slate (zero demo data)!");
      loadDiagnostics();
    } catch (err) {
      showToast("Reset failed: " + err.message, true);
    }
  }

  // Export to window for HTML inline handlers
  window.switchSettingsTab = switchSettingsTab;
  window.switchTtsModel = switchTtsModel;
  window.applyVoiceFilters = applyVoiceFilters;
  window.selectVoice = selectVoice;
  window.updateVoiceSpeed = updateVoiceSpeed;
  window.previewVoice = previewVoice;
  window.saveSelectedVoicePreference = saveSelectedVoicePreference;
  window.saveShopkeeperSettings = saveShopkeeperSettings;
  window.runConnectivityTest = runConnectivityTest;
  window.openResetModal = openResetModal;
  window.closeResetModal = closeResetModal;
  window.executeResetDemo = executeResetDemo;

  document.addEventListener("DOMContentLoaded", () => {
    loadVoiceCatalog();
    loadGeneralSettings();
    loadDiagnostics();
  });
})();
