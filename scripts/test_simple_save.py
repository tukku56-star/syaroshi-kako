import os
from datetime import datetime

GOOGLE_DRIVE = r"\\Desktop-jp91uul\開発関連"

def test_save():
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join(GOOGLE_DRIVE, today, "log")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"Created directory: {log_dir}")
    
    test_file = os.path.join(log_dir, "test_save.txt")
    
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(f"Test save at {datetime.now()}\n")
        f.write("This is a test message\n")
    
    print(f"Successfully saved to: {test_file}")
    
    # Verify
    if os.path.exists(test_file):
        with open(test_file, "r", encoding="utf-8") as f:
            print(f"Content: {f.read()}")

if __name__ == "__main__":
    test_save()
