import os
import datetime

GOOGLE_DRIVE = r"G:\マイドライブ\開発関連"
today = datetime.datetime.now().strftime("%Y-%m-%d")
log_dir = os.path.join(GOOGLE_DRIVE, today, "logs")

print(f"Checking: {log_dir}")

if os.path.exists(log_dir):
    print("Directory exists!")
    files = os.listdir(log_dir)
    print(f"Found {len(files)} files:")
    for f in files:
        print(f" - {f}")
        # Print first few lines of one file
        if f.endswith('.json'):
            try:
                with open(os.path.join(log_dir, f), 'r', encoding='utf-8') as file:
                    print(f"Content of {f} (first 100 chars):")
                    print(file.read(100))
            except Exception as e:
                print(f"Error reading {f}: {e}")
            break
else:
    print("Directory does NOT exist!")
