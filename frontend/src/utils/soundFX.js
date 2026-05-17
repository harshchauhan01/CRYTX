/**
 * CRYTX — Sound Engine
 * Synthesizes retro terminal sounds using Web Audio API.
 */

class SoundEngine {
  constructor() { this.ctx = null; }

  init() {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
  }

  _play(type, freq, duration, volume = 0.15) {
    if (!this.ctx) this.init();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
    gain.gain.setValueAtTime(volume, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + duration);
  }

  hover()   { this._play('triangle', 800, 0.05, 0.08); }
  click()   { this._play('square', 1200, 0.03, 0.1); }
  buy()     { this._play('sawtooth', 400, 0.15, 0.12); setTimeout(() => this._play('sawtooth', 800, 0.1, 0.1), 80); }
  sell()    { this._play('sawtooth', 800, 0.15, 0.12); setTimeout(() => this._play('sawtooth', 400, 0.1, 0.1), 80); }
  success() { this._play('sine', 880, 0.1, 0.1); setTimeout(() => this._play('sine', 1100, 0.15, 0.1), 100); }
  error()   { this._play('square', 200, 0.2, 0.15); }
  notify()  { this._play('sine', 660, 0.08, 0.08); setTimeout(() => this._play('sine', 880, 0.12, 0.08), 100); }
}

export const soundFX = new SoundEngine();
