import traceback
print("Testing audio_engine.py...")
try:
    import audio_engine
    print("✅ SUCCESS: audio_engine.py is loading perfectly fine!")
except Exception as e:
    print(f"❌ ERROR: audio_engine.py has a bug:")
    traceback.print_exc()