import os
import json
import sys
import importlib.util
from pathlib import Path

def check_file_exists(path, description):
    if os.path.exists(path):
        print(f"✅ {description} found: {path}")
        return True
    else:
        print(f"❌ {description} NOT found: {path}")
        return False

def check_python_package(package_name):
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"✅ Python package '{package_name}' is installed.")
        return True
    else:
        print(f"❌ Python package '{package_name}' is NOT installed.")
        return False

def main():
    print("=== Antigravity System Health Check ===")
    
    # 1. Check Extensions Registry
    ext_path = r"C:\Users\admin\.gemini\antigravity\extensions\extensions.json"
    if check_file_exists(ext_path, "Extensions Registry"):
        try:
            with open(ext_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"   Found {len(data)} plugins registered.")
                for plugin in data:
                    entry = plugin.get('entry_point')
                    if entry:
                        check_file_exists(entry, f"Plugin '{plugin.get('name')}' entry point")
                    else:
                        print(f"   ⚠️ Plugin '{plugin.get('name')}' has no entry point.")
        except Exception as e:
            print(f"   ❌ Error reading extensions.json: {e}")

    # 2. Check Dependencies
    print("\n--- Checking Dependencies ---")
    check_python_package("flask")
    check_python_package("flask_socketio")

    # 3. Check Playground
    print("\n--- Checking Playground ---")
    playground_path = r"C:\Users\admin\.gemini\antigravity\playground"
    if os.path.exists(playground_path):
        for item in os.listdir(playground_path):
            item_path = os.path.join(playground_path, item)
            if os.path.isdir(item_path):
                if not os.listdir(item_path):
                    print(f"⚠️ Empty project found: {item}")
                else:
                    print(f"✅ Project '{item}' seems active.")
    else:
        print(f"❌ Playground directory not found: {playground_path}")

    print("\n=== Health Check Complete ===")

if __name__ == "__main__":
    main()
