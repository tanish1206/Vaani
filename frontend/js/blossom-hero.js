/**
 * VAANI — Cinematic Botanical Scroll-Driven Blossom Engine
 * 
 * Orchestrates a 4-stage coordinated botanical lifecycle:
 * Stage 1 (0% - 15%): Seed & Earth — Soil stratum, anchored taproot, pulsing amber seed, subtle illumination.
 * Stage 2 (15% - 42%): Stem Growth — Organic stem draws upward from ground, branches extend, leaves unfurl.
 * Stage 3 (42% - 72%): Flower Development — Bud calyx parts, multi-tiered petals rotate and unfold, core warms up.
 * Stage 4 (72% - 100%): Full Majestic Blossom — Full floral bloom, stamen radiance, drifting golden pollen,
 *                       acoustic waveform rings, editorial typography reveals ("Boliye. Vaani."), and active voice.
 *
 * Fully reversible, butter-smooth 60fps RAF lerp interpolation, zero scroll traps,
 * respects prefers-reduced-motion, and integrates real Web Audio microphone FFT analysis.
 */

(function () {
  'use strict';

  function clamp(v, min, max) {
    return Math.max(min, Math.min(max, v));
  }

  function smoothstep(edge0, edge1, x) {
    const t = clamp((x - edge0) / (edge1 - edge0), 0, 1);
    return t * t * (3 - 2 * t);
  }

  function lerp(start, end, factor) {
    return start + (end - start) * factor;
  }

  class BotanicalBlossomHero {
    constructor() {
      this.track = document.getElementById('heroBlossomTrack');
      this.sticky = document.getElementById('heroBlossomSticky');
      this.svg = document.getElementById('botanicalBlossomSvg');
      this.progressFill = document.getElementById('heroBlossomProgress');
      this.scrollHint = document.getElementById('heroScrollHint');

      // Stem Elements
      this.stemPath = document.getElementById('stemPath');
      this.stemShadowPath = document.getElementById('stemShadowPath');
      this.stemHighlightPath = document.getElementById('stemHighlightPath');
      this.stemLength = 515;

      // Seed Elements
      this.seedGroup = document.getElementById('botanicalSeed');
      this.seedAura = document.getElementById('seedAuraCircle');
      this.seedBody = document.getElementById('seedBody');
      this.seedEmbryo = document.getElementById('seedEmbryo');
      this.seedSeam = document.getElementById('seedSeam');

      // Foliage & Branches
      this.branches = [
        document.getElementById('branchPath1'),
        document.getElementById('branchPath2'),
        document.getElementById('branchPath3'),
        document.getElementById('branchPath4')
      ];
      this.leaves = [
        document.getElementById('botanicalLeaf1'),
        document.getElementById('botanicalLeaf2'),
        document.getElementById('botanicalLeaf3'),
        document.getElementById('botanicalLeaf4')
      ];
      this.bracts = document.getElementById('botanicalBracts');

      // Bud & Sepals
      this.budCluster = document.getElementById('botanicalBud');
      this.sepalLeft = document.getElementById('sepalLeft');
      this.sepalRight = document.getElementById('sepalRight');
      this.budSpire = document.getElementById('budSpire');

      // Petal Tiers (Independently controllable layers)
      this.outerPetals = {
        dorsal: document.getElementById('petalOuterDorsal'),
        upperLeft: document.getElementById('petalOuterUpperLeft'),
        upperRight: document.getElementById('petalOuterUpperRight'),
        lateralLeft: document.getElementById('petalOuterLateralLeft'),
        lateralRight: document.getElementById('petalOuterLateralRight'),
        inferiorLeft: document.getElementById('petalOuterInferiorLeft'),
        inferiorRight: document.getElementById('petalOuterInferiorRight')
      };

      this.midPetals = [
        document.getElementById('petalMid1'),
        document.getElementById('petalMid2'),
        document.getElementById('petalMid3'),
        document.getElementById('petalMid4'),
        document.getElementById('petalMid5'),
        document.getElementById('petalMid6'),
        document.getElementById('petalMid7'),
        document.getElementById('petalMid8')
      ];

      this.innerPetals = [
        document.getElementById('petalInner1'),
        document.getElementById('petalInner2'),
        document.getElementById('petalInner3'),
        document.getElementById('petalInner4'),
        document.getElementById('petalInner5'),
        document.getElementById('petalInner6')
      ];

      // Flower Center & Acoustic Glow
      this.flowerCenter = document.getElementById('botanicalFlowerCenter');
      this.coreGlowCircle = document.getElementById('coreGlowCircle');
      this.stamenFilaments = document.getElementById('stamenFilaments');
      this.pollenMotes = document.getElementById('pollenMotes');
      this.soundRings = document.getElementById('acousticSoundRings');
      this.waveformRibbon = document.getElementById('botanicalWaveformRibbon');

      // Typography & UI Reveal Nodes
      this.revealNodes = document.querySelectorAll('[data-blossom-reveal]');
      this.headlineBoliye = document.getElementById('heroHeadlineBoliye');
      this.headlineVaani = document.getElementById('heroHeadlineVaani');
      this.supportingCopy = document.getElementById('heroSupportingCopy');
      this.ctaGroup = document.querySelector('.hero-cta-group');

      // Voice Buttons & Mic Interaction
      this.heroVoiceBtn = document.getElementById('heroVoiceBtn');
      this.heroVoiceBtnText = document.getElementById('heroVoiceBtnText');
      this.phoneMicOrb = document.getElementById('phoneMicOrb');

      // Animation State
      this.currentProgress = 0;
      this.targetProgress = 0;
      this.rafId = 0;
      this.isListening = false;
      this.audioContext = null;
      this.analyser = null;
      this.mediaStream = null;
      this.liveVolume = 0;
      this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (!this.track || !this.sticky) return;

      this.init();
    }

    init() {
      // Measure real stem path length for dasharray calculation
      if (this.stemPath && typeof this.stemPath.getTotalLength === 'function') {
        try {
          this.stemLength = this.stemPath.getTotalLength() || 515;
        } catch (e) {
          this.stemLength = 515;
        }
      }

      // Initialize branch lengths
      this.branchLengths = this.branches.map(b => {
        if (b && typeof b.getTotalLength === 'function') {
          try {
            const len = b.getTotalLength();
            b.style.strokeDasharray = `${len} ${len}`;
            b.style.strokeDashoffset = len;
            return len;
          } catch (e) {
            return 80;
          }
        }
        return 80;
      });

      // Prepare Stem Stroke Dasharray
      [this.stemPath, this.stemShadowPath, this.stemHighlightPath].forEach(path => {
        if (path) {
          path.style.strokeDasharray = `${this.stemLength} ${this.stemLength}`;
          path.style.strokeDashoffset = this.stemLength;
        }
      });

      // Bind Scroll and Resize
      this.onScroll = this.onScroll.bind(this);
      this.onResize = this.onResize.bind(this);
      this.tick = this.tick.bind(this);

      window.addEventListener('scroll', this.onScroll, { passive: true });
      window.addEventListener('resize', this.onResize, { passive: true });

      // Microphone activation on CTA
      this.bindMicrophone();

      // If reduced motion, jump straight to 100% full blossom
      if (this.reducedMotion) {
        this.targetProgress = 1;
        this.currentProgress = 1;
        this.renderStage(1);
        return;
      }

      // Initial layout tick
      this.onScroll();
      this.tick();
    }

    onScroll() {
      const rect = this.track.getBoundingClientRect();
      const maxScroll = Math.max(1, rect.height - window.innerHeight);
      const scrolled = clamp(-rect.top, 0, maxScroll);
      this.targetProgress = scrolled / maxScroll;
    }

    onResize() {
      if (this.stemPath && typeof this.stemPath.getTotalLength === 'function') {
        try {
          this.stemLength = this.stemPath.getTotalLength() || 515;
        } catch (e) {}
      }
      this.onScroll();
    }

    tick() {
      // Smooth linear interpolation (lerp) for cinematic inertia
      const diff = this.targetProgress - this.currentProgress;
      if (Math.abs(diff) > 0.0005) {
        this.currentProgress = lerp(this.currentProgress, this.targetProgress, 0.12);
        this.renderStage(this.currentProgress);
      } else if (Math.abs(diff) > 0) {
        this.currentProgress = this.targetProgress;
        this.renderStage(this.currentProgress);
      }

      // Live Microphone Audio Visualizer Modulation
      if (this.isListening && this.analyser) {
        this.sampleMicrophone();
      }

      this.rafId = requestAnimationFrame(this.tick);
    }

    /**
     * Renders the 4 coordinated botanical stages based on scrub progress p (0.0 to 1.0)
     */
    renderStage(p) {
      // 1. Progress Bar & Scroll Hint
      if (this.progressFill) {
        this.progressFill.style.transform = `scaleX(${p})`;
      }
      if (this.scrollHint) {
        this.scrollHint.classList.toggle('is-hidden', p > 0.12);
      }

      // Expose CSS variable for background ambient warmth
      document.documentElement.style.setProperty('--hero-blossom-progress', String(p));

      // ----------------------------------------------------------------------
      // STAGE 1: SEED & GROUND (0% - 15%)
      // ----------------------------------------------------------------------
      const seedWarmth = smoothstep(0, 0.12, p);
      if (this.seedAura) {
        const pulse = 0.6 + 0.4 * Math.sin(Date.now() * 0.003);
        const auraOpacity = p < 0.25 ? (0.4 + 0.5 * seedWarmth) * pulse : Math.max(0, 1 - (p - 0.25) * 4);
        this.seedAura.style.opacity = String(auraOpacity);
      }
      if (this.seedBody) {
        const seedScale = p < 0.18 ? 1 + p * 0.4 : Math.max(0.7, 1 - (p - 0.18) * 1.5);
        this.seedBody.style.transformOrigin = '720px 812px';
        this.seedBody.style.transform = `scale(${seedScale})`;
      }
      if (this.seedEmbryo) {
        const embryoRise = smoothstep(0.06, 0.20, p) * -12;
        this.seedEmbryo.style.transform = `translateY(${embryoRise}px)`;
        this.seedEmbryo.style.opacity = String(p < 0.35 ? 1 : Math.max(0, 1 - (p - 0.35) * 3));
      }

      // ----------------------------------------------------------------------
      // STAGE 2: STEM GROWTH & BRANCHES (15% - 42%)
      // ----------------------------------------------------------------------
      const stemGrowth = smoothstep(0.10, 0.44, p);
      const stemOffset = this.stemLength * (1 - stemGrowth);

      [this.stemPath, this.stemShadowPath, this.stemHighlightPath].forEach(path => {
        if (path) {
          path.style.strokeDashoffset = String(stemOffset);
          path.style.opacity = stemGrowth > 0.01 ? '1' : '0';
        }
      });

      // Branches draw as the stem grows past each node
      const branchProgress = [
        smoothstep(0.22, 0.36, p),
        smoothstep(0.28, 0.40, p),
        smoothstep(0.32, 0.44, p),
        smoothstep(0.36, 0.48, p)
      ];

      this.branches.forEach((b, i) => {
        if (b && this.branchLengths[i]) {
          const bp = branchProgress[i];
          b.style.strokeDashoffset = String(this.branchLengths[i] * (1 - bp));
          b.style.opacity = bp > 0.02 ? '1' : '0';
        }
      });

      // Leaves emerge & unfurl with natural rotation
      const leafScales = [
        smoothstep(0.24, 0.40, p),
        smoothstep(0.30, 0.44, p),
        smoothstep(0.34, 0.48, p),
        smoothstep(0.38, 0.52, p)
      ];

      const leafRotations = [
        lerp(-28, 0, leafScales[0]),
        lerp(28, 0, leafScales[1]),
        lerp(-20, 0, leafScales[2]),
        lerp(20, 0, leafScales[3])
      ];

      this.leaves.forEach((leaf, i) => {
        if (leaf) {
          const s = leafScales[i];
          const rot = leafRotations[i];
          leaf.style.transform = `scale(${s}) rotate(${rot}deg)`;
          leaf.style.opacity = String(clamp(s * 1.5, 0, 1));
        }
      });

      // Sub-calyx bracts cradling bud apex
      if (this.bracts) {
        const bractScale = smoothstep(0.36, 0.50, p);
        this.bracts.style.transformOrigin = '705px 315px';
        this.bracts.style.transform = `scale(${bractScale})`;
        this.bracts.style.opacity = String(bractScale);
      }

      // ----------------------------------------------------------------------
      // STAGE 3: BUD OPENING & PETAL DEVELOPMENT (42% - 72%)
      // ----------------------------------------------------------------------
      const budForm = smoothstep(0.32, 0.48, p);
      const budOpen = smoothstep(0.44, 0.68, p);

      if (this.budCluster) {
        this.budCluster.style.opacity = String(budForm > 0.02 ? Math.max(0.1, 1 - budOpen * 0.9) : 0);
      }
      if (this.sepalLeft) {
        const sepalRot = lerp(0, -42, budOpen);
        this.sepalLeft.style.transform = `scale(${budForm}) rotate(${sepalRot}deg)`;
      }
      if (this.sepalRight) {
        const sepalRot = lerp(0, 42, budOpen);
        this.sepalRight.style.transform = `scale(${budForm}) rotate(${sepalRot}deg)`;
      }
      if (this.budSpire) {
        this.budSpire.style.opacity = String(Math.max(0, 1 - budOpen * 1.5));
      }

      // Outer Petals unfold with individual rotation and non-linear spring easing
      const outerBloom = smoothstep(0.45, 0.82, p);

      if (this.outerPetals.dorsal) {
        const s = outerBloom;
        const rot = lerp(-18, 0, smoothstep(0.48, 0.80, p));
        this.outerPetals.dorsal.style.transform = `scale(${s}) rotate(${rot}deg)`;
        this.outerPetals.dorsal.style.opacity = String(s > 0.05 ? 1 : s * 20);
      }
      if (this.outerPetals.upperLeft) {
        const s = outerBloom;
        const rot = lerp(32, 0, smoothstep(0.46, 0.82, p));
        this.outerPetals.upperLeft.style.transform = `scale(${s}) rotate(${rot}deg)`;
        this.outerPetals.upperLeft.style.opacity = String(s > 0.05 ? 1 : s * 20);
      }
      if (this.outerPetals.upperRight) {
        const s = outerBloom;
        const rot = lerp(-32, 0, smoothstep(0.46, 0.82, p));
        this.outerPetals.upperRight.style.transform = `scale(${s}) rotate(${rot}deg)`;
        this.outerPetals.upperRight.style.opacity = String(s > 0.05 ? 1 : s * 20);
      }
      if (this.outerPetals.lateralLeft) {
        const s = outerBloom;
        const rot = lerp(45, 0, smoothstep(0.50, 0.84, p));
        this.outerPetals.lateralLeft.style.transform = `scale(${s}) rotate(${rot}deg)`;
        this.outerPetals.lateralLeft.style.opacity = String(s > 0.05 ? 1 : s * 20);
      }
      if (this.outerPetals.lateralRight) {
        const s = outerBloom;
        const rot = lerp(-45, 0, smoothstep(0.50, 0.84, p));
        this.outerPetals.lateralRight.style.transform = `scale(${s}) rotate(${rot}deg)`;
        this.outerPetals.lateralRight.style.opacity = String(s > 0.05 ? 1 : s * 20);
      }
      if (this.outerPetals.inferiorLeft) {
        const s = outerBloom;
        const rot = lerp(35, 0, smoothstep(0.52, 0.86, p));
        this.outerPetals.inferiorLeft.style.transform = `scale(${s}) rotate(${rot}deg)`;
        this.outerPetals.inferiorLeft.style.opacity = String(s > 0.05 ? 1 : s * 20);
      }
      if (this.outerPetals.inferiorRight) {
        const s = outerBloom;
        const rot = lerp(-35, 0, smoothstep(0.52, 0.86, p));
        this.outerPetals.inferiorRight.style.transform = `scale(${s}) rotate(${rot}deg)`;
        this.outerPetals.inferiorRight.style.opacity = String(s > 0.05 ? 1 : s * 20);
      }

      // Intermediate Petals follow slightly phased
      const midBloom = smoothstep(0.54, 0.88, p);
      this.midPetals.forEach((petal, idx) => {
        if (petal) {
          const phaseLag = 0.52 + (idx * 0.02);
          const s = smoothstep(phaseLag, phaseLag + 0.28, p);
          const staggerRot = ((idx % 2 === 0 ? 1 : -1) * (18 - idx * 2)) * (1 - s);
          petal.style.transform = `scale(${s}) rotate(${staggerRot}deg)`;
          petal.style.opacity = String(s > 0.02 ? 0.95 : 0);
        }
      });

      // ----------------------------------------------------------------------
      // STAGE 4: FULL BLOSSOM, STAMEN RADIANCE & AUDIO WAVEFORMS (72% - 100%)
      // ----------------------------------------------------------------------
      const innerBloom = smoothstep(0.66, 0.94, p);
      this.innerPetals.forEach((petal, idx) => {
        if (petal) {
          const s = innerBloom;
          const rot = ((idx % 2 === 0 ? 1 : -1) * 12) * (1 - s);
          petal.style.transform = `scale(${s}) rotate(${rot}deg)`;
          petal.style.opacity = String(s > 0.05 ? 1 : 0);
        }
      });

      // Core Stamen Warmth & Hearth Glow
      const fullBloom = smoothstep(0.70, 0.96, p);
      if (this.flowerCenter) {
        this.flowerCenter.style.opacity = String(fullBloom);
      }
      if (this.coreGlowCircle) {
        const livePulse = this.isListening ? 1 + this.liveVolume * 0.8 : 1;
        this.coreGlowCircle.style.transformOrigin = '705px 310px';
        this.coreGlowCircle.style.transform = `scale(${fullBloom * livePulse})`;
      }
      if (this.stamenFilaments) {
        const stamenScale = smoothstep(0.72, 0.95, p);
        this.stamenFilaments.style.transformOrigin = '705px 310px';
        this.stamenFilaments.style.transform = `scale(${stamenScale})`;
      }
      if (this.pollenMotes) {
        const pollenScale = smoothstep(0.76, 0.98, p);
        this.pollenMotes.style.transformOrigin = '705px 310px';
        this.pollenMotes.style.transform = `scale(${pollenScale})`;
      }

      // Concentric Acoustic Sound Wave Rings
      if (this.soundRings) {
        const soundScale = smoothstep(0.80, 1.0, p);
        this.soundRings.style.opacity = String(soundScale * 0.85);
      }

      // Horizontal Waveform Frequency Bands
      if (this.waveformRibbon) {
        const waveScale = smoothstep(0.82, 1.0, p);
        this.waveformRibbon.style.opacity = String(waveScale * 0.92);
      }

      // ----------------------------------------------------------------------
      // TYPOGRAPHY & OVERLAY CHOREOGRAPHY
      // ----------------------------------------------------------------------
      this.revealNodes.forEach(node => {
        const start = parseFloat(node.dataset.revealAt || '0.7');
        const end = parseFloat(node.dataset.revealEnd || String(Math.min(1, start + 0.16)));
        const revealT = smoothstep(start, end, p);
        node.style.setProperty('--blossom-reveal', String(revealT));
        node.classList.toggle('is-revealed', revealT > 0.85);
      });
    }

    /**
     * Binds real Web Audio API microphone handling to the primary CTA & Phone Mic Orb
     */
    bindMicrophone() {
      const handleMicToggle = async (e) => {
        if (e) e.preventDefault();

        if (this.isListening) {
          this.stopMicrophone();
          return;
        }

        try {
          if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showMicToast("Microphone browser support unavailable. Opening Vaani App...");
            setTimeout(() => { window.location.href = '/app'; }, 1200);
            return;
          }

          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          this.mediaStream = stream;
          this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
          const source = this.audioContext.createMediaStreamSource(stream);
          this.analyser = this.audioContext.createAnalyser();
          this.analyser.fftSize = 64;
          source.connect(this.analyser);

          this.isListening = true;
          if (this.heroVoiceBtn) {
            this.heroVoiceBtn.classList.add('is-listening');
          }
          if (this.heroVoiceBtnText) {
            this.heroVoiceBtnText.textContent = "Sun raha hoon... (Listening)";
          }
          if (this.phoneMicOrb) {
            this.phoneMicOrb.classList.add('active');
          }

          // Advance flower bloom if not already scrolled
          if (this.currentProgress < 0.85) {
            window.scrollTo({
              top: this.track.offsetTop + this.track.offsetHeight * 0.88,
              behavior: 'smooth'
            });
          }
        } catch (err) {
          console.warn('[VAANI] Microphone permission notice:', err);
          this.showMicToast("Microphone permission denied. Aap Bol-Khata ya Parchi mein type karke bol sakte hain.");
          if (this.heroVoiceBtnText) {
            this.heroVoiceBtnText.textContent = "Start Speaking";
          }
        }
      };

      if (this.heroVoiceBtn) {
        this.heroVoiceBtn.addEventListener('click', handleMicToggle);
      }
      if (this.phoneMicOrb) {
        this.phoneMicOrb.addEventListener('click', handleMicToggle);
      }
    }

    stopMicrophone() {
      this.isListening = false;
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(t => t.stop());
        this.mediaStream = null;
      }
      if (this.audioContext && this.audioContext.state !== 'closed') {
        this.audioContext.close();
      }
      this.analyser = null;
      this.liveVolume = 0;

      if (this.heroVoiceBtn) {
        this.heroVoiceBtn.classList.remove('is-listening');
      }
      if (this.heroVoiceBtnText) {
        this.heroVoiceBtnText.textContent = "Start Speaking";
      }
      if (this.phoneMicOrb) {
        this.phoneMicOrb.classList.remove('active');
      }
    }

    sampleMicrophone() {
      if (!this.analyser) return;
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      this.analyser.getByteFrequencyData(dataArray);

      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const avg = sum / dataArray.length;
      this.liveVolume = avg / 128.0; // 0.0 to 1.0+

      // Modulate sound rings with real voice decibels
      if (this.soundRings) {
        const ringScale = 1 + this.liveVolume * 0.45;
        this.soundRings.style.transformOrigin = '705px 310px';
        this.soundRings.style.transform = `scale(${ringScale})`;
      }

      // Notify window audio visualizer if connected
      if (window.vaaniVisualizer && typeof window.vaaniVisualizer.setLiveAmplitude === 'function') {
        window.vaaniVisualizer.setLiveAmplitude(this.liveVolume);
      }
    }

    showMicToast(msg) {
      let toast = document.getElementById('vaaniMicToast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'vaaniMicToast';
        toast.className = 'vaani-mic-toast';
        document.body.appendChild(toast);
      }
      toast.textContent = msg;
      toast.classList.add('is-visible');
      setTimeout(() => {
        toast.classList.remove('is-visible');
      }, 4200);
    }

    destroy() {
      window.removeEventListener('scroll', this.onScroll);
      window.removeEventListener('resize', this.onResize);
      if (this.rafId) cancelAnimationFrame(this.rafId);
      this.stopMicrophone();
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    window.vaaniBlossomHero = new BotanicalBlossomHero();
  });
})();
