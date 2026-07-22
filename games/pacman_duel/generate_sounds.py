import numpy as np
from scipy.io.wavfile import write
import os

def synth_waveform(freq, duration, wave_type="sine", sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    if wave_type == "sine":
        wave = np.sin(freq * t * 2 * np.pi)
    elif wave_type == "square":
        wave = np.sign(np.sin(freq * t * 2 * np.pi))
    elif wave_type == "sawtooth":
        wave = 2 * (t * freq - np.floor(0.5 + t * freq))
    elif wave_type == "noise":
        wave = np.random.uniform(-1, 1, len(t))
    
    # Fade out
    fade_len = int(sample_rate * 0.05)
    if len(wave) > fade_len:
        wave[-fade_len:] *= np.linspace(1, 0, fade_len)
        wave[:fade_len] *= np.linspace(0, 1, fade_len)
        
    return wave

def save_wav(filename, wave, sample_rate=44100):
    # Normalize and convert to 16-bit PCM
    wave = wave / np.max(np.abs(wave))
    audio = np.int16(wave * 32767)
    write(filename, sample_rate, audio)

def generate_sounds():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    sr = 44100
    
    # 1. Chomp (Waka waka)
    # Fast alternating triangle/sine waves
    t = np.linspace(0, 0.3, int(sr * 0.3), False)
    freq1 = 300 + 100 * np.sin(t * 20 * np.pi)
    chomp = np.sin(freq1 * t * 2 * np.pi)
    save_wav(os.path.join(out_dir, "chomp.wav"), chomp)
    
    # 2. Eat Ghost
    t = np.linspace(0, 0.5, int(sr * 0.5), False)
    freq2 = 800 + 400 * np.sin(t * 15 * np.pi) * np.exp(-t*5)
    eat_ghost = np.sign(np.sin(freq2 * t * 2 * np.pi))
    save_wav(os.path.join(out_dir, "eat_ghost.wav"), eat_ghost)
    
    # 3. Power Pellet (Siren)
    t = np.linspace(0, 0.4, int(sr * 0.4), False)
    freq3 = 400 + 150 * np.sin(t * 8 * np.pi)
    power = np.sin(freq3 * t * 2 * np.pi)
    save_wav(os.path.join(out_dir, "power_pellet.wav"), power)
    
    # 4. Death
    t = np.linspace(0, 1.5, int(sr * 1.5), False)
    freq4 = np.linspace(600, 100, len(t))
    death = np.sign(np.sin(freq4 * t * 2 * np.pi)) * np.exp(-t*2)
    save_wav(os.path.join(out_dir, "death.wav"), death)
    
if __name__ == "__main__":
    generate_sounds()
    print("Sounds generated.")
