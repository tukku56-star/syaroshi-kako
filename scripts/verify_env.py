import sys
import subprocess

print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

try:
    import pip
    print(f"Pip Version: {pip.__version__}")
except ImportError:
    print("Pip not found!")

print("Hello from Portable Python!")
