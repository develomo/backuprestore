# fix_kwargs_order.py
import re
from pathlib import Path

slp = Path("safe_long_video_polished.py")
content = slp.read_text(encoding="utf-8")

# Find the function signature and fix parameter order
sig_pattern = r'(def run_integrated_long_pipeline\()([^)]+)(\):)'
match = re.search(sig_pattern, content, re.DOTALL)

if match:
    params_str = match.group(2)
    
    # Split all parameters
    params = [p.strip() for p in params_str.split(',')]
    
    # Separate **kwargs from regular params
    kwargs_param = None
    regular_params = []
    for p in params:
        if p.startswith('**'):
            kwargs_param = p
        else:
            regular_params.append(p)
    
    # Rebuild: regular params first, then **kwargs last
    if kwargs_param:
        new_params = regular_params + [kwargs_param]
    else:
        new_params = regular_params
    
    new_sig = match.group(1) + ", ".join(new_params) + match.group(3)
    content = content.replace(match.group(0), new_sig)
    slp.write_text(content, encoding="utf-8")
    
    print(f"✅ FIXED: Moved **kwargs to end of signature")
    print(f"   Params order: {len(regular_params)} regular + {kwargs_param}")
else:
    print("⚠️ Could not find function signature")

# Verify
try:
    compile(slp.read_text(encoding="utf-8"), str(slp), "exec")
    print("✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"❌ Still has error at line {e.lineno}: {e.msg}")