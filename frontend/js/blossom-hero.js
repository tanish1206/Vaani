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
 * uses both SVG attributes and CSS styles for 100% cross-browser reliability,
 * and integrates real Web Audio microphone FFT analysis.
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

  function setSvgTransform(el, cx, cy, s, rot) {
    if (!el) return;
    const r = rot || 0;
    const t = 'translate(' + cx + ' ' + cy + ') scale(' + s.toFixed(4) + ') rotate(' + r.toFixed(2) + ') translate(' + (-cx) + ' ' + (-cy) + ')';
    el.setAttribute('transform', t);
    el.style.transform = '';
  }

  function setSvgOpacity(el, op) {
    if (!el) return;
    const val = clamp(op, 0, 1).toFixed(3);
    el.setAttribute('opacity', val);
    el.style.opacity = val;
  }

  class BotanicalBlossomHero {
    constructor() {
      this.track = document.getElementById('heroBlossomTrack');
      this.sticky = document.getElementById('heroBlossomSticky');
      this.svg = document.getElementById('botanicalBlossomSvg');
      this.progressFill = document.getElementById('heroBlossomProgress');
      this.scrollHint = document.getElementById('heroScrollHint');
      this.stageBadge = document.getElementById('heroBotanicalStageBadge');

      // Stem Elements
      this.stemPath = document.getElementById('stemPath');
      this.stemShadowPath = document.getElementById('stemShadowPath');
      this.stemHighlightPath = document.getElementById('stemHighlightPath');
      this.stemLength = 520;

      this.stemNodes = [
        document.getElementById('stemNode1'),
        document.getElementById('stemNode2'),
        document.getElementById('stemNode3'),
        document.getElementById('stemNode4')
      ];

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

      // Petal Tiers
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

      // Center & Acoustic Elements
      this.flowerCenter = document.getElementById('botanicalFlowerCenter');
      this.coreGlowCircle = document.getElementById('coreGlowCircle');
      this.coreHearth = document.getElementById('coreHearth');
      this.stamenFilaments = document.getElementById('stamenFilaments');
      this.pollenMotes = document.getElementById('pollenMotes');
      this.soundRings = document.getElementById('acousticSoundRings');
      this.waveformRibbon = document.getElementById('botanicalWaveformRibbon');

      // Reveal Nodes
      this.revealNodes = document.querySelectorAll('[data-blossom-reveal]');

      // Voice Controls
      this.heroVoiceBtn = document.getElementById('heroVoiceBtn');
      this.heroVoiceBtnText = document.getElementById('heroVoiceBtnText');
      this.phoneMicOrb = document.getElementById('phoneMicOrb');

      // State
      this.currentProgress = 0;
      this.targetProgress = 0;
      this.rafId = 0;
      this.isListening = false;
      this.audioContext = null;
      this.analyser = null;
      this.mediaStream = null;
      this.liveVolume = 0;

      if (!this.track || !this.sticky) return;

      this.init();
    }

    init() {
      // 1. Measure real stem path length
      if (this.stemPath && typeof this.stemPath.getTotalLength === 'function') {
        try {
          const l = this.stemPath.getTotalLength();
          if (l && l > 100) this.stemLength = l;
        } catch (e) {}
      }

      // 2. Initialize branch lengths
      this.branchLengths = [70, 75, 55, 55];
      this.branches.forEach((b, i) => {
        if (b && typeof b.getTotalLength === 'function') {
          try {
            const len = b.getTotalLength() || this.branchLengths[i];
            this.branchLengths[i] = len;
            b.setAttribute('stroke-dasharray', len + ' ' + len);
            b.setAttribute('stroke-dashoffset', String(len));
            b.style.strokeDasharray = len + ' ' + len;
            b.style.strokeDashoffset = String(len);
          } catch (e) {}
        }
      });

      // 3. Initialize stem stroke-dasharray & dashoffset to hidden state
      [this.stemPath, this.stemShadowPath, this.stemHighlightPath].forEach(path => {
        if (path) {
          path.setAttribute('stroke-dasharray', this.stemLength + ' ' + this.stemLength);
          path.setAttribute('stroke-dashoffset', String(this.stemLength));
          path.style.strokeDasharray = this.stemLength + ' ' + this.stemLength;
          path.style.strokeDashoffset = String(this.stemLength);
          setSvgOpacity(path, 0);
        }
      });

      // 4. Force immediate render of Stage 0 (Seed and ground only)
      this.renderStage(0);

      // 5. Bind Scroll & Resize handlers
      this.onScroll = this.onScroll.bind(this);
      this.onResize = this.onResize.bind(this);
      this.tick = this.tick.bind(this);

      window.addEventListener('scroll', this.onScroll, { passive: true });
      window.addEventListener('resize', this.onResize, { passive: true });
      window.addEventListener('wheel', this.onScroll, { passive: true });
      window.addEventListener('touchmove', this.onScroll, { passive: true });

      // 6. Bind Real Web Audio Microphone
      this.bindMicrophone();

      // 7. Initial sync & start 60fps tick loop
      this.onScroll();
      this.tick();
    }

    onScroll() {
      if (!this.track) return;
      const scrollY = window.pageYOffset || document.documentElement.scrollTop || 0;
      const trackRect = this.track.getBoundingClientRect();
      const trackTop = trackRect.top + scrollY;
      const trackHeight = this.track.offsetHeight;
      const windowHeight = window.innerHeight;
      const maxScroll = Math.max(1, trackHeight - windowHeight);
      const relativeScrolled = clamp(scrollY - trackTop, 0, maxScroll);
      this.targetProgress = relativeScrolled / maxScroll;
    }

    onResize() {
      if (this.stemPath && typeof this.stemPath.getTotalLength === 'function') {
        try {
          const l = this.stemPath.getTotalLength();
          if (l && l > 100) this.stemLength = l;
        } catch (e) {}
      }
      this.onScroll();
    }

    tick() {
      // Smooth linear interpolation (lerp) for weighted cinematic scrubbing
      const diff = this.targetProgress - this.currentProgress;
      if (Math.abs(diff) > 0.0008) {
        this.currentProgress = lerp(this.currentProgress, this.targetProgress, 0.16);
        this.renderStage(this.currentProgress);
      } else if (Math.abs(diff) > 0) {
        this.currentProgress = this.targetProgress;
        this.renderStage(this.currentProgress);
      } else if (this.currentProgress < 0.25 && this.seedAura) {
        // Subtle ambient pulse for the dormant seed at rest
        const pulse = 0.65 + 0.35 * Math.sin(Date.now() * 0.0035);
        const seedWarmth = smoothstep(0, 0.14, this.currentProgress);
        const auraOp = (0.5 + 0.5 * seedWarmth) * pulse;
        setSvgOpacity(this.seedAura, auraOp);
      }

      // Sample live microphone amplitude
      if (this.isListening && this.analyser) {
        this.sampleMicrophone();
      }

      this.rafId = requestAnimationFrame(this.tick);
    }

    /**
     * Renders all botanical layers based on scrub progress p (0.0 to 1.0)
     */
    renderStage(p) {
      // 1. Progress Bar & Scroll Hint
      if (this.progressFill) {
        this.progressFill.style.transform = 'scaleX(' + p.toFixed(4) + ')';
      }
      if (this.scrollHint) {
        this.scrollHint.classList.toggle('is-hidden', p > 0.12);
      }

      document.documentElement.style.setProperty('--hero-blossom-progress', String(p));

      // ----------------------------------------------------------------------
      // STAGE 1: SEED & GROUND (0% - 15%)
      // ----------------------------------------------------------------------
      const seedWarmth = smoothstep(0, 0.14, p);
      if (this.seedAura) {
        const pulse = 0.65 + 0.35 * Math.sin(Date.now() * 0.0035);
        const auraOp = p < 0.25 ? (0.5 + 0.5 * seedWarmth) * pulse : Math.max(0, 1 - (p - 0.25) * 4);
        setSvgOpacity(this.seedAura, auraOp);
      }
      if (this.seedBody) {
        const seedScale = p < 0.18 ? 1 + p * 0.5 : Math.max(0.7, 1 - (p - 0.18) * 1.6);
        setSvgTransform(this.seedBody, 720, 812, seedScale, -8);
      }
      if (this.seedEmbryo) {
        const embryoRise = smoothstep(0.06, 0.22, p) * -14;
        this.seedEmbryo.setAttribute('transform', 'translate(0, ' + embryoRise.toFixed(2) + ')');
        setSvgOpacity(this.seedEmbryo, p < 0.35 ? 1 : Math.max(0, 1 - (p - 0.35) * 3));
      }

      // ----------------------------------------------------------------------
      // STAGE 2: STEM GROWTH & BRANCHES (15% - 44%)
      // ----------------------------------------------------------------------
      const stemGrowth = smoothstep(0.10, 0.44, p);
      const stemOffset = this.stemLength * (1 - stemGrowth);

      [this.stemPath, this.stemShadowPath, this.stemHighlightPath].forEach(path => {
        if (path) {
          path.setAttribute('stroke-dashoffset', stemOffset.toFixed(2));
          path.style.strokeDashoffset = stemOffset.toFixed(2);
          setSvgOpacity(path, stemGrowth > 0.01 ? 1 : 0);
        }
      });

      // Stem nodes
      const nodeProgresses = [
        smoothstep(0.20, 0.30, p),
        smoothstep(0.26, 0.36, p),
        smoothstep(0.32, 0.42, p),
        smoothstep(0.38, 0.46, p)
      ];
      this.stemNodes.forEach((node, idx) => {
        if (node) {
          const np = nodeProgresses[idx];
          setSvgTransform(node, parseFloat(node.getAttribute('cx')), parseFloat(node.getAttribute('cy')), np);
          setSvgOpacity(node, np);
        }
      });

      // Branches draw as stem reaches each node
      const branchProgress = [
        smoothstep(0.22, 0.36, p),
        smoothstep(0.28, 0.40, p),
        smoothstep(0.32, 0.44, p),
        smoothstep(0.36, 0.48, p)
      ];

      this.branches.forEach((b, i) => {
        if (b && this.branchLengths[i]) {
          const bp = branchProgress[i];
          const offset = this.branchLengths[i] * (1 - bp);
          b.setAttribute('stroke-dashoffset', offset.toFixed(2));
          b.style.strokeDashoffset = offset.toFixed(2);
          setSvgOpacity(b, bp > 0.02 ? 1 : 0);
        }
      });

      // Leaves emerge & rotate around branch endpoints
      const leafOrigins = [
        [595, 618],
        [830, 538],
        [608, 434],
        [804, 385]
      ];
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
          const organicSway = Math.sin(Date.now() * 0.0018 + i * 1.4) * 2.5 * smoothstep(0.75, 1.0, p);
          const rot = leafRotations[i] + organicSway;
          const [lx, ly] = leafOrigins[i];
          setSvgTransform(leaf, lx, ly, s, rot);
          setSvgOpacity(leaf, clamp(s * 1.5, 0, 1));
        }
      });

      // Sub-calyx bracts
      if (this.bracts) {
        const bractScale = smoothstep(0.36, 0.50, p);
        setSvgTransform(this.bracts, 705, 315, bractScale);
        setSvgOpacity(this.bracts, bractScale);
      }

      // ----------------------------------------------------------------------
      // STAGE 3: BUD OPENING & PETAL UNCOROLLA (42% - 72%)
      // ----------------------------------------------------------------------
      const budForm = smoothstep(0.32, 0.48, p);
      const budOpen = smoothstep(0.44, 0.68, p);

      if (this.budCluster) {
        setSvgTransform(this.budCluster, 705, 310, budForm);
        setSvgOpacity(this.budCluster, budForm > 0.02 ? Math.max(0.05, 1 - budOpen * 0.95) : 0);
      }
      if (this.sepalLeft) {
        const sepalRot = lerp(0, -42, budOpen);
        setSvgTransform(this.sepalLeft, 705, 310, 1, sepalRot);
      }
      if (this.sepalRight) {
        const sepalRot = lerp(0, 42, budOpen);
        setSvgTransform(this.sepalRight, 705, 310, 1, sepalRot);
      }
      if (this.budSpire) {
        setSvgOpacity(this.budSpire, Math.max(0, 1 - budOpen * 1.5));
      }

      // Outer Petals (Tier 1) — Individual rotations around receptacle (705, 310)
      const outerBloom = smoothstep(0.45, 0.82, p);

      if (this.outerPetals.dorsal) {
        const s = outerBloom;
        const rot = lerp(-18, 0, smoothstep(0.48, 0.80, p));
        setSvgTransform(this.outerPetals.dorsal, 705, 310, s, rot);
        setSvgOpacity(this.outerPetals.dorsal, s > 0.02 ? 1 : 0);
      }
      if (this.outerPetals.upperLeft) {
        const s = outerBloom;
        const rot = lerp(32, 0, smoothstep(0.46, 0.82, p));
        setSvgTransform(this.outerPetals.upperLeft, 705, 310, s, rot);
        setSvgOpacity(this.outerPetals.upperLeft, s > 0.02 ? 1 : 0);
      }
      if (this.outerPetals.upperRight) {
        const s = outerBloom;
        const rot = lerp(-32, 0, smoothstep(0.46, 0.82, p));
        setSvgTransform(this.outerPetals.upperRight, 705, 310, s, rot);
        setSvgOpacity(this.outerPetals.upperRight, s > 0.02 ? 1 : 0);
      }
      if (this.outerPetals.lateralLeft) {
        const s = outerBloom;
        const rot = lerp(45, 0, smoothstep(0.50, 0.84, p));
        setSvgTransform(this.outerPetals.lateralLeft, 705, 310, s, rot);
        setSvgOpacity(this.outerPetals.lateralLeft, s > 0.02 ? 1 : 0);
      }
      if (this.outerPetals.lateralRight) {
        const s = outerBloom;
        const rot = lerp(-45, 0, smoothstep(0.50, 0.84, p));
        setSvgTransform(this.outerPetals.lateralRight, 705, 310, s, rot);
        setSvgOpacity(this.outerPetals.lateralRight, s > 0.02 ? 1 : 0);
      }
      if (this.outerPetals.inferiorLeft) {
        const s = outerBloom;
        const rot = lerp(35, 0, smoothstep(0.52, 0.86, p));
        setSvgTransform(this.outerPetals.inferiorLeft, 705, 310, s, rot);
        setSvgOpacity(this.outerPetals.inferiorLeft, s > 0.02 ? 1 : 0);
      }
      if (this.outerPetals.inferiorRight) {
        const s = outerBloom;
        const rot = lerp(-35, 0, smoothstep(0.52, 0.86, p));
        setSvgTransform(this.outerPetals.inferiorRight, 705, 310, s, rot);
        setSvgOpacity(this.outerPetals.inferiorRight, s > 0.02 ? 1 : 0);
      }

      // Intermediate Petals (Tier 2) — Phased expansion
      this.midPetals.forEach((petal, idx) => {
        if (petal) {
          const phaseLag = 0.52 + (idx * 0.02);
          const s = smoothstep(phaseLag, phaseLag + 0.28, p);
          const staggerRot = ((idx % 2 === 0 ? 1 : -1) * (18 - idx * 2)) * (1 - s);
          setSvgTransform(petal, 705, 310, s, staggerRot);
          setSvgOpacity(petal, s > 0.02 ? 0.95 : 0);
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
          setSvgTransform(petal, 705, 310, s, rot);
          setSvgOpacity(petal, s > 0.05 ? 1 : 0);
        }
      });

      // Core Stamen & Receptacle Hearth
      const fullBloom = smoothstep(0.70, 0.96, p);
      if (this.flowerCenter) {
        setSvgTransform(this.flowerCenter, 705, 310, fullBloom);
        setSvgOpacity(this.flowerCenter, fullBloom);
      }
      if (this.coreGlowCircle) {
        const livePulse = this.isListening ? 1 + this.liveVolume * 0.8 : 1;
        setSvgTransform(this.coreGlowCircle, 705, 310, fullBloom * livePulse);
      }
      if (this.stamenFilaments) {
        const stamenScale = smoothstep(0.72, 0.95, p);
        setSvgTransform(this.stamenFilaments, 705, 310, stamenScale);
      }
      if (this.pollenMotes) {
        const pollenScale = smoothstep(0.76, 0.98, p);
        setSvgTransform(this.pollenMotes, 705, 310, pollenScale);
      }

      // Concentric Acoustic Sound Wave Rings
      if (this.soundRings) {
        const soundScale = smoothstep(0.80, 1.0, p);
        setSvgOpacity(this.soundRings, soundScale * 0.85);
      }

      // Horizontal Waveform Frequency Bands
      if (this.waveformRibbon) {
        const waveScale = smoothstep(0.82, 1.0, p);
        setSvgOpacity(this.waveformRibbon, waveScale * 0.92);
      }

      // ----------------------------------------------------------------------
      // EDITORIAL TYPOGRAPHY & OVERLAY CHOREOGRAPHY
      // ----------------------------------------------------------------------
      if (this.stageBadge) {
        if (p < 0.20) {
          this.stageBadge.textContent = "01 / SOWING \u2022 DORMANT SEED IN SOIL";
        } else if (p < 0.45) {
          this.stageBadge.textContent = "02 / GERMINATION \u2022 ORGANIC STEM ASCENT";
        } else if (p < 0.75) {
          this.stageBadge.textContent = "03 / ANTHESIS \u2022 COROLLA UNFOLDING";
        } else {
          this.stageBadge.textContent = "04 / FULL BLOOM \u2022 BOLIYE, VAANI SAMBHAL LEGI";
        }
      }

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
          if (this.currentProgress < 0.85 && this.track) {
            const scrollY = window.pageYOffset || document.documentElement.scrollTop || 0;
            const trackRect = this.track.getBoundingClientRect();
            const trackTop = trackRect.top + scrollY;
            window.scrollTo({
              top: trackTop + this.track.offsetHeight * 0.88,
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
      this.liveVolume = avg / 128.0;

      if (this.soundRings) {
        const ringScale = 1 + this.liveVolume * 0.45;
        setSvgTransform(this.soundRings, 705, 310, ringScale);
      }

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
      window.removeEventListener('wheel', this.onScroll);
      window.removeEventListener('touchmove', this.onScroll);
      if (this.rafId) cancelAnimationFrame(this.rafId);
      this.stopMicrophone();
    }
  }

  function initHero() {
    if (!window.vaaniBlossomHero) {
      window.vaaniBlossomHero = new BotanicalBlossomHero();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHero);
  } else {
    initHero();
  }
})();
