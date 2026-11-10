/**
 * VAANI — Reusable Contextual Agent Component
 * Shared across Bol-Khata, Parchi, Sensex Awaaz, Settings, and Overview pages.
 * Fully integrated with official Gnani Prisma v3.0 STT & Timbre v3.0 / v2.5 TTS.
 * Zero browser speechSynthesis or mock fallbacks: Only real Gnani audio playback.
 */

(function () {
  'use strict';

  class VaaniAgent {
    constructor(options = {}) {
      this.containerId = options.containerId;
      this.moduleId = options.moduleId || options.moduleScope || 'overview';
      this.moduleTitle = options.moduleTitle || (this.moduleId === 'settings' ? 'Vaani Settings & Diagnostics' : 'Vaani Assistant');
      this.initialGreeting = options.initialGreeting || options.welcomeMessage || 'Namaste! Main Vaani hoon. Boliye, main sun rahi hoon.';
      this.quickPhrases = options.quickPhrases || options.suggestedChips || [];
      this.onActionExecuted = options.onActionExecuted || (() => {});

      this.isRecording = false;
      this.isPlayingSpeech = false;
      this.mediaRecorder = null;
      this.audioChunks = [];
      this.activeStream = null;
      this.currentAudio = null;

      this.container = document.getElementById(this.containerId);
      if (!this.container) {
        console.error(`VaaniAgent: Container #${this.containerId} not found.`);
        return;
      }

      // Register agent instance globally
      window.vaaniAgents = window.vaaniAgents || {};
      window.vaaniAgents[this.containerId] = this;

      this.render();
      this.bindEvents();
      this.initWaveform();
      this.listenVoiceUpdates();
    }

    render() {
      const moduleBadgeText = {
        khata: 'Bol-Khata Scope',
        parchi: 'Parchi Scope',
        bazaar: 'Sensex Awaaz Scope',
        settings: 'Settings Scope',
        overview: 'Global Scope'
      }[this.moduleId] || 'Active';

      this.container.innerHTML = `
        <div class="vaani-agent-panel">
          <!-- Agent Header -->
          <div class="agent-header">
            <div class="agent-title-lockup">
              <div class="agent-avatar-orb">व</div>
              <div>
                <div class="agent-title">${this.moduleTitle}</div>
                <span class="agent-module-tag">${moduleBadgeText}</span>
              </div>
            </div>
            <div class="agent-status-badge">
              <span class="agent-status-dot"></span>
              <span id="${this.containerId}-status-text">Ready</span>
            </div>
          </div>

          <!-- Messages Area -->
          <div class="agent-messages-viewport" id="${this.containerId}-messages">
            <div class="agent-bubble vaani">
              <div class="agent-bubble-speaker-tag">
                <span>VAANI &bull; बोलिए</span>
              </div>
              <div class="agent-bubble-text">${this.initialGreeting}</div>
            </div>
          </div>

          <!-- Quick Suggestion Chips -->
          <div class="agent-quick-chips">
            ${this.quickPhrases.map(phrase => `
              <button class="agent-chip" data-phrase="${phrase}">${phrase}</button>
            `).join('')}
          </div>

          <!-- Dock Controls (Waveform + Mic + Input) -->
          <div class="agent-dock-controls">
            <div class="agent-waveform-row">
              <canvas id="${this.containerId}-waveform" width="300" height="24"></canvas>
            </div>

            <div class="agent-dock-inputs">
              <button id="${this.containerId}-mic-btn" class="agent-mic-btn" title="Tap to speak into microphone" aria-label="Microphone">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                  <line x1="12" y1="19" x2="12" y2="23"></line>
                  <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>
              </button>

              <div class="agent-input-box">
                <input type="text" id="${this.containerId}-input" class="agent-text-input" placeholder="Bolkar ya likhkar batayein..." />
                <button id="${this.containerId}-send-btn" class="agent-send-btn" title="Send command">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      this.messagesContainer = document.getElementById(`${this.containerId}-messages`);
      this.statusText = document.getElementById(`${this.containerId}-status-text`);
      this.micBtn = document.getElementById(`${this.containerId}-mic-btn`);
      this.textInput = document.getElementById(`${this.containerId}-input`);
      this.sendBtn = document.getElementById(`${this.containerId}-send-btn`);
    }

    bindEvents() {
      this.sendBtn.addEventListener('click', () => this.handleTextSubmit());
      this.textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.handleTextSubmit();
        }
      });

      this.container.querySelectorAll('.agent-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          const phrase = chip.getAttribute('data-phrase');
          if (phrase) this.processQuery(phrase);
        });
      });

      this.micBtn.addEventListener('click', () => this.toggleMicrophone());
    }

    listenVoiceUpdates() {
      window.addEventListener('vaani:voice-updated', (e) => {
        if (e.detail && e.detail.voice_id) {
          console.info(`[Agent ${this.moduleId}] Voice updated to ${e.detail.voice_id}`);
        }
      });
    }

    setStatus(text) {
      if (this.statusText) this.statusText.textContent = text;
    }

    async handleTextSubmit() {
      const text = this.textInput.value.trim();
      if (!text) return;
      this.textInput.value = '';
      await this.processQuery(text);
    }

    async processQuery(text) {
      this.appendMessage('user', text);
      this.setStatus('Understanding...');

      const lower = text.toLowerCase();

      // Cross-Module Scope Guard
      if (this.moduleId === 'bazaar') {
        if (lower.includes('udhaar') || lower.includes('likh de') || lower.includes('jama') || lower.includes('diye')) {
          this.setStatus('Ready');
          this.appendMessage('vaani', 
            `Aap abhi <strong>Sensex Awaaz</strong> par hain. Udhaar ya jama hisaab darj karne ke liye Bol-Khata page par jaayein.`, 
            'hinglish', 
            [{ label: 'Bol-Khata Workspace Kholein →', url: '/app/bol-khata' }]
          );
          return;
        }
      } else if (this.moduleId === 'khata') {
        if (lower.includes('goli') || lower.includes('dawa') || lower.includes('antibiotic') || lower.includes('sugar ki dawa')) {
          this.setStatus('Ready');
          this.appendMessage('vaani', 
            `Aap abhi <strong>Bol-Khata</strong> page par hain. Dawa ke niyamit reminder schedule karne ke liye Parchi page par jaayein.`, 
            'hinglish', 
            [{ label: 'Parchi Workspace Kholein →', url: '/app/parchi' }]
          );
          return;
        }
      }

      // Execute through backend pipeline
      try {
        const resp = await fetch('/api/v1/text/turn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: text,
            session_id: `agent-${this.moduleId}`,
            language_hint: 'auto'
          })
        });

        if (!resp.ok) {
          throw new Error(`Server returned HTTP ${resp.status}`);
        }

        const data = await resp.json();

        this.appendMessage('vaani', data.reply_text, data.language, null, data);
        this.speakResponse(data);

        if (this.onActionExecuted) {
          this.onActionExecuted(data);
        }
      } catch (err) {
        console.error('Agent processQuery error:', err);
        this.setStatus('Error');
        this.appendMessage('vaani', 'Kshama karein, aadesh poora karne mein samasya aayi.');
        setTimeout(() => this.setStatus('Ready'), 3000);
      }
    }

    appendMessage(role, text, lang = 'hinglish', actionLinks = null, turnData = null) {
      const bubble = document.createElement('div');
      bubble.className = `agent-bubble ${role}`;

      if (role === 'user') {
        bubble.textContent = text;
      } else {
        let structuredHtml = '';

        if (turnData && turnData.requires_confirmation) {
          structuredHtml += `
            <div class="confirmation-card-box">
              <p>⚠️ Bada amount darj ho raha hai. Kya aap iski pushti karte hain?</p>
              <div class="confirmation-buttons-row">
                <button class="btn-confirm-yes" onclick="window.vaaniAgents['${this.containerId}'].processQuery('Haan, sahi hai')">Haan, likh do</button>
                <button class="btn-confirm-no" onclick="window.vaaniAgents['${this.containerId}'].processQuery('Nahi, galat ho gaya')">Radd karein</button>
              </div>
            </div>
          `;
        }

        if (actionLinks && actionLinks.length > 0) {
          structuredHtml += `
            <div class="agent-bubble-actions">
              ${actionLinks.map(l => `<button class="agent-action-chip" onclick="window.location.href='${l.url}'">${l.label}</button>`).join('')}
            </div>
          `;
        }

        const voiceBadge = turnData && turnData.voice_id ? `🎙️ Gnani ${turnData.voice_id}` : 'VAANI • बोलिए';

        bubble.innerHTML = `
          <div class="agent-bubble-speaker-tag">
            <span>${voiceBadge}</span>
            ${turnData && turnData.audio_base64 ? `
              <button class="btn-replay-icon" title="Replay spoken audio" style="cursor:pointer; background:none; border:none; color:var(--aubergine-70); font-size:11px; font-weight:600;">
                🔊 Replay
              </button>
            ` : ''}
          </div>
          <div class="agent-bubble-text">${text}</div>
          ${structuredHtml}
        `;

        const replayBtn = bubble.querySelector('.btn-replay-icon');
        if (replayBtn && turnData && turnData.audio_base64) {
          replayBtn.addEventListener('click', () => {
            this.playAudioBase64(turnData.audio_base64);
          });
        }
      }

      this.messagesContainer.appendChild(bubble);
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    speakResponse(data) {
      if (data && data.audio_base64) {
        this.playAudioBase64(data.audio_base64);
      } else {
        this.setStatus('Ready');
      }
    }

    playAudioBase64(b64) {
      if (!b64) return;
      try {
        if (this.currentAudio) {
          this.currentAudio.pause();
          this.currentAudio = null;
        }

        const audio = new Audio("data:audio/wav;base64," + b64);
        this.currentAudio = audio;
        this.isPlayingSpeech = true;
        this.setStatus('Speaking...');

        audio.onended = () => {
          this.isPlayingSpeech = false;
          this.setStatus('Ready');
        };
        audio.onerror = () => {
          this.isPlayingSpeech = false;
          this.setStatus('Ready');
        };

        audio.play().catch(e => {
          console.warn("Audio autoplay prevented:", e);
          this.isPlayingSpeech = false;
          this.setStatus('Ready');
        });
      } catch (err) {
        console.warn("Audio playback error:", err);
        this.isPlayingSpeech = false;
        this.setStatus('Ready');
      }
    }

    async toggleMicrophone() {
      if (this.isRecording) {
        await this.stopMicrophone();
      } else {
        await this.startMicrophone();
      }
    }

    async startMicrophone() {
      if (this.currentAudio && !this.currentAudio.paused) {
        this.currentAudio.pause();
        this.currentAudio = null;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.activeStream = stream;
        this.isRecording = true;
        this.micBtn.classList.add('listening');
        this.setStatus('Listening...');

        this.mediaRecorder = new MediaRecorder(stream);
        this.audioChunks = [];
        this.mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) this.audioChunks.push(e.data);
        };
        this.mediaRecorder.start();
      } catch (err) {
        console.warn('Microphone error:', err);
        this.textInput.focus();
        this.appendMessage('vaani', 'Microphone permission nahi mili. Kripya type karke batayein.');
        this.setStatus('Ready');
      }
    }

    async stopMicrophone() {
      if (!this.isRecording || !this.mediaRecorder) return;
      this.isRecording = false;
      this.micBtn.classList.remove('listening');
      this.setStatus('Processing audio...');

      this.mediaRecorder.onstop = async () => {
        const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
        if (this.activeStream) {
          this.activeStream.getTracks().forEach(t => t.stop());
          this.activeStream = null;
        }
        await this.uploadAudio(blob);
      };
      this.mediaRecorder.stop();
    }

    async uploadAudio(blob) {
      this.setStatus('Transcribing (Prisma v3.0)...');

      try {
        const resp = await fetch('/api/v1/voice/turn', {
          method: 'POST',
          headers: {
            'Content-Type': blob.type || 'audio/webm',
            'X-Session-ID': `agent-${this.moduleId}`,
            'X-Lang-Hint': 'indic-auto'
          },
          body: blob
        });

        if (!resp.ok) {
          throw new Error(`Server returned HTTP ${resp.status}`);
        }

        const data = await resp.json();

        if (data.transcript) {
          this.appendMessage('user', data.transcript);
        }

        if (data.error_code === 'CONFIGURATION_MISSING') {
          this.appendMessage('vaani', 'GNANI API KEY NOT CONFIGURED. Please set GNANI_API_KEY in .env on the backend.');
          this.setStatus('Ready');
          return;
        }

        this.appendMessage('vaani', data.reply_text, data.language, null, data);
        this.speakResponse(data);

        if (this.onActionExecuted) {
          this.onActionExecuted(data);
        }
      } catch (err) {
        console.error('Audio upload failed:', err);
        this.setStatus('Error');
        this.appendMessage('vaani', 'Awaaz pehchanne mein samasya aayi. Kripya dobara boliye.');
        setTimeout(() => this.setStatus('Ready'), 3000);
      }
    }

    initWaveform() {
      const canvas = document.getElementById(`${this.containerId}-waveform`);
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      let phase = 0;

      const draw = () => {
        requestAnimationFrame(draw);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        phase += 0.06;

        const bars = 22;
        const barWidth = 3;
        const spacing = (canvas.width - (bars * barWidth)) / (bars - 1);
        const centerY = canvas.height / 2;

        const isActive = this.isRecording || this.isPlayingSpeech;

        for (let i = 0; i < bars; i++) {
          const x = i * (barWidth + spacing);
          const amp = isActive ? 9 : 2.5;
          const h = Math.max(3, Math.abs(Math.sin(phase + i * 0.3) * amp));

          ctx.fillStyle = this.isRecording ? '#EAAA00' : (this.isPlayingSpeech ? '#EAAA00' : 'rgba(58, 15, 52, 0.25)');
          ctx.beginPath();
          ctx.roundRect ? ctx.roundRect(x, centerY - h / 2, barWidth, h, 1.5) : ctx.rect(x, centerY - h / 2, barWidth, h);
          ctx.fill();
        }
      };
      draw();
    }
  }

  window.VaaniAgent = VaaniAgent;
  window.vaaniAgents = window.vaaniAgents || {};
})();
