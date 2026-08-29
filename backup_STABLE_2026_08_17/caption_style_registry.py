# caption_style_registry.py
"""
Complete Registry of 30+ Dynamic Caption Styles supporting 3 Modes:
- line: Displays full lines of text
- phrase: Displays 2-4 word chunks
- word_by_word: Displays individual words with highlight/animations
"""

CAPTION_STYLES = {
    # --- STANDARD & CLEAN STYLES (1-10) ---
    "clean_subtitle": {
        "font": "Arial-Bold",
        "font_size": 48,
        "primary_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 3,
        "bg_box": False,
        "glow": False,
        "animation": "none",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "crystal_cyan": {
        "font": "Impact",
        "font_size": 52,
        "primary_color": "#00E5FF",
        "stroke_color": "#002B36",
        "stroke_width": 4,
        "bg_box": True,
        "bg_color": (0, 0, 0, 160),
        "glow": True,
        "glow_color": "#00E5FF",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "flame_red": {
        "font": "Impact",
        "font_size": 54,
        "primary_color": "#FF2A2A",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "bg_box": False,
        "glow": True,
        "glow_color": "#FF2A2A",
        "animation": "bounce",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "gold_impact": {
        "font": "Impact",
        "font_size": 55,
        "primary_color": "#FFD700",
        "stroke_color": "#3A2800",
        "stroke_width": 4,
        "bg_box": False,
        "glow": False,
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "tech_slate": {
        "font": "DejaVuSans-Bold",
        "font_size": 46,
        "primary_color": "#E2E8F0",
        "stroke_color": "#0F172A",
        "stroke_width": 3,
        "bg_box": True,
        "bg_color": (15, 23, 42, 210),
        "glow": False,
        "animation": "none",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "emerald_glow": {
        "font": "Arial-Bold",
        "font_size": 50,
        "primary_color": "#10B981",
        "stroke_color": "#064E3B",
        "stroke_width": 4,
        "bg_box": False,
        "glow": True,
        "glow_color": "#10B981",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "royal_purple": {
        "font": "Impact",
        "font_size": 52,
        "primary_color": "#A855F7",
        "stroke_color": "#3B0764",
        "stroke_width": 4,
        "bg_box": True,
        "bg_color": (0, 0, 0, 180),
        "glow": True,
        "glow_color": "#A855F7",
        "animation": "bounce",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "sunset_orange": {
        "font": "Impact",
        "font_size": 52,
        "primary_color": "#FF7A00",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "bg_box": False,
        "glow": False,
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "bold_yellow": {
        "font": "Impact",
        "font_size": 56,
        "primary_color": "#FFE600",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "bg_box": False,
        "glow": False,
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "minimal_dark": {
        "font": "Arial-Bold",
        "font_size": 44,
        "primary_color": "#18181B",
        "stroke_color": "#FFFFFF",
        "stroke_width": 2,
        "bg_box": True,
        "bg_color": (255, 255, 255, 220),
        "glow": False,
        "animation": "none",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },

    # --- HIGH CONTRAST & DYNAMIC DUAL COLOR (11-20) ---
    "cyber_pink": {
        "font": "Impact",
        "font_size": 54,
        "primary_color": "#FF007A",
        "secondary_color": "#00E5FF",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "bg_box": False,
        "glow": True,
        "glow_color": "#FF007A",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "lime_tracker": {
        "font": "Impact",
        "font_size": 52,
        "primary_color": "#A3E635",
        "secondary_color": "#FFFFFF",
        "stroke_color": "#1A2E05",
        "stroke_width": 4,
        "bg_box": True,
        "bg_color": (0, 0, 0, 200),
        "glow": False,
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "electric_violet": {
        "font": "Impact",
        "font_size": 54,
        "primary_color": "#7C3AED",
        "secondary_color": "#F472B6",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "bg_box": False,
        "glow": True,
        "glow_color": "#7C3AED",
        "animation": "bounce",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "ice_cube": {
        "font": "DejaVuSans-Bold",
        "font_size": 48,
        "primary_color": "#E0F2FE",
        "stroke_color": "#0369A1",
        "stroke_width": 4,
        "bg_box": True,
        "bg_color": (3, 105, 161, 150),
        "glow": True,
        "glow_color": "#38BDF8",
        "animation": "none",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "vivid_crimson": {
        "font": "Impact",
        "font_size": 55,
        "primary_color": "#E11D48",
        "secondary_color": "#FFE4E6",
        "stroke_color": "#4C0519",
        "stroke_width": 4,
        "bg_box": False,
        "glow": True,
        "glow_color": "#E11D48",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "toxic_green": {
        "font": "Impact",
        "font_size": 52,
        "primary_color": "#22C55E",
        "stroke_color": "#052E16",
        "stroke_width": 4,
        "bg_box": True,
        "bg_color": (0, 0, 0, 220),
        "glow": True,
        "glow_color": "#22C55E",
        "animation": "bounce",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "hot_magenta": {
        "font": "Impact",
        "font_size": 54,
        "primary_color": "#E11D48",
        "secondary_color": "#F43F5E",
        "stroke_color": "#000000",
        "stroke_width": 4,
        "bg_box": False,
        "glow": True,
        "glow_color": "#F43F5E",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "solar_flare": {
        "font": "Impact",
        "font_size": 56,
        "primary_color": "#F59E0B",
        "secondary_color": "#EF4444",
        "stroke_color": "#451A03",
        "stroke_width": 5,
        "bg_box": False,
        "glow": True,
        "glow_color": "#F59E0B",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "deep_ocean": {
        "font": "DejaVuSans-Bold",
        "font_size": 48,
        "primary_color": "#38BDF8",
        "stroke_color": "#0C4A6E",
        "stroke_width": 4,
        "bg_box": True,
        "bg_color": (12, 74, 110, 200),
        "glow": False,
        "animation": "none",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "pure_white_stroke": {
        "font": "Impact",
        "font_size": 50,
        "primary_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 6,
        "bg_box": False,
        "glow": False,
        "animation": "none",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },

    # --- PREMIUM ULTRA & TRI-COLOR MULTI-WORD STYLES (21-30+) ---
    "ultra_tri_color_sweep": {
        "font": "Impact",
        "font_size": 56,
        "primary_color": "#00E5FF",
        "secondary_color": "#FFE600",
        "tertiary_color": "#FF007A",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "bg_box": True,
        "bg_color": (0, 0, 0, 190),
        "glow": True,
        "glow_color": "#00E5FF",
        "animation": "tri_color_sequence",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "neon_cyberpunk_paid": {
        "font": "Impact",
        "font_size": 58,
        "primary_color": "#00FF66",
        "secondary_color": "#FF0055",
        "tertiary_color": "#00FFFF",
        "stroke_color": "#050505",
        "stroke_width": 6,
        "bg_box": True,
        "bg_color": (10, 10, 15, 230),
        "glow": True,
        "glow_color": "#00FF66",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "dual_tone_gradient_word": {
        "font": "Impact",
        "font_size": 54,
        "primary_color": "#FF8C00",
        "secondary_color": "#FF0080",
        "stroke_color": "#200010",
        "stroke_width": 4,
        "bg_box": False,
        "glow": True,
        "glow_color": "#FF8C00",
        "animation": "word_gradient",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "hyper_bounce_yellow": {
        "font": "Impact",
        "font_size": 58,
        "primary_color": "#FFEA00",
        "stroke_color": "#000000",
        "stroke_width": 6,
        "bg_box": True,
        "bg_color": (0, 0, 0, 210),
        "glow": True,
        "glow_color": "#FFEA00",
        "animation": "bounce",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "holo_blue_ultra": {
        "font": "Impact",
        "font_size": 52,
        "primary_color": "#7DF9FF",
        "secondary_color": "#0047AB",
        "stroke_color": "#000814",
        "stroke_width": 4,
        "bg_box": True,
        "bg_color": (0, 29, 61, 200),
        "glow": True,
        "glow_color": "#7DF9FF",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "fire_burn_premium": {
        "font": "Impact",
        "font_size": 56,
        "primary_color": "#FF3131",
        "secondary_color": "#FF914D",
        "stroke_color": "#1A0000",
        "stroke_width": 5,
        "bg_box": False,
        "glow": True,
        "glow_color": "#FF3131",
        "animation": "bounce",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "glow_box_emerald": {
        "font": "Impact",
        "font_size": 50,
        "primary_color": "#50C878",
        "stroke_color": "#002A10",
        "stroke_width": 4,
        "bg_box": True,
        "bg_color": (0, 42, 16, 220),
        "glow": True,
        "glow_color": "#50C878",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "tokyo_night": {
        "font": "Impact",
        "font_size": 54,
        "primary_color": "#9D4EDD",
        "secondary_color": "#00F5D4",
        "stroke_color": "#10002B",
        "stroke_width": 5,
        "bg_box": True,
        "bg_color": (16, 0, 43, 210),
        "glow": True,
        "glow_color": "#00F5D4",
        "animation": "tri_color_sequence",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "golden_emperor": {
        "font": "Impact",
        "font_size": 56,
        "primary_color": "#FFDF00",
        "secondary_color": "#FFFFFF",
        "stroke_color": "#332200",
        "stroke_width": 5,
        "bg_box": True,
        "bg_color": (51, 34, 0, 200),
        "glow": True,
        "glow_color": "#FFDF00",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    },
    "glitch_red_cyan": {
        "font": "Impact",
        "font_size": 54,
        "primary_color": "#FF003C",
        "secondary_color": "#00F0FF",
        "stroke_color": "#000000",
        "stroke_width": 5,
        "bg_box": False,
        "glow": True,
        "glow_color": "#FF003C",
        "animation": "pop",
        "modes_supported": ["line", "phrase", "word_by_word"]
    }
}

def get_style(style_id: str) -> dict:
    """Helper function to fetch style configuration with fallback."""
    return CAPTION_STYLES.get(style_id, CAPTION_STYLES["clean_subtitle"])