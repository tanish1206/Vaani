/**
 * VAANI — Reactive Audio Waveform Visualizer
 * Draws golden/amber frequency bars and fluid sine waveforms
 */

(function () {
  'use strict';

  class AudioWaveformVisualizer {
    constructor(canvasId) {
      this.canvas = document.getElementById(canvasId);
      if (!this.canvas) return;
      this.ctx = this.canvas.getContext('2d');
      this.bars = 36;
      this.phase = 0;
      this.isSimulating = false;
      this.resize();
      window.addEventListener('resize', () => this.resize());
      this.animate();
    }

    resize() {
      if (!this.canvas) return;
      this.width = this.canvas.clientWidth;
      this.height = this.canvas.clientHeight;
      this.canvas.width = this.width * window.devicePixelRatio;
      this.canvas.height = this.height * window.devicePixelRatio;
      this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }

    animate() {
      requestAnimationFrame(() => this.animate());
      this.ctx.clearRect(0, 0, this.width, this.height);

      const barWidth = 3;
      const barSpacing = (this.width - (this.bars * barWidth)) / (this.bars - 1);
      const centerY = this.height / 2;

      this.phase += 0.05;

      for (let i = 0; i < this.bars; i++) {
        const x = i * (barWidth + barSpacing);
        // Harmonic waves formula
        const wave1 = Math.sin(this.phase + i * 0.2);
        const wave2 = Math.cos(this.phase * 0.8 + i * 0.15);
        const amplitude = this.isSimulating ? 18 : 8;
        const barHeight = Math.max(4, Math.abs(wave1 * wave2) * amplitude * 2);

        const gradient = this.ctx.createLinearGradient(0, centerY - barHeight / 2, 0, centerY + barHeight / 2);
        gradient.addColorStop(0, '#EAAA00');
        gradient.addColorStop(0.5, '#F58220');
        gradient.addColorStop(1, '#EAAA00');

        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 2);
        this.ctx.fill();
      }
    }

    setSimulating(active) {
      this.isSimulating = active;
    }
  }

  window.AudioWaveformVisualizer = AudioWaveformVisualizer;
})();

