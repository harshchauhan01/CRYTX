/**
 * soundFX.js
 * Synthesizes retro terminal sounds using Web Audio API so we don't need MP3 files.
 */

class SoundEngine {
  constructor() {
    this.ctx = null;
  }

  init() {
    if (!this.ctx) {
      // AudioContext requires a user gesture to start in modern browsers
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playTone(freq, type, duration, vol=0.1) {
    if (!this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      
      gain.gain.setValueAtTime(vol, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
      
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      console.warn("Audio playback failed", e);
    }
  }

  blip() {
    this.init();
    this.playTone(800, 'square', 0.05, 0.02);
  }

  execute() {
    this.init();
    // Two fast tones for success
    this.playTone(600, 'square', 0.1, 0.05);
    setTimeout(() => this.playTone(1200, 'square', 0.2, 0.05), 100);
  }

  error() {
    this.init();
    // Low harsh buzz
    this.playTone(150, 'sawtooth', 0.3, 0.1);
  }
}

export const soundFX = new SoundEngine();
