import shutil
import subprocess
import sys
from pathlib import Path

def start_tools():
    script_path = Path(__file__).resolve().parent / "smuggle.py"
    args = sys.argv[1:]
    command = [sys.executable, str(script_path)] + args
    subprocess.run(command)
