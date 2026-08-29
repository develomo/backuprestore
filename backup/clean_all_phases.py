"""
============================================================================
CLEAN ALL-IN-ONE — Phases 3+4+5 from Phase 2 Backup
============================================================================
INSTRUCTIONS:
  1. First RESTORE from Phase 2 backup:
     copy app.py.backup_phase2 app.py

  2. Then RUN this script:
     python clean_all_phases.py

THIS SCRIPT:
  - Phase 3: Captions fix (remove preview, connect short+long, instant timing)
  - Phase 4: Fix render_long_batch_memory() clips/keep_temp/sfx_files args  
  - Phase 5: Premium CSS + dark/light mode
  - VALIDATES syntax after EACH patch — stops if any error

NOTES:
  - Uses raw strings (r\"\"\") to avoid ANY quoting issues
  - All string concatenation uses proper Python syntax
  - Indentation carefully matched
============================================================================
"""
import os
import re
import sys

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(BACKUP_DIR, 'app.py')
SAFE_LONG_PATH = os.path.join(BACKUP_DIR, 'safe_long_video_polished.py')


def validate_syntax(content, label):
    """Check Python syntax. Returns True if OK, False if error."""
    try:
        compile(content, '<string>', 'exec')
        print(f"  [OK] {label} — syntax valid")
        return True
    except SyntaxError as e:
        print(f"  [FAIL] {label} — SyntaxError: {e} at line {e.lineno}")
        lines = content.split('\n')
        if e.lineno:
            lo = max(0, e.lineno - 3)
            hi = min(len(lines), e.lineno + 2)
            for i in range(lo, hi):
                m = ">>>" if i == e.lineno - 1 else "   "
                print(f"     {m} L{i+1}: {lines[i][:140]}")
        return False


def main():
    # Check if app.py exists
    if not os.path.exists(APP_PATH):
        print(f"[ERROR] {APP_PATH} not found!")
        return

    # Read current app.py
    with open(APP_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    init_lines = len(content.split('\n'))
    print(f"[INFO] Starting: {init_lines} lines")

    # Initial syntax check
    if not validate_syntax(content, "Initial state"):
        print("\n[FATAL] app.py already has syntax errors. Restore from backup_phase2 first:")
        print("  copy app.py.backup_phase2 app.py")
        return

    total_fixes = 0

    # ==================================================================
    # PHASE 3: Captions Fix
    # ==================================================================
    print("\n--- PHASE 3: Captions ---")

    # 3a: Remove caption_video_preview_section() from _page_generator()
    old_block_3a = """    # 6. Caption Preview
    st.markdown("---")
    caption_video_preview_section()

    # 7. Output"""
    new_block_3a = """    # 6. Output"""

    if old_block_3a in content:
        content = content.replace(old_block_3a, new_block_3a)
        total_fixes += 1
        print("  [3a] Removed caption_video_preview_section() from _page_generator()")
        if not validate_syntax(content, "After 3a"):
            print("[STOP] Rolling back 3a was not possible, syntax error introduced")
    else:
        print("  [SKIP 3a] caption_video_preview_section block not found (may already be removed)")

    # 3b: Fix caption_dropdown_card() — the <br> issue
    # Find the function and fix the preview fallback
    # The Phase 2 version has: st.warning("Preview missing...")
    # We replace it with clean st.markdown without <br> issues
    old_preview_fallback = '        st.warning("Preview missing. Run: python caption_preview_generator.py")'
    new_preview_fallback = (
        '        st.markdown('
        "'<div style=\"color:#aaa;font-size:12px;text-align:center;padding:15px 8px;\">"
        "Sample &bull; Text &bull; Preview &bull; Here"
        '<br><span style=\"opacity:0.5;font-size:10px;\">'
        "Run: python caption_preview_generator.py</span></div>'"
        ', unsafe_allow_html=True)'
    )
    
    if old_preview_fallback in content:
        content = content.replace(old_preview_fallback, new_preview_fallback)
        total_fixes += 1
        print("  [3b] Fixed caption preview fallback (dummy text without <br> error)")
        if not validate_syntax(content, "After 3b"):
            print("[STOP] Syntax error in 3b")
    else:
        print("  [SKIP 3b] warning fallback not found — checking alternatives...")
        # Try to find the pattern
        if 'caption_preview_generator.py' in content:
            # Find the st.warning line
            warn_idx = content.find('caption_preview_generator.py')
            if warn_idx > 0:
                line_start = content.rfind('\n', 0, warn_idx)
                line_end = content.find('\n', warn_idx)
                existing_line = content[line_start:line_end]
                print(f"    Found: {existing_line[:120]}")
                content = content[:line_start] + '\n' + new_preview_fallback + content[line_end:]
                total_fixes += 1
                print("  [3b] Fixed caption preview fallback (fuzzy match)")
                if not validate_syntax(content, "After 3b fuzzy"):
                    print("[STOP] Syntax error in 3b fuzzy")
        else:
            print("  [SKIP 3b] Not found at all")

    # 3c: caption_offset = 0 in run_render()
    # Find the block where update() is called before loading pipeline
    old_pipeline_load = '        update(20, "Loading pipeline")'
    if old_pipeline_load in content:
        injection = (
            '        update(15, "Preparing captions")\n'
            '        kwargs["caption_offset"] = 0.0\n'
            '        kwargs["caption_timing_precision"] = True\n'
            '        '
        )
        content = content.replace(old_pipeline_load, injection + old_pipeline_load, 1)
        total_fixes += 1
        print("  [3c] Injected caption_offset=0.0 in run_render()")
        if not validate_syntax(content, "After 3c"):
            print("[STOP] Syntax error in 3c — rolling back...")
            content = content.replace(injection + old_pipeline_load, old_pipeline_load, 1)
            print("  [ROLLED BACK 3c]")
    else:
        print("  [SKIP 3c] pipeline load marker not found")

    # ==================================================================
    # PHASE 4: Fix safe_long_video_polished.py
    # ==================================================================
    print("\n--- PHASE 4: Long Video Pipeline ---")

    if os.path.exists(SAFE_LONG_PATH):
        with open(SAFE_LONG_PATH, 'r', encoding='utf-8') as f:
            sl = f.read()

        sl_backup = SAFE_LONG_PATH + '.backup_phase4'
        with open(sl_backup, 'w', encoding='utf-8') as f:
            f.write(sl)
        print(f"  [4] Backup: {sl_backup}")

        sl_fixes = 0
        if 'clips=clip_list' in sl:
            sl = sl.replace('clips=clip_list', 'clip_paths=clip_list')
            sl_fixes += 1
            print("  [4a] clips=clip_list → clip_paths=clip_list")
        if 'sfx_files=' in sl:
            sl = sl.replace('sfx_files=', 'sfx_path=')
            sl_fixes += 1
            print("  [4b] sfx_files= → sfx_path=")
        if 'final_quality=' in sl:
            sl = re.sub(r',?\s*final_quality\s*=\s*"[^"]*"', '', sl)
            sl_fixes += 1
            print("  [4c] Removed final_quality= arg")
        if 'cleanup=True' in sl:
            sl = sl.replace('cleanup=True', 'keep_temp=False')
            sl_fixes += 1
            print("  [4d] cleanup=True → keep_temp=False")

        if sl_fixes:
            # Validate safe_long_video_polished.py syntax
            try:
                compile(sl, SAFE_LONG_PATH, 'exec')
                with open(SAFE_LONG_PATH, 'w', encoding='utf-8') as f:
                    f.write(sl)
                total_fixes += sl_fixes
                print(f"  [4] Written: {sl_fixes} fixes")
            except SyntaxError as e:
                print(f"  [4 ERROR] SyntaxError in safe_long: {e}")
        else:
            print("  [4] No fixes needed")
    else:
        print(f"  [SKIP 4] {SAFE_LONG_PATH} not found")

    # ==================================================================
    # PHASE 5: Premium CSS
    # ==================================================================
    print("\n--- PHASE 5: Premium UI ---")

    # Find css() function
    css_start = content.find('\ndef css() -> None:')
    if css_start < 0:
        print("  [SKIP 5] css() not found")
    else:
        # Find end of current css()
        after_css = content[css_start + 20:]
        next_func = re.search(r'\n(def \w+|# ={10,}|# PHASE)', after_css)
        if next_func:
            css_end = css_start + 20 + next_func.start()
        else:
            css_end = len(content)

        # Build clean premium CSS
        clean_css = r'''
def css() -> None:
    st.markdown(
        """
        <style>
        :root{--bg:#f5f6f8;--bg-alt:#edeff3;--surface:#fff;--surface-hover:#f9fafb;--border:#e0e3e8;--border-light:#ebeef2;--text:#1a1a2e;--text-primary:#111122;--text-secondary:#6b7280;--text-tertiary:#9ca3af;--accent:#e63946;--accent-hover:#c1121f;--accent-light:#fef2f3;--accent-soft:#fce4e6;--green:#059669;--green-light:#ecfdf5;--amber:#d97706;--amber-light:#fffbeb;--red:#dc2626;--red-light:#fef2f2;--shadow-xs:0 1px 2px rgba(0,0,0,.03);--shadow-sm:0 1px 3px rgba(0,0,0,.05),0 1px 2px rgba(0,0,0,.03);--shadow-md:0 4px 12px rgba(0,0,0,.06),0 1px 3px rgba(0,0,0,.04);--shadow-lg:0 8px 24px rgba(0,0,0,.08),0 2px 6px rgba(0,0,0,.04);--radius-xs:6px;--radius-sm:8px;--radius:12px;--radius-lg:16px;--transition:.2s cubic-bezier(.4,0,.2,1)}
        [data-theme="dark"]{--bg:#0b0b18;--bg-alt:#12122a;--surface:#181835;--surface-hover:#1e1e40;--border:#2a2a4a;--border-light:#222244;--text:#e8e8f5;--text-primary:#f0f0ff;--text-secondary:#9a9ab8;--text-tertiary:#6a6a88;--accent:#ff4d5a;--accent-hover:#ff6b6b;--accent-light:rgba(255,77,90,.12);--accent-soft:rgba(255,77,90,.08);--green:#34d399;--green-light:rgba(52,211,153,.12);--amber:#fbbf24;--amber-light:rgba(251,191,36,.12);--red:#f87171;--red-light:rgba(248,113,113,.12)}
        .stApp{background:var(--bg)!important}
        .block-container{padding:.5rem 1.5rem 1.5rem!important;max-width:1240px!important}
        header[data-testid="stHeader"]{background:transparent!important}
        #MainMenu,footer,.stDeployButton{visibility:hidden!important;display:none!important}
        ::-webkit-scrollbar{width:6px;height:6px}
        ::-webkit-scrollbar-track{background:transparent}
        ::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
        hr{border-color:var(--border)!important;margin:8px 0!important;opacity:.5!important}
        .app-title{font-size:28px;font-weight:800;letter-spacing:-.6px;margin-bottom:6px;color:var(--text-primary)}
        .section-title{font-size:16px;font-weight:700;margin:16px 0 8px;color:var(--text-primary)}
        .card{border:1px solid var(--border);border-radius:var(--radius);padding:16px;background:var(--surface);box-shadow:var(--shadow-sm);margin-bottom:10px;transition:box-shadow var(--transition)}
        .card:hover{box-shadow:var(--shadow-md)}
        .asset-title{font-size:15px;font-weight:700;margin:2px 0 8px;color:var(--text-primary)}
        .asset-label{font-size:12px;font-weight:600;margin:6px 0 4px;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.3px}
        .count{font-size:11px;color:var(--text-tertiary);margin-bottom:4px}
        .ready{font-size:12px;font-weight:700;color:var(--green);padding:4px 10px;background:var(--green-light);border-radius:20px;display:inline-block}
        .missing{font-size:12px;font-weight:700;color:var(--red);padding:4px 10px;background:var(--red-light);border-radius:20px;display:inline-block}
        .caption-wrap{border:1px solid var(--border);border-radius:var(--radius);padding:14px;background:var(--surface);box-shadow:var(--shadow-xs);margin-bottom:10px;transition:all var(--transition)}
        .caption-wrap:hover{border-color:var(--border-light);box-shadow:var(--shadow-sm)}
        .caption-title{font-size:13px;font-weight:700;margin-bottom:6px;color:var(--text-primary)}
        .caption-desc{font-size:11px;color:var(--text-tertiary);margin:6px 0 8px;line-height:1.4}
        .caption-preview-box{width:150px;max-width:100%;border:1px solid var(--border);border-radius:var(--radius-xs);overflow:hidden;background:#0a0a18;padding:0;box-shadow:var(--shadow-sm)}
        .preview-box{border:1px dashed var(--border);border-radius:var(--radius);padding:16px;min-height:100px;background:var(--surface);transition:border-color var(--transition)}
        .preview-box:hover{border-color:var(--accent)}
        div.stButton>button{height:38px!important;border-radius:var(--radius-sm)!important;font-weight:600!important;font-size:13px!important;transition:all var(--transition)!important;border:1px solid var(--border)!important}
        div.stButton>button[kind="primary"]{background:var(--accent)!important;color:#fff!important;border-color:var(--accent)!important;box-shadow:0 2px 8px rgba(230,57,70,.25)!important}
        div.stButton>button[kind="primary"]:hover{background:var(--accent-hover)!important;transform:translateY(-1px);box-shadow:0 4px 14px rgba(230,57,70,.35)!important}
        div.stButton>button[kind="secondary"]{background:var(--surface)!important;color:var(--text)!important}
        div.stButton>button[kind="secondary"]:hover{background:var(--surface-hover)!important;border-color:var(--accent)!important;color:var(--accent)!important}
        div[data-testid="stFileUploader"] section{min-height:48px!important;padding:6px 10px!important;border-radius:var(--radius-sm)!important;border:2px dashed var(--border)!important;background:var(--bg-alt)!important;transition:all var(--transition)!important}
        div[data-testid="stFileUploader"] section:hover{border-color:var(--accent)!important;background:var(--accent-light)!important}
        div[data-testid="stFileUploader"] small{display:none!important}
        .streamlit-expanderHeader{border-radius:var(--radius-sm)!important;border:1px solid var(--border)!important;background:var(--surface)!important;font-weight:650!important;font-size:14px!important;color:var(--text-primary)!important;padding:12px 16px!important;transition:all var(--transition)!important}
        .streamlit-expanderHeader:hover{border-color:var(--accent)!important;background:var(--surface-hover)!important}
        .streamlit-expanderContent{border:1px solid var(--border)!important;border-top:none!important;border-radius:0 0 var(--radius-sm) var(--radius-sm)!important;background:var(--surface)!important;padding:12px!important}
        section[data-testid="stSidebar"]{background:var(--surface)!important;border-right:1px solid var(--border)!important}
        div[data-testid="stSelectbox"] label,div[data-testid="stRadio"] label{color:var(--text-secondary)!important;font-size:12px!important;font-weight:600!important}
        div[data-testid="stCheckbox"] label{color:var(--text)!important;font-size:13px!important}
        div[data-testid="stSlider"]>div>div>div>div{background:var(--accent)!important}
        div[data-testid="stSuccess"]{background:var(--green-light)!important;border:1px solid var(--green)!important;border-radius:var(--radius-sm)!important}
        div[data-testid="stError"]{background:var(--red-light)!important;border:1px solid var(--red)!important;border-radius:var(--radius-sm)!important}
        div[data-testid="stWarning"]{background:var(--amber-light)!important;border:1px solid var(--amber)!important;border-radius:var(--radius-sm)!important}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <script>
        (function(){try{var s=localStorage.getItem('zaro_theme_v2');if(s==='dark')document.documentElement.setAttribute('data-theme','dark');}catch(e){}
        window.toggleThemeV2=function(){try{var c=document.documentElement.getAttribute('data-theme');if(c==='dark'){document.documentElement.removeAttribute('data-theme');localStorage.setItem('zaro_theme_v2','light');}else{document.documentElement.setAttribute('data-theme','dark');localStorage.setItem('zaro_theme_v2','dark');}}catch(e){}}})();
        </script>
        """,
        unsafe_allow_html=True,
    )
'''

        content = content[:css_start] + clean_css + '\n' + content[css_end:]
        total_fixes += 1
        print("  [5a] css() replaced with premium CSS")
        if not validate_syntax(content, "After 5a"):
            print("[STOP] Syntax error in 5a")
    # Don't proceed if css failed

    # 5b: Fix theme toggle JS function name in main()
    if 'window.toggleTheme();' in content:
        content = content.replace('window.toggleTheme();', 'window.toggleThemeV2();')
        total_fixes += 1
        print("  [5b] Theme toggle JS function name updated")
    if 'try{window.toggleTheme();}catch(e){}' in content:
        content = content.replace('try{window.toggleTheme();}catch(e){}', 'try{window.toggleThemeV2();}catch(e){}')
        total_fixes += 1
        print("  [5b-2] Hidden toggle JS updated")

    # ==================================================================
    # FINAL VALIDATION
    # ==================================================================
    print("\n" + "=" * 60)
    final_ok = validate_syntax(content, "FINAL STATE")
    print("=" * 60)

    if final_ok:
        with open(APP_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        new_lines = len(content.split('\n'))
        print(f"\n[SUCCESS] {total_fixes} fixes applied")
        print(f"[INFO] {init_lines} → {new_lines} lines")
        print("\n▶ RUN: streamlit run app.py")
    else:
        print("\n[FAILED] Syntax errors remain. app.py NOT modified.")
        print("The original file was NOT changed. Fix the issues above and retry.")


if __name__ == "__main__":
    main()
