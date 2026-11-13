## Disclaimer: this file, unlike the other code in this demo, was AI generated.

## Hardware Setup
# Connect these 5 GPIO pins through resistors to a single shared node, then through a 10µF capacitor (positive leg toward the resistors) to an amplifier or audio jack:
# • GP10: Channel 1 — Pulse 1 (Lead Melody) via 2.2kΩ
# • GP12: Channel 2 — Pulse 2 (Harmony) via 2.2kΩ
# • GP14: Channel 3 — Triangle-style Square (Bass) via 3.3kΩ
# • GP16: Channel 4 — Arpeggio / Chords via 3.3kΩ
# • GP18: Channel 5 — PIO Noise (Kick/Snare/Hi-Hat) via 4.7kΩ

import rp2
from machine import Pin, PWM
import uasyncio as asyncio
import math

# ==========================================
# 1. PIO NOISE CHANNEL (Channel 5 on GP18)
# ==========================================
@rp2.asm_pio(out_init=rp2.PIO.OUT_LOW)
def nes_noise():
    set(x, 1)
    wrap_target()
    mov(isr, x)
    in_(x, 1)
    mov(y, isr)
    jmp(x_not_y, "one")
    set(y, 0)
    jmp("shift")
    label("one")
    set(y, 1)
    label("shift")
    mov(osr, x)
    out(null, 1)
    in_(y, 1)
    mov(x, isr)
    out(pins, 1)
    wrap()

noise_pin = Pin(18, Pin.OUT)
sm_noise = rp2.StateMachine(0, nes_noise, freq=12000, out_base=noise_pin)

def trigger_drum(drum_type):
    if drum_type == "H":      # Crisp Hi-Hat
        sm_noise.init(nes_noise, freq=48000, out_base=noise_pin)
        sm_noise.active(1)
    elif drum_type == "S":    # Punchy Snare
        sm_noise.init(nes_noise, freq=15000, out_base=noise_pin)
        sm_noise.active(1)
    elif drum_type == "K":    # Low 8-bit Kick
        sm_noise.init(nes_noise, freq=3200, out_base=noise_pin)
        sm_noise.active(1)
    else:
        sm_noise.active(0)
        noise_pin.value(0)

# ==========================================
# 2. PWM SYNTH CHANNELS
# ==========================================
ch1 = PWM(Pin(10)) # Pulse 1: Lead Melody + SFX Hijack
ch2 = PWM(Pin(12)) # Pulse 2: Harmony / Counter-melody
ch3 = PWM(Pin(14)) # Bass: Pumping Oom-Pah Bassline
ch4 = PWM(Pin(16)) # Arp / Off-beat Chord Stabs

DUTY_LEAD = 16384  # 25% pulse (iconic Game Boy / NES lead timbre)
DUTY_HARM = 8192   # 12.5% pulse (thin harmony)
DUTY_BASS = 32768  # 50% square (deep bass)
DUTY_ARP  = 16384  # 25% pulse (staccato off-beat chords)

def set_pwm(channel, freq, duty):
    if freq > 0:
        channel.freq(int(freq))
        channel.duty_u16(duty)
    else:
        channel.duty_u16(0)

# ==========================================
# 3. TETRIS SOUND EFFECTS LIBRARY (20ms Frames)
# ==========================================
SFX_LIBRARY = {
    # Subtle side-to-side piece shift blip
    "move": [
        (523, 8192, 0), (659, 8192, 0)
    ],
    # Classic two-tone piece rotation chirp
    "rotate": [
        (440, 16384, 0), (587, 16384, 0), (880, 16384, 0)
    ],
    # Hard drop thud
    "drop": [
        (180, 32768, 9000), (120, 32768, 6000), (75, 32768, 3500)
    ],
    # Single/Double Line Clear chime
    "line": [
        (523, 16384, 0), (659, 16384, 0), (784, 16384, 0),
        (1047, 16384, 0), (1047, 16384, 0), (1047, 16384, 0)
    ],
    # 4-Line "TETRIS!" celebratory fanfare
    "tetris": [
        (659, 16384, 25000), (659, 16384, 0),
        (784, 16384, 25000), (784, 16384, 0),
        (988, 16384, 25000), (988, 16384, 0),
        (1319, 16384, 35000), (1319, 16384, 0),
        (1175, 16384, 0), (1319, 16384, 35000),
        (1319, 16384, 0), (1319, 16384, 0)
    ],
    # Classic descending Game Over jingle (~1.1 seconds)
    "gameover": [
        # B4 -> G#4 -> E4 -> B3 -> G#3 -> E3 -> Low Rumble
        (494, 16384, 0), (494, 16384, 0), (494, 16384, 0), (494, 16384, 0), (0, 0, 0),
        (415, 16384, 0), (415, 16384, 0), (415, 16384, 0), (415, 16384, 0), (0, 0, 0),
        (330, 16384, 0), (330, 16384, 0), (330, 16384, 0), (330, 16384, 0), (0, 0, 0),
        (247, 16384, 0), (247, 16384, 0), (247, 16384, 0), (0, 0, 0),
        (208, 16384, 0), (208, 16384, 0), (208, 16384, 0), (0, 0, 0),
        (165, 32768, 4000), (165, 32768, 3000), (165, 32768, 2000),
        (110, 32768, 1500), (110, 32768, 1200), (110, 32768, 900),
        (82,  32768, 700),  (82,  32768, 500),  (82,  32768, 400),
        (82,  32768, 0),    (82,  32768, 0),    (82,  32768, 0),
        (82,  32768, 0),    (82,  32768, 0),    (82,  32768, 0),
    ]
}

active_sfx = None
sfx_frame_index = 0

def play_sfx(name):
    global active_sfx, sfx_frame_index
    if name in SFX_LIBRARY:
        active_sfx = SFX_LIBRARY[name]
        sfx_frame_index = 0

def audio_game_over():
    """Stops the background theme, mutes Ch2-Ch4, and plays the Game Over jingle."""
    global music_playing
    music_playing = False
    for ch in (ch2, ch3, ch4):
        ch.duty_u16(0)
    play_sfx("gameover")

# ==========================================
# 4. NOTE FREQUENCIES & TETRIS THEME (KOROBEINIKI)
# ==========================================
# Octave 2 & 3 (Bass)
E2, A2, B2 = 82, 110, 123
C3, D3, E3, F3, G3, GS3, A3, B3 = 131, 147, 165, 175, 196, 208, 220, 247
# Octave 4 (Harmony & Stabs)
C4, D4, E4, F4, G4, GS4, A4, B4 = 262, 294, 330, 349, 392, 415, 440, 494
# Octave 5 (Lead Melody)
C5, D5, E5, F5, G5, A5 = 523, 587, 659, 698, 784, 880

# 1 step = 1 eighth note (fast Russian dance tempo)
# Format: (Lead, Harmony, Bass, Offbeat_Stab, Drum, Lead_FX)
tetris_theme = [
    # --- PART A: Bars 1-2 (E7 -> Am) ---
    (E5, B4, E2, 0,   "K", None),
    (E5, B4, 0,  GS4, "H", None),
    (B4, GS4, E3, 0,  "S", None),
    (C5, A4, 0,  B4,  "H", None),
    (D5, B4, E2, 0,   "K", None),
    (D5, B4, 0,  GS4, "H", None),
    (C5, A4, E3, 0,   "S", None),
    (B4, GS4, 0, B4,  "H", None),

    (A4, E4, A2, 0,   "K", None),
    (A4, E4, 0,  C4,  "H", None),
    (A4, E4, E3, 0,   "S", None),
    (C5, A4, 0,  E4,  "H", None),
    (E5, C5, A2, 0,   "K", "VIB"),
    (E5, C5, 0,  C4,  "H", "VIB"),
    (D5, B4, E3, 0,   "S", None),
    (C5, A4, 0,  E4,  "H", None),

    # --- PART A: Bars 3-4 (E7 -> Am) ---
    (B4, GS4, E2, 0,  "K", None),
    (B4, GS4, 0,  GS4,"H", None),
    (B4, GS4, E3, 0,  "S", None),
    (C5, A4, 0,  B4,  "H", None),
    (D5, B4, E2, 0,   "K", None),
    (D5, B4, 0,  GS4, "H", None),
    (E5, C5, E3, 0,   "S", "SLIDE"),
    (E5, C5, 0,  B4,  "H", "VIB"),

    (C5, A4, A2, 0,   "K", None),
    (C5, A4, 0,  C4,  "H", None),
    (A4, E4, E3, 0,   "S", None),
    (A4, E4, 0,  E4,  "H", None),
    (A4, E4, A2, 0,   "K", "VIB"),
    (0,  0,  0,  C4,  "H", None),
    (0,  0,  E3, 0,   "S", None),
    (0,  0,  0,  0,   "H", None),

    # --- PART A2: Bars 5-6 (Dm -> Am) ---
    (0,  0,  D3, 0,   "K", None),
    (D5, F4, 0,  A4,  "H", None),
    (D5, F4, A3, 0,   "S", None),
    (F5, A4, 0,  D4,  "H", None),
    (A5, D5, D3, 0,   "K", "VIB"),
    (A5, D5, 0,  A4,  "H", "VIB"),
    (G5, C5, A3, 0,   "S", None),
    (F5, A4, 0,  D4,  "H", None),

    (E5, C5, A2, 0,   "K", "VIB"),
    (E5, C5, 0,  C4,  "H", "VIB"),
    (E5, C5, E3, 0,   "S", None),
    (C5, A4, 0,  E4,  "H", None),
    (E5, C5, A2, 0,   "K", "VIB"),
    (E5, C5, 0,  C4,  "H", "VIB"),
    (D5, B4, E3, 0,   "S", None),
    (C5, A4, 0,  E4,  "H", None),

    # --- PART A2: Bars 7-8 (E7 -> Am Turnaround) ---
    (B4, GS4, E2, 0,  "K", None),
    (B4, GS4, 0,  GS4,"H", None),
    (B4, GS4, E3, 0,  "S", None),
    (C5, A4, 0,  B4,  "H", None),
    (D5, B4, E2, 0,   "K", None),
    (D5, B4, 0,  GS4, "H", None),
    (E5, C5, E3, 0,   "S", "SLIDE"),
    (E5, C5, 0,  B4,  "H", "VIB"),

    (C5, A4, A2, 0,   "K", None),
    (C5, A4, 0,  C4,  "H", None),
    (A4, E4, E3, 0,   "S", None),
    (A4, E4, 0,  E4,  "H", None),
    (A4, E4, A2, 0,   "K", "VIB"),
    (0,  0,  E2, 0,   "S", None),
    (0,  0,  A2, 0,   "S", None),
    (0,  0,  0,  0,   "H", None),

    # --- PART B: Bridge (Bars 9-12) ---
    (E5, C5, A2, 0,   "K", "VIB"),
    (E5, C5, 0,  E4,  "H", "VIB"),
    (E5, C5, E3, 0,   "S", "VIB"),
    (E5, C5, 0,  E4,  "H", "VIB"),
    (C5, A4, A2, 0,   "K", "VIB"),
    (C5, A4, 0,  C4,  "H", "VIB"),
    (C5, A4, E3, 0,   "S", "VIB"),
    (C5, A4, 0,  C4,  "H", "VIB"),

    (D5, B4, GS3, 0,  "K", "VIB"),
    (D5, B4, 0,  B3,  "H", "VIB"),
    (D5, B4, E3, 0,   "S", "VIB"),
    (D5, B4, 0,  B3,  "H", "VIB"),
    (B4, GS4, GS3, 0, "K", "VIB"),
    (B4, GS4, 0,  GS4,"H", "VIB"),
    (B4, GS4, E3, 0,  "S", "VIB"),
    (B4, GS4, 0,  GS4,"H", "VIB"),

    (C5, A4, A2, 0,   "K", "VIB"),
    (C5, A4, 0,  C4,  "H", "VIB"),
    (C5, A4, E3, 0,   "S", "VIB"),
    (C5, A4, 0,  C4,  "H", "VIB"),
    (A4, E4, A2, 0,   "K", "VIB"),
    (A4, E4, 0,  E4,  "H", "VIB"),
    (A4, E4, E3, 0,   "S", "VIB"),
    (A4, E4, 0,  E4,  "H", "VIB"),

    (GS4, E4, E2, 0,  "K", "VIB"),
    (GS4, E4, 0,  B3,  "H", "VIB"),
    (GS4, E4, E3, 0,   "S", "VIB"),
    (GS4, E4, 0,  B3,  "H", "VIB"),
    (B4, GS4, E2, 0,  "K", "VIB"),
    (B4, GS4, 0,  GS4,"H", "VIB"),
    (0,  0,  E3, 0,   "S", None),
    (0,  0,  0,  0,   "H", None),
]

# ==========================================
# 5. 50Hz ENGINE WITH TEMPO ACCELERATION
# ==========================================
music_playing = True
# TICKS_PER_STEP controls game speed!
# 8 = Normal Level 1 (~150 BPM), 6 = Fast Level 5, 5 = Panic Mode!
ticks_per_step = 8

async def chiptune_engine():
    global active_sfx, sfx_frame_index
    last_lead_freq = 0

    while True:
        if not music_playing and active_sfx is None:
            for ch in (ch1, ch2, ch3, ch4):
                ch.duty_u16(0)
            sm_noise.active(0)
            noise_pin.value(0)
            await asyncio.sleep_ms(20)
            continue

        for lead, harm, bass, stab, drum, fx in tetris_theme:
            if not music_playing and active_sfx is None:
                break

            if music_playing:
                set_pwm(ch2, harm, DUTY_HARM)
                set_pwm(ch3, bass, DUTY_BASS)
                set_pwm(ch4, stab, DUTY_ARP)
                if active_sfx is None:
                    trigger_drum(drum)

            start_freq = last_lead_freq if (fx == "SLIDE" and last_lead_freq > 0) else lead
            current_steps = ticks_per_step

            for tick in range(current_steps):
                # --- SFX HIJACK CHECK ---
                if active_sfx is not None:
                    if sfx_frame_index < len(active_sfx):
                        sfx_freq, sfx_duty, sfx_noise = active_sfx[sfx_frame_index]
                        set_pwm(ch1, sfx_freq, sfx_duty)
                        if sfx_noise > 0:
                            sm_noise.init(nes_noise, freq=sfx_noise, out_base=noise_pin)
                            sm_noise.active(1)
                        else:
                            sm_noise.active(0)
                            noise_pin.value(0)
                        sfx_frame_index += 1
                    else:
                        active_sfx = None
                        ch1.duty_u16(0)
                        sm_noise.active(0)
                        noise_pin.value(0)

                # --- NORMAL TETRIS MUSIC ---
                elif music_playing:
                    # Crisp 40ms percussion envelope
                    if tick == 2:
                        sm_noise.active(0)
                        noise_pin.value(0)

                    # Staccato bass & off-beat chord stabs for authentic Russian bounce
                    if tick == current_steps - 2:
                        ch3.duty_u16(0)
                        ch4.duty_u16(0)

                    if lead > 0:
                        current_freq = lead
                        if fx == "SLIDE" and start_freq > 0:
                            progress = (tick + 1) / current_steps
                            current_freq = start_freq + (lead - start_freq) * progress
                        elif fx == "VIB" and tick >= 2:
                            wobble = math.sin(tick * 1.9) * (lead * 0.015)
                            current_freq = lead + wobble
                            set_pwm(ch1, current_freq, DUTY_LEAD)
                        else:
                            ch1.duty_u16(0)
                            await asyncio.sleep_ms(20)
                    if lead > 0:
                        last_lead_freq = lead

# ==========================================
# 6. DEMO MAIN LOOP (TESTS MUSIC, SFX & SPEED-UP)
# ==========================================

async def audio():
    global ticks_per_step
    asyncio.create_task(chiptune_engine())
    print("Playing Tetris Theme (Type A)!")
    demo_sfx = ["move", "rotate", "drop", "line", "tetris"]
    idx = 0
    while True:
        await asyncio.sleep_ms(3500)
        sfx = demo_sfx[idx]
        print("SFX:", sfx)
        play_sfx(sfx)
        # Just like real Tetris, clearing a 4-line "tetris" speeds up the music!
        if sfx == "tetris":
            ticks_per_step = 6 if ticks_per_step == 8 else 8
            print("Tempo changed! ticks_per_step =", ticks_per_step)
            idx = (idx + 1) % len(demo_sfx)
