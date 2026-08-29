import os
import shutil

def rollback_and_cleanup():
    # 1. Target backup jo sabse pehle banaya gaya tha (Original File)
    original_backup = "app.py.nav_backup"
    main_file = "app.py"
    
    print("--- RESTORING ORIGINAL UI ---")
    
    if os.path.exists(original_backup):
        # Current kharab file ko hata dena
        if os.path.exists(main_file):
            os.remove(main_file)
        
        # Original backup ko wapis app.py bana dena
        shutil.copy(original_backup, main_file)
        print(f"✅ SUCCESS: {original_backup} se app.py restore ho gayi hai.")
    else:
        # Agar pehla backup na mile, toh kal wala stable backup check karna
        alternative = "app.py.bak_gap_1785954449"
        if os.path.exists(alternative):
            if os.path.exists(main_file): os.remove(main_file)
            shutil.copy(alternative, main_file)
            print(f"✅ SUCCESS: Yesterday's backup ({alternative}) se restore kiya gaya.")
        else:
            print("❌ Error: Koi stable backup nahi mila!")

    # 2. Saare "Patch" files ko delete karna jo humne banaye thay
    patches_to_delete = [
        "APPLY_NAVBAR_PATCH.py", "FINAL_UI_FIX.py", "REPAIR_APP_NOW.py",
        "FIX_NAVBAR_FINAL.py", "CLEAN_NAVBAR_ULTIMATE.py", "RESTORE_AND_NAVBAR.py",
        "TOTAL_REPAIR_NAVBAR.py", "FINAL_STABLE_REPAIR.py", "RESTORE_MY_APP.py",
        "FINAL_UI_FIX.py", "FINAL_STABLE_REPAIR.py"
    ]
    
    print("\\n--- DELETING PATCH FILES ---")
    for patch in patches_to_delete:
        if os.path.exists(patch):
            os.remove(patch)
            print(f"🗑️ Deleted: {patch}")

    print("\\n✅ SAB KUCH SAAF HO GAYA HAI. Ab aapka original UI wapis aa gaya hoga.")

if __name__ == "__main__":
    rollback_and_cleanup()