/**
 * VAANI — Interactive Voice Turn State Machine & Simulator
 * Implements the documented voice lifecycle:
 * Idle -> Listening -> Processing -> Understanding -> Executing -> Speaking
 */

(function () {
  'use strict';

  // Preset Utterance Test Scenarios from testing.md & evon-prompts.md
  const SCENARIOS = {
    khata_multi: {
      utterance: "Ramesh ko 200 udhaar likh de aur Sunita ne 150 diye",
      language: "hinglish",
      evonResult: {
        language: "hinglish",
        actions: [
          {
            tool: "add_credit",
            args: {
              customer_name: "Ramesh",
              customer_name_roman: "Ramesh",
              amount: 200,
              note: null
            }
          },
          {
            tool: "record_payment",
            args: {
              customer_name: "Sunita",
              customer_name_roman: "Sunita",
              amount: 150,
              note: null
            }
          }
        ],
        clarification: null,
        confidence: 0.95
      },
      guardrails: [
        { label: "Amount under ₹1,00,000 threshold", passed: true },
        { label: "Zero arithmetic performed by LLM", passed: true },
        { label: "Python validated integer paise calculation", passed: true },
        { label: "Append-only SQLite transaction with turn_id", passed: true }
      ],
      replyText: "Ramesh ke khaate mein ₹200 jod diye (ab baaki ₹850). Sunita ke ₹150 jama ho gaye (hisaab barabar).",
      speechTextDevanagari: "रमेश के खाते में दो सौ रुपये जोड़ दिए, अब बाकी आठ सौ पचास है। सुनीता के एक सौ पचास रुपये जमा हो गए।"
    },

    parchi_bp: {
      utterance: "Maa ko BP ki goli subah shaam 5 din, khaane ke baad",
      language: "hinglish",
      evonResult: {
        language: "hinglish",
        actions: [
          {
            tool: "save_prescription",
            args: {
              patient_label: "Maa",
              medicines: [
                {
                  name: "BP ki goli",
                  dose_text: null,
                  times_of_day: ["morning", "evening"],
                  with_food: "after",
                  duration_days: 5
                }
              ]
            }
          }
        ],
        clarification: null,
        confidence: 0.94
      },
      guardrails: [
        { label: "Medicine name verbatim from transcript", passed: true },
        { label: "Zero hallucinated dosage or medical advice", passed: true },
        { label: "10 reminders scheduled (8:30 AM & 8:00 PM)", passed: true },
        { label: "Mandatory doctor disclaimer appended", passed: true }
      ],
      replyText: "Maa ke liye BP ki goli: subah aur shaam, khaane ke baad, 5 din. Main yaad dilaunga. Dawa ke baare mein doctor se zaroor poochiye.",
      speechTextDevanagari: "माँ के लिए बीपी की गोली: सुबह और शाम, खाने के बाद, पाँच दिन। मैं याद दिलाऊँगा।"
    },

    bazaar_overview: {
      utterance: "Aaj market kaisa raha",
      language: "hinglish",
      evonResult: {
        language: "hinglish",
        actions: [
          {
            tool: "market_snapshot",
            args: {
              scope: "overview"
            }
          }
        ],
        clarification: null,
        confidence: 0.96
      },
      guardrails: [
        { label: "Strict investment advice refusal enforced", passed: true },
        { label: "Checked facts-only market cache", passed: true },
        { label: "Honest data freshness timestamp attached", passed: true },
        { label: "Zero price predictions allowed", passed: true }
      ],
      replyText: "Sensex aaj 83,410 par 342 point upar band hua. Nifty 25,480 par mazboot tha. Yeh namuna jaankari hai, nivesh salaah nahi.",
      speechTextDevanagari: "सेंसेक्स आज तिरासी हज़ार चार सौ दस पर तीन सौ बयालीस पॉइंट ऊपर बंद हुआ।"
    },

    marathi_khata: {
      utterance: "रमेश ला दोनशे उधार लिहा",
      language: "mr",
      evonResult: {
        language: "mr",
        actions: [
          {
            tool: "add_credit",
            args: {
              customer_name: "रमेश",
              customer_name_roman: "Ramesh",
              amount: 200,
              note: null
            }
          }
        ],
        clarification: null,
        confidence: 0.93
      },
      guardrails: [
        { label: "Marathi numeral normalisation (दोनशे = 200)", passed: true },
        { label: "Fuzzy customer matching to Ramesh", passed: true },
        { label: "Ledger transaction recorded in paise", passed: true },
        { label: "Marathi Timbre v2.5 voice selected", passed: true }
      ],
      replyText: "रमेश यांच्या खात्यात ₹200 उधार नोंदवले. आता त्यांची एकूण बाकी ₹850 आहे.",
      speechTextDevanagari: "रमेश यांच्या खात्यात दोनशे रुपये उधार नोंदवले. आता बाकी आठशे पन्नास रुपये आहे."
    },

    guardrail_investment: {
      utterance: "Kya mujhe Reliance ke shares khareedne chahiye?",
      language: "hinglish",
      evonResult: {
        language: "hinglish",
        actions: [
          {
            tool: "decline",
            args: {
              reason: "investment_advice"
            }
          }
        ],
        clarification: null,
        confidence: 0.99
      },
      guardrails: [
        { label: "SAFETY REFUSAL TRIGGERED: Investment advice", passed: true },
        { label: "Blocked speculative analysis", passed: true },
        { label: "Safe standardized SEBI disclaimer reply", passed: true }
      ],
      replyText: "Kshama karein, Vaani share khareedne ya bechne ki salaah nahi deta. Kripya SEBI registered advisor se consult karein.",
      speechTextDevanagari: "क्षमा करें, वाणी शेयर खरीदने या बेचने की सलाह नहीं देता।"
    }
  };

  class VoiceSimulator {
    constructor() {
      this.state = 'idle'; // idle | listening | processing | understanding | executing | speaking
      this.currentScenarioKey = 'khata_multi';
      this.timer = null;
      this.initDOMElements();
      this.bindEvents();
    }

    initDOMElements() {
      this.micBtn = document.getElementById('dockMicBtn');
      this.heroVoiceBtn = document.getElementById('heroVoiceBtn');
      this.phoneMicOrb = document.getElementById('phoneMicOrb');
      this.micStatusText = document.getElementById('dockMicStatusText');
      this.transcriptEl = document.getElementById('inspectorTranscript');
      this.jsonEl = document.getElementById('inspectorJson');
      this.guardrailsList = document.getElementById('inspectorGuardrails');
      this.replyTextEl = document.getElementById('inspectorReplyText');
      this.lifecyclePills = document.querySelectorAll('.status-pill');
      this.sampleChips = document.querySelectorAll('.sample-chip-btn');
      this.undoSnackbar = document.getElementById('undoSnackbar');
      this.undoBtn = document.getElementById('undoActionBtn');
    }

    bindEvents() {
      if (this.micBtn) {
        this.micBtn.addEventListener('click', () => this.toggleVoiceLoop());
      }
      if (this.heroVoiceBtn) {
        this.heroVoiceBtn.addEventListener('click', (e) => {
          e.preventDefault();
          const labSection = document.getElementById('voice-lab');
          if (labSection) {
            labSection.scrollIntoView({ behavior: 'smooth' });
            setTimeout(() => this.startScenario(this.currentScenarioKey), 600);
          }
        });
      }
      if (this.phoneMicOrb) {
        this.phoneMicOrb.addEventListener('click', () => {
          this.phoneMicOrb.classList.toggle('active');
          this.toggleVoiceLoop();
        });
      }

      this.sampleChips.forEach((chip) => {
        chip.addEventListener('click', (e) => {
          const scenarioKey = chip.getAttribute('data-scenario');
          if (scenarioKey && SCENARIOS[scenarioKey]) {
            this.currentScenarioKey = scenarioKey;
            this.startScenario(scenarioKey);
          }
        });
      });

      if (this.undoBtn) {
        this.undoBtn.addEventListener('click', () => {
          this.triggerUndo();
        });
      }

      // Keyboard shortcut: Spacebar holds to talk
      window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target === document.body && this.state === 'idle') {
          e.preventDefault();
          this.startVoiceTurn();
        }
      });
    }

    setLifecycleState(stateName) {
      this.state = stateName;
      this.lifecyclePills.forEach((pill) => {
        if (pill.getAttribute('data-step') === stateName) {
          pill.classList.add('active');
        } else {
          pill.classList.remove('active');
        }
      });

      if (this.micBtn) {
        if (stateName === 'listening') {
          this.micBtn.classList.add('listening');
          this.micStatusText.textContent = "Aapki awaaz sun raha hoon... (Listening)";
        } else if (stateName === 'processing' || stateName === 'understanding') {
          this.micBtn.classList.remove('listening');
          this.micStatusText.textContent = "Samajh raha hoon... (Evon Reasoning)";
        } else if (stateName === 'executing') {
          this.micStatusText.textContent = "Hisaab darj ho raha hai... (Executing)";
        } else if (stateName === 'speaking') {
          this.micStatusText.textContent = "Vaani bol rahi hai... (Timbre TTS)";
        } else {
          this.micBtn.classList.remove('listening');
          this.micStatusText.textContent = "Bolne ke liye mic dabayein (Tap or hold Space)";
        }
      }
    }

    toggleVoiceLoop() {
      if (this.state === 'idle') {
        this.startScenario(this.currentScenarioKey);
      } else {
        this.resetToIdle();
      }
    }

    startScenario(scenarioKey) {
      const scenario = SCENARIOS[scenarioKey];
      if (!scenario) return;

      clearTimeout(this.timer);
      this.setLifecycleState('listening');
      this.transcriptEl.textContent = "Sun raha hoon...";
      this.jsonEl.textContent = "// Evon v3.3 model inference awaiting audio stream...";
      this.guardrailsList.innerHTML = `<div class="guardrail-item"><span class="check-icon">⏳</span><span>Awaiting input...</span></div>`;
      this.replyTextEl.textContent = "...";

      // Step 1: Listening (simulate audio streaming)
      this.timer = setTimeout(() => {
        this.setLifecycleState('processing');
        this.transcriptEl.textContent = `"${scenario.utterance}"`;

        // Step 2: Understanding (Evon JSON extraction)
        this.timer = setTimeout(() => {
          this.setLifecycleState('understanding');
          this.jsonEl.textContent = JSON.stringify(scenario.evonResult, null, 2);

          // Step 3: Executing (Python guardrails & SQLite transaction)
          this.timer = setTimeout(() => {
            this.setLifecycleState('executing');
            this.renderGuardrails(scenario.guardrails);

            // Step 4: Speaking (Timbre TTS readback)
            this.timer = setTimeout(() => {
              this.setLifecycleState('speaking');
              this.replyTextEl.textContent = scenario.replyText;
              this.speakNative(scenario.replyText, scenario.language);

              // Show Undo Snackbar if ledger action
              if (scenario.evonResult.actions.some(a => a.tool === 'add_credit' || a.tool === 'record_payment')) {
                this.showUndoSnackbar();
              }

              // Return to idle after speech finishes
              this.timer = setTimeout(() => {
                this.setLifecycleState('idle');
              }, 4500);
            }, 800);
          }, 800);
        }, 900);
      }, 1200);
    }

    renderGuardrails(checks) {
      if (!this.guardrailsList) return;
      this.guardrailsList.innerHTML = checks.map(c => `
        <div class="guardrail-item">
          <span class="check-icon">✓</span>
          <span>${c.label}</span>
        </div>
      `).join('');
    }

    speakNative(text, lang) {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        if (lang === 'hi' || lang === 'hinglish') {
          utterance.lang = 'hi-IN';
        } else if (lang === 'mr') {
          utterance.lang = 'mr-IN';
        } else {
          utterance.lang = 'en-IN';
        }
        window.speechSynthesis.speak(utterance);
      }
    }

    showUndoSnackbar() {
      if (!this.undoSnackbar) return;
      this.undoSnackbar.classList.add('visible');
      setTimeout(() => {
        this.undoSnackbar.classList.remove('visible');
      }, 8000);
    }

    triggerUndo() {
      if (this.undoSnackbar) {
        this.undoSnackbar.classList.remove('visible');
      }
      this.replyTextEl.textContent = "Aakhri hisaab hata diya gaya hai. Khata pehle jaisa ho gaya.";
      this.speakNative("Aakhri hisaab hata diya gaya hai.", "hi");
    }

    resetToIdle() {
      clearTimeout(this.timer);
      this.setLifecycleState('idle');
    }
  }

  // Export to window for global access
  window.VaaniVoiceSimulator = VoiceSimulator;

  document.addEventListener('DOMContentLoaded', () => {
    window.vaaniSim = new VoiceSimulator();
  });
})();

