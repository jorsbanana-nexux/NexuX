/**
 * Web Audio API synthesizer for futuristic space sound effects & ambient deep-space music.
 * Produces ultra-lightweight, zero-latency feedback without heavy audio asset downloads.
 */

class SoundEngine {
  private ctx: AudioContext | null = null;
  private isMuted: boolean = false;
  private isAmbientPlaying: boolean = false;
  private ambientGain: GainNode | null = null;
  private ambientOscillators: OscillatorNode[] = [];
  private ambientFilter: BiquadFilterNode | null = null;
  private lfoGain: GainNode | null = null;
  private lfo: OscillatorNode | null = null;

  private initContext() {
    if (!this.ctx && typeof window !== 'undefined') {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        this.ctx = new AudioCtx();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  public toggleMute(): boolean {
    this.isMuted = !this.isMuted;
    if (this.ambientGain && this.ctx) {
      this.ambientGain.gain.setTargetAtTime(
        this.isMuted ? 0 : 0.08,
        this.ctx.currentTime,
        0.1
      );
    }
    return this.isMuted;
  }

  public getMuted(): boolean {
    return this.isMuted;
  }

  public isAmbientActive(): boolean {
    return this.isAmbientPlaying && !this.isMuted;
  }

  /**
   * Start generative, soothing deep space ambient drone (Sci-Fi chord harmonics)
   */
  public startAmbientMusic() {
    try {
      this.initContext();
      if (!this.ctx) return;
      if (this.isAmbientPlaying) return;

      this.isAmbientPlaying = true;
      const now = this.ctx.currentTime;

      // Master ambient gain
      this.ambientGain = this.ctx.createGain();
      this.ambientGain.gain.setValueAtTime(0.001, now);
      this.ambientGain.gain.exponentialRampToValueAtTime(
        this.isMuted ? 0.001 : 0.065,
        now + 2.5
      );

      // Low-pass warmth filter simulating deep space void
      this.ambientFilter = this.ctx.createBiquadFilter();
      this.ambientFilter.type = 'lowpass';
      this.ambientFilter.frequency.setValueAtTime(320, now);
      this.ambientFilter.Q.setValueAtTime(2.0, now);

      // LFO for slow atmospheric breathing / pulsar modulation (0.1 Hz)
      this.lfo = this.ctx.createOscillator();
      this.lfoGain = this.ctx.createGain();
      this.lfo.frequency.setValueAtTime(0.08, now);
      this.lfoGain.gain.setValueAtTime(80, now);
      this.lfo.connect(this.lfoGain);
      this.lfoGain.connect(this.ambientFilter.frequency);
      this.lfo.start();

      // Deep space root notes (Cosmic D minor / A fifth chord harmonics: 55Hz, 110Hz, 164.8Hz, 220Hz)
      const chordFrequencies = [55.0, 110.0, 164.81, 220.0, 329.63];
      this.ambientOscillators = [];

      chordFrequencies.forEach((freq, idx) => {
        const osc = this.ctx!.createOscillator();
        const oscGain = this.ctx!.createGain();

        osc.type = idx % 2 === 0 ? 'sine' : 'triangle';
        // Gentle detuning for lush space chorus effect
        osc.frequency.setValueAtTime(freq + (idx - 2) * 0.35, now);

        const baseVol = 0.04 / (idx + 1);
        oscGain.gain.setValueAtTime(baseVol, now);

        osc.connect(oscGain);
        oscGain.connect(this.ambientFilter!);
        osc.start(now);
        this.ambientOscillators.push(osc);
      });

      this.ambientFilter.connect(this.ambientGain);
      this.ambientGain.connect(this.ctx.destination);
    } catch {
      // Audio autoplay policy fallback
    }
  }

  /**
   * Stop ambient background music with smooth fade out
   */
  public stopAmbientMusic() {
    if (!this.isAmbientPlaying || !this.ctx || !this.ambientGain) return;
    try {
      const now = this.ctx.currentTime;
      this.ambientGain.gain.linearRampToValueAtTime(0.0001, now + 1.2);
      setTimeout(() => {
        this.ambientOscillators.forEach((osc) => {
          try {
            osc.stop();
            osc.disconnect();
          } catch {}
        });
        this.ambientOscillators = [];
        if (this.lfo) {
          try {
            this.lfo.stop();
            this.lfo.disconnect();
          } catch {}
          this.lfo = null;
        }
        this.isAmbientPlaying = false;
      }, 1300);
    } catch {}
  }

  public toggleAmbientMusic(): boolean {
    if (this.isAmbientPlaying) {
      this.stopAmbientMusic();
      return false;
    } else {
      this.startAmbientMusic();
      return true;
    }
  }

  /**
   * Subtle high-frequency blip on interactive element hover
   */
  public playHover() {
    if (this.isMuted) return;
    try {
      this.initContext();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(950, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1400, this.ctx.currentTime + 0.035);

      gain.gain.setValueAtTime(0.012, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.035);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.035);
    } catch {}
  }

  /**
   * Snappy digital sci-fi instrument click
   */
  public playClick() {
    if (this.isMuted) return;
    try {
      this.initContext();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(750, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(220, this.ctx.currentTime + 0.05);

      gain.gain.setValueAtTime(0.03, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.05);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.05);
    } catch {}
  }

  /**
   * Warp Speed Hyperspace Drive sound effect (Pitch ascending + white noise burst)
   */
  public playWarpSpeed() {
    if (this.isMuted) return;
    try {
      this.initContext();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      const filter = this.ctx.createBiquadFilter();

      osc.type = 'sawtooth';
      filter.type = 'lowpass';

      osc.frequency.setValueAtTime(90, now);
      osc.frequency.exponentialRampToValueAtTime(1200, now + 0.6);
      osc.frequency.exponentialRampToValueAtTime(320, now + 1.2);

      filter.frequency.setValueAtTime(400, now);
      filter.frequency.exponentialRampToValueAtTime(4000, now + 0.6);
      filter.frequency.exponentialRampToValueAtTime(300, now + 1.2);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.05, now + 0.4);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.2);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 1.2);
    } catch {}
  }

  /**
   * Futuristic swoosh / beam sound for generation launch & transitions
   */
  public playSwoosh() {
    if (this.isMuted) return;
    try {
      this.initContext();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(180, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(950, this.ctx.currentTime + 0.18);
      osc.frequency.exponentialRampToValueAtTime(440, this.ctx.currentTime + 0.35);

      gain.gain.setValueAtTime(0.001, this.ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.04, this.ctx.currentTime + 0.1);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.35);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.35);
    } catch {}
  }

  /**
   * Success chime when generation completes
   */
  public playSuccess() {
    if (this.isMuted) return;
    try {
      this.initContext();
      if (!this.ctx) return;

      const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
      notes.forEach((freq, index) => {
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();

        const startTime = this.ctx!.currentTime + index * 0.08;
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, startTime);

        gain.gain.setValueAtTime(0.025, startTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.3);

        osc.connect(gain);
        gain.connect(this.ctx!.destination);

        osc.start(startTime);
        osc.stop(startTime + 0.3);
      });
    } catch {}
  }
}

export const sound = new SoundEngine();
