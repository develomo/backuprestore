# Premium 13 Caption Styles Engine
CAPTION_STYLES = {
    "1_neon_glow": {"fontsize": 48, "color": "#00FFCC", "bg_color": None, "stroke_color": "#FF007F", "stroke_width": 3, "font": "Arial-Bold"},
    "2_cyberpunk_yellow": {"fontsize": 50, "color": "#FFE600", "bg_color": "#000000", "stroke_color": "#00FFFF", "stroke_width": 2, "font": "Arial-Bold"},
    "3_word_highlight_red": {"fontsize": 46, "color": "#FF2A2A", "bg_color": "#FFFFFF", "stroke_color": "#000000", "stroke_width": 2, "font": "Impact"},
    "4_tiktok_viral_green": {"fontsize": 52, "color": "#00FF66", "bg_color": None, "stroke_color": "#000000", "stroke_width": 4, "font": "Arial-Bold"},
    "5_dark_box_gold": {"fontsize": 45, "color": "#FFD700", "bg_color": "#111111", "stroke_color": None, "stroke_width": 0, "font": "Arial-Bold"},
    "6_multi_color_pop": {"fontsize": 48, "color": "#FF00AA", "bg_color": "#00FFCC", "stroke_color": "#000000", "stroke_width": 2, "font": "Impact"},
    "7_soft_pastel_purple": {"fontsize": 44, "color": "#E0BBE4", "bg_color": "#3D1E6D", "stroke_color": None, "stroke_width": 0, "font": "Arial"},
    "8_bold_white_black_border": {"fontsize": 54, "color": "#FFFFFF", "bg_color": None, "stroke_color": "#000000", "stroke_width": 5, "font": "Impact"},
    "9_retro_vhs_cyan": {"fontsize": 46, "color": "#00FFFF", "bg_color": "#FF0055", "stroke_color": "#000000", "stroke_width": 2, "font": "Courier-Bold"},
    "10_karaoke_glow_orange": {"fontsize": 50, "color": "#FF6600", "bg_color": None, "stroke_color": "#FFFF00", "stroke_width": 3, "font": "Arial-Bold"},
    "11_gradient_blue": {"fontsize": 48, "color": "#0099FF", "bg_color": "#001133", "stroke_color": "#FFFFFF", "stroke_width": 1, "font": "Arial-Bold"},
    "12_minimal_clean_box": {"fontsize": 42, "color": "#FFFFFF", "bg_color": "rgba(0,0,0,0.7)", "stroke_color": None, "stroke_width": 0, "font": "Arial"},
    "13_fire_red_yellow": {"fontsize": 52, "color": "#FF0000", "bg_color": None, "stroke_color": "#FFCC00", "stroke_width": 4, "font": "Impact"}
}

def get_caption_style(style_name):
    return CAPTION_STYLES.get(style_name, CAPTION_STYLES["1_neon_glow"])
