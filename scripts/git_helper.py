#!/usr/bin/env python
import subprocess
import sys

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    # Stage all changes
    run("git add -A")
    # Show staged files
    changed = run("git diff --cached --name-only").splitlines()
    if not changed:
        print("No changes to commit.")
        return
    print("Staged files:\n" + "\n".join(changed))
    # Use Commitizen for conventional commit message (requires commitizen installed)
    print("Launching Commitizen (cz)...")
    run("git cz")
    # Push to remote
    run("git push")
    print("✅ Push completed.")

if __name__ == "__main__":
    main()
