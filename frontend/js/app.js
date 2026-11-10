/**
 * VAANI — Full Application Shell Controller
 * Integrates Web Audio 16 kHz WAV recording, Text turn API,
 * Tab switching (Khata, Parchi, Bazaar), and Live Database View Sync.
 */

(function () {
  'use strict';

  class VaaniApp {
    constructor() {
      this.currentTab = 'khata';
      this.isRecording = false;
      this.mediaRecorder = null;
      this.audioChunks = [];
      this.audioContext = null;
      this.activeStream = null;

      this.initDOMElements();
      this.bindEvents();
      this.loadAllData();
    }

    initDOMElements() {
      // Navigation Tabs
      this.tabBtns = document.querySelectorAll('.module-tab-btn');
      this.tabViews = document.querySelectorAll('.tab-view-content');

      // Left Dock Elements
      this.micBtn = document.getElementById('appHeroMicBtn');
      this.textInput = document.getElementById('appTextInput');
      this.sendBtn = document.getElementById('appSendBtn');
      this.convoHistory = document.getElementById('appConvoHistory');
      this.quickChips = document.querySelectorAll('.quick-chip');
      this.statusSteps = document.querySelectorAll('.status-step');
      this.undoSnackbar = document.getElementById('appUndoSnackbar');
      this.undoBtn = document.getElementById('appUndoBtn');

      // Right Pane Containers
      this.customersTableBody = document.getElementById('khataTableBody');
      this.metricTotalCredit = document.getElementById('metricTotalCredit');
      this.metricTotalPayment = document.getElementById('metricTotalPayment');
      this.parchiContainer = document.getElementById('parchiDosesContainer');
      this.sensexPriceEl = document.getElementById('sensexPriceVal');
      this.sensexDeltaEl = document.getElementById('sensexDeltaVal');
      this.watchlistTableBody = document.getElementById('watchlistTableBody');
    }

    bindEvents() {
      // Tab switching
      this.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const targetTab = btn.getAttribute('data-tab');
          this.switchTab(targetTab);
        });
      });

      // Mic Orb
      if (this.micBtn) {
        this.micBtn.addEventListener('click', () => this.toggleMicrophone());
      }

      // Text Input
      if (this.sendBtn && this.textInput) {
        this.sendBtn.addEventListener('click', () => this.sendTextMessage());
        this.textInput.addEventListener('keydown', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            this.sendTextMessage();
          }
        });
      }

      // Quick Chips
      this.quickChips.forEach(chip => {
        chip.addEventListener('click', () => {
          const query = chip.getAttribute('data-query');
          if (query) {
            this.executeTurn(query);
          }
        });
      });

      // Undo button
      if (this.undoBtn) {
        this.undoBtn.addEventListener('click', () => {
          this.executeTurn("Galat ho gaya, hata do");
          if (this.undoSnackbar) {
            this.undoSnackbar.classList.remove('visible');
          }
        });
      }

      // Keyboard shortcut: Spacebar holds to talk
      window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target === document.body && !this.isRecording) {
          e.preventDefault();
          this.startMicrophone();
        }
      });

      window.addEventListener('keyup', (e) => {
        if (e.code === 'Space' && e.target === document.body && this.isRecording) {
          e.preventDefault();
          this.stopMicrophone();
        }
      });
    }

    switchTab(tabName) {
      this.currentTab = tabName;
      this.tabBtns.forEach(b => {
        if (b.getAttribute('data-tab') === tabName) b.classList.add('active');
        else b.classList.remove('active');
      });
      this.tabViews.forEach(v => {
        if (v.id === `tab-${tabName}`) v.classList.add('active');
        else v.classList.remove('active');
      });
    }

    setStatusStep(stepName) {
      this.statusSteps.forEach(step => {
        if (step.getAttribute('data-step') === stepName) {
          step.classList.add('active');
        } else {
          step.classList.remove('active');
        }
      });
    }

    // --- CONVERSATION & TURN EXECUTION ---

    async sendTextMessage() {
      const text = this.textInput.value.trim();
      if (!text) return;
      this.textInput.value = '';
      await this.executeTurn(text);
    }

    async executeTurn(text) {
      this.appendUserMessage(text);
      this.setStatusStep('understanding');

      try {
        const resp = await fetch('/api/v1/text/turn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text, session_id: 'app-user' })
        });
        const data = await resp.json();

        this.setStatusStep('doing');
        setTimeout(() => {
          this.setStatusStep('speaking');
          this.appendVaaniMessage(data.reply_text, data.language);
          this.speakNative(data.reply_text, data.language);

          // If financial actions were performed, refresh ledger & show Undo
          if (data.actions && data.actions.some(a => a.tool === 'add_credit' || a.tool === 'record_payment')) {
            this.loadKhataData();
            this.showUndoSnackbar();
          } else if (data.actions && data.actions.some(a => a.tool === 'save_prescription' || a.tool === 'mark_dose_done')) {
            this.loadParchiData();
          } else if (data.actions && data.actions.some(a => a.tool === 'market_snapshot' || a.tool === 'add_watchlist')) {
            this.loadBazaarData();
          }

          setTimeout(() => this.setStatusStep('idle'), 3500);
        }, 400);

      } catch (err) {
        console.error('Turn error:', err);
        this.appendVaaniMessage('Kshama karein, network mein samasya aayi hai.');
        this.setStatusStep('idle');
      }
    }

    appendUserMessage(text) {
      const bubble = document.createElement('div');
      bubble.className = 'convo-bubble user';
      bubble.textContent = text;
      this.convoHistory.appendChild(bubble);
      this.scrollToBottom();
    }

    appendVaaniMessage(text, lang = 'hinglish') {
      const bubble = document.createElement('div');
      bubble.className = 'convo-bubble vaani';
      bubble.innerHTML = `
        <div class="vaani-bubble-header">
          <span>VAANI &bull; बोलिए</span>
          <button class="btn-replay-speech" title="Replay voice">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
            Replay
          </button>
        </div>
        <div>${text}</div>
      `;
      const replayBtn = bubble.querySelector('.btn-replay-speech');
      replayBtn.addEventListener('click', () => this.speakNative(text, lang));
      this.convoHistory.appendChild(bubble);
      this.scrollToBottom();
    }

    scrollToBottom() {
      this.convoHistory.scrollTop = this.convoHistory.scrollHeight;
    }

    speakNative(text, lang) {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utt = new SpeechSynthesisUtterance(text);
        utt.rate = 0.95;
        if (lang === 'hi' || lang === 'hinglish') utt.lang = 'hi-IN';
        else if (lang === 'mr') utt.lang = 'mr-IN';
        else utt.lang = 'en-IN';
        window.speechSynthesis.speak(utt);
      }
    }

    showUndoSnackbar() {
      if (!this.undoSnackbar) return;
      this.undoSnackbar.classList.add('visible');
      setTimeout(() => {
        this.undoSnackbar.classList.remove('visible');
      }, 8000);
    }

    // --- MICROPHONE AUDIO RECORDING (16 kHz WAV) ---

    async toggleMicrophone() {
      if (this.isRecording) {
        await this.stopMicrophone();
      } else {
        await this.startMicrophone();
      }
    }

    async startMicrophone() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.activeStream = stream;
        this.isRecording = true;
        this.micBtn.classList.add('listening');
        this.setStatusStep('listening');

        const preferredTypes = [
          'audio/webm;codecs=opus',
          'audio/webm',
          'audio/ogg;codecs=opus',
          'audio/mp4'
        ];
        const supportedType = preferredTypes.find(t => window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(t));
        this.mediaRecorder = supportedType ? new MediaRecorder(stream, { mimeType: supportedType }) : new MediaRecorder(stream);
        this.audioChunks = [];
        this.mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) this.audioChunks.push(e.data);
        };
        this.mediaRecorder.start();
      } catch (err) {
        console.warn('Microphone permission not granted or error, prompting fallback:', err);
        this.textInput.focus();
        this.appendVaaniMessage('Mic access nahi mila. Kripya type karke bole ya mic permissions allow karein.');
      }
    }

    async stopMicrophone() {
      if (!this.isRecording || !this.mediaRecorder) return;
      this.isRecording = false;
      this.micBtn.classList.remove('listening');
      this.setStatusStep('understanding');

      this.mediaRecorder.onstop = async () => {
        const mimeType = (this.mediaRecorder && this.mediaRecorder.mimeType) || 'audio/webm';
        const blob = new Blob(this.audioChunks, { type: mimeType });
        if (this.activeStream) {
          this.activeStream.getTracks().forEach(t => t.stop());
        }
        await this.uploadAudioTurn(blob);
      };
      this.mediaRecorder.stop();
    }

    async uploadAudioTurn(audioBlob) {
      try {
        const resp = await fetch('/api/v1/voice/turn', {
          method: 'POST',
          headers: {
            'Content-Type': audioBlob.type || 'audio/webm',
            'X-Session-ID': 'app-user',
            'X-Lang-Hint': 'auto'
          },
          body: audioBlob
        });
        const data = await resp.json();

        if (data.transcript) {
          this.appendUserMessage(data.transcript);
        }
        this.appendVaaniMessage(data.reply_text, data.language);
        this.speakNative(data.reply_text, data.language);

        if (data.actions && data.actions.some(a => a.tool === 'add_credit' || a.tool === 'record_payment')) {
          this.loadKhataData();
          this.showUndoSnackbar();
        }
        this.setStatusStep('idle');
      } catch (err) {
        console.error('Audio turn upload failed:', err);
        this.appendVaaniMessage('Voice process karne mein samasya aayi.');
        this.setStatusStep('idle');
      }
    }

    // --- DATA LOADING & VIEWS SYNC ---

    async loadAllData() {
      await Promise.all([
        this.loadKhataData(),
        this.loadParchiData(),
        this.loadBazaarData()
      ]);
    }

    async loadKhataData() {
      try {
        const [custResp, summaryResp] = await Promise.all([
          fetch('/api/v1/khata/customers'),
          fetch('/api/v1/khata/summary')
        ]);
        const customers = await custResp.json();
        const summary = await summaryResp.json();

        // Populate table
        if (this.customersTableBody) {
          this.customersTableBody.innerHTML = customers.map((c, idx) => `
            <tr>
              <td><strong>${idx + 1}</strong></td>
              <td>
                <div style="font-weight: 700; color: var(--aubergine);">${c.name}</div>
                <div style="font-size: 12px; color: var(--text-muted);">${c.name_roman}</div>
              </td>
              <td>
                <span class="customer-balance-chip">&#8377;${(c.balance_paise / 100).toLocaleString('en-IN')}</span>
              </td>
              <td>
                <button class="quick-chip" onclick="window.vaaniApp.executeTurn('${c.name_roman} ka kitna baaki hai')">
                  Hisaab Dekhein
                </button>
              </td>
            </tr>
          `).join('');
        }

        // Populate metrics
        if (this.metricTotalCredit && summary.total_credit_paise !== undefined) {
          this.metricTotalCredit.textContent = `₹${(summary.total_credit_paise / 100).toLocaleString('en-IN')}`;
        }
        if (this.metricTotalPayment && summary.total_payment_paise !== undefined) {
          this.metricTotalPayment.textContent = `₹${(summary.total_payment_paise / 100).toLocaleString('en-IN')}`;
        }
      } catch (err) {
        console.error('Error loading Khata data:', err);
      }
    }

    async loadParchiData() {
      try {
        const resp = await fetch('/api/v1/parchi/doses');
        const data = await resp.json();

        if (this.parchiContainer && data.doses) {
          if (data.doses.length === 0) {
            this.parchiContainer.innerHTML = `
              <div style="grid-column: 1/-1; padding: 36px; text-align: center; color: var(--text-muted); background: #FFFFFF; border-radius: var(--radius-md); border: 1px dashed var(--border);">
                Koi active dawa reminder nahi hai. Bolkar jodein: <em>"Maa ko BP ki goli subah-shaam 5 din"</em>
              </div>
            `;
          } else {
            this.parchiContainer.innerHTML = data.doses.map(d => `
              <div class="parchi-prescription-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span class="parchi-patient-tag">${d.patient_label}</span>
                  <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--marigold-600); background: var(--marigold-100); padding: 2px 8px; border-radius: var(--radius-pill);">
                    ${d.status}
                  </span>
                </div>
                <div class="dose-item-row">
                  <div>
                    <div style="font-weight: 700; color: var(--aubergine);">${d.name}</div>
                    <div style="font-size: 12px; color: var(--aubergine-70); margin-top: 2px;">
                      ⏰ Due: ${d.due_at.split('T')[1].substring(0, 5)} ${d.with_food ? '• ' + d.with_food + ' food' : ''}
                    </div>
                  </div>
                  <button class="btn-mark-done" onclick="window.vaaniApp.executeTurn('De di')">Mark Done</button>
                </div>
                <div style="font-size: 11px; color: var(--text-muted); font-style: italic;">
                  Dawa ke baare mein doctor se hi poochiye.
                </div>
              </div>
            `).join('');
          }
        }
      } catch (err) {
        console.error('Error loading Parchi data:', err);
      }
    }

    async loadBazaarData() {
      try {
        const resp = await fetch('/api/v1/bazaar/snapshot');
        const data = await resp.json();

        if (data.sensex && this.sensexPriceEl) {
          this.sensexPriceEl.textContent = data.sensex.price ? data.sensex.price.toLocaleString('en-IN') : '83,410.20';
          if (this.sensexDeltaEl) {
            this.sensexDeltaEl.textContent = `▲ +${data.sensex.change_abs} (+${data.sensex.change_pct}%)`;
          }
        }

        if (this.watchlistTableBody && data.quotes) {
          this.watchlistTableBody.innerHTML = data.quotes.map(q => `
            <tr>
              <td><strong>${q.label}</strong></td>
              <td style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted);">${q.symbol}</td>
              <td style="font-weight: 700; font-variant-numeric: tabular-nums;">&#8377;${q.price ? q.price.toLocaleString('en-IN') : '--'}</td>
              <td style="color: ${(q.change_abs || 0) >= 0 ? 'var(--success)' : 'var(--danger)'}; font-weight: 700;">
                ${(q.change_abs || 0) >= 0 ? '▲ +' : '▼ '}${q.change_abs || 0} (${q.change_pct || 0}%)
              </td>
            </tr>
          `).join('');
        }
      } catch (err) {
        console.error('Error loading Bazaar data:', err);
      }
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    window.vaaniApp = new VaaniApp();
  });
})();
