"""
VOICE PROFILE DATABASE
======================

All niche voice presets live here.

Important:
- These are BASE settings.
- Human variation engine will modify them slightly.
- Same niche ki har video me micro variation hogi.
"""

VOICE_PROFILES = {

    "quantum_future": {

        "name": "Quantum Future",

        "voice": {
            "stability": 28,
            "similarity": 80,
            "style": 32,
            "speed": 0.92,
            "pitch": 0.00,
            "energy": 0.55,
        },

        "pauses": {
            "comma": 0.20,
            "thinking": 0.65,
            "dramatic": 0.85,
            "reveal": 1.20,
        },

        "breathing": {
            "enabled": True,
            "volume_db": -33,
            "frequency": "medium",
        },

        "eq": {
            "hpf": 80,
            "warmth_db": 2.0,
            "warmth_freq": 140,
            "mud_cut_db": -2.0,
            "mud_freq": 300,
            "presence_db": 2.0,
            "presence_freq": 4000,
            "air_db": 1.0,
            "air_freq": 10000,
        },

        "compression": {
            "ratio": 2.5,
            "threshold": -20,
            "attack": 20,
            "release": 120,
        },

        "deesser": {
            "freq": 6500,
            "reduction": 3,
        },

        "saturation": 7,
        "reverb": 5,
        "music_db": -27,
        "peak_db": -1,
    },

    "stoic_wisdom": {

        "name": "Stoic Wisdom",

        "voice": {
            "stability": 48,
            "similarity": 85,
            "style": 18,
            "speed": 0.89,
            "pitch": -0.05,
            "energy": 0.35,
        },

        "pauses": {
            "comma": 0.25,
            "thinking": 0.90,
            "dramatic": 1.25,
            "reveal": 1.50,
        },

        "breathing": {
            "enabled": True,
            "volume_db": -35,
            "frequency": "low",
        },

        "eq": {
            "hpf": 75,
            "warmth_db": 2.0,
            "warmth_freq": 150,
            "mud_cut_db": -2.0,
            "mud_freq": 300,
            "presence_db": 1.5,
            "presence_freq": 3500,
            "air_db": 1.0,
            "air_freq": 9000,
        },

        "compression": {
            "ratio": 2.0,
            "threshold": -22,
            "attack": 25,
            "release": 120,
        },

        "deesser": {
            "freq": 6500,
            "reduction": 2,
        },

        "saturation": 8,
        "reverb": 4,
        "music_db": -29,
        "peak_db": -1,
    },

    "luxury_lifestyle": {

        "name": "Luxury Lifestyle",

        "voice": {
            "stability": 42,
            "similarity": 88,
            "style": 22,
            "speed": 0.93,
            "pitch": -0.03,
            "energy": 0.45,
        },

        "pauses": {
            "comma": 0.22,
            "thinking": 0.80,
            "dramatic": 1.00,
            "reveal": 1.30,
        },

        "breathing": {
            "enabled": True,
            "volume_db": -36,
            "frequency": "low",
        },

        "eq": {
            "hpf": 80,
            "warmth_db": 2.0,
            "warmth_freq": 150,
            "mud_cut_db": -2.0,
            "mud_freq": 300,
            "presence_db": 2.0,
            "presence_freq": 3500,
            "air_db": 2.0,
            "air_freq": 11000,
        },

        "compression": {
            "ratio": 2.5,
            "threshold": -20,
            "attack": 20,
            "release": 100,
        },

        "deesser": {
            "freq": 6500,
            "reduction": 3,
        },

        "saturation": 6,
        "reverb": 5,
        "music_db": -28,
        "peak_db": -1,
    },

    "mystery": {

        "name": "Mystery",

        "voice": {
            "stability": 32,
            "similarity": 82,
            "style": 38,
            "speed": 0.91,
            "pitch": -0.08,
            "energy": 0.50,
        },

        "pauses": {
            "comma": 0.22,
            "thinking": 0.90,
            "dramatic": 1.30,
            "reveal": 1.80,
        },

        "breathing": {
            "enabled": True,
            "volume_db": -34,
            "frequency": "medium",
        },

        "eq": {
            "hpf": 80,
            "warmth_db": 1.5,
            "warmth_freq": 140,
            "mud_cut_db": -2,
            "mud_freq": 300,
            "presence_db": 2,
            "presence_freq": 4000,
            "air_db": 1,
            "air_freq": 9000,
        },

        "compression": {
            "ratio": 2.5,
            "threshold": -20,
            "attack": 20,
            "release": 100,
        },

        "deesser": {
            "freq": 6500,
            "reduction": 3,
        },

        "saturation": 7,
        "reverb": 5,
        "music_db": -30,
        "peak_db": -1,
    },

    "interior_design": {

        "name": "Interior Design",

        "voice": {
            "stability": 46,
            "similarity": 88,
            "style": 18,
            "speed": 0.91,
            "pitch": 0.02,
            "energy": 0.30,
        },

        "pauses": {
            "comma": 0.25,
            "thinking": 0.80,
            "dramatic": 1.10,
            "reveal": 1.40,
        },

        "breathing": {
            "enabled": True,
            "volume_db": -36,
            "frequency": "low",
        },

        "eq": {
            "hpf": 75,
            "warmth_db": 2,
            "warmth_freq": 150,
            "mud_cut_db": -1.5,
            "mud_freq": 300,
            "presence_db": 1.5,
            "presence_freq": 3500,
            "air_db": 1.5,
            "air_freq": 10000,
        },

        "compression": {
            "ratio": 2,
            "threshold": -22,
            "attack": 25,
            "release": 120,
        },

        "deesser": {
            "freq": 6000,
            "reduction": 2,
        },

        "saturation": 6,
        "reverb": 5,
        "music_db": -28,
        "peak_db": -1,
    },

    "finance_simulation": {

        "name": "Finance Simulation",

        "voice": {
            "stability": 52,
            "similarity": 90,
            "style": 15,
            "speed": 0.95,
            "pitch": -0.02,
            "energy": 0.40,
        },

        "pauses": {
            "comma": 0.20,
            "thinking": 0.60,
            "dramatic": 0.95,
            "reveal": 1.20,
        },

        "breathing": {
            "enabled": True,
            "volume_db": -38,
            "frequency": "very_low",
        },

        "eq": {
            "hpf": 80,
            "warmth_db": 1.5,
            "warmth_freq": 150,
            "mud_cut_db": -2,
            "mud_freq": 300,
            "presence_db": 2,
            "presence_freq": 4000,
            "air_db": 1,
            "air_freq": 10000,
        },

        "compression": {
            "ratio": 2.5,
            "threshold": -20,
            "attack": 20,
            "release": 100,
        },

        "deesser": {
            "freq": 7000,
            "reduction": 3,
        },

        "saturation": 5,
        "reverb": 3,
        "music_db": -30,
        "peak_db": -1,
    },
}