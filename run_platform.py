#!/usr/bin/env python3
"""
Orchestration & Verification Runner for Polyglot Pharma Supply Chain Platform.
Allows starting or validating services locally (native Python/Node) or via Docker.
"""

import sys
import subprocess
import time
import urllib.request
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def check_backend_health():
    url = "http://localhost:8000/health"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                print(f"[OK] Backend health: {data.get('status')} - {data.get('service')}")
                return True
    except Exception as e:
        print(f"[INFO] Backend not currently reachable at {url}: {e}")
        return False

def check_frontend():
    url = "http://localhost:3000"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            if resp.status == 200:
                print(f"[OK] Frontend reachable at {url}")
                return True
    except Exception as e:
        print(f"[INFO] Frontend not currently reachable at {url}: {e}")
        return False

def run_tests():
    print("[RUNNING] Backend unit tests...")
    python_bin = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
    if not python_bin.exists():
        python_bin = "python"
    
    cmd = [str(python_bin), "-m", "pytest", "tests/unit/test_backend_api.py", "-v"]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return res.returncode == 0

def test_frontend_build():
    print("[BUILDING] React production bundle in frontend/...")
    cmd = ["npm", "run", "build"]
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT / "frontend"), shell=True)
    return res.returncode == 0

if __name__ == "__main__":
    print("=" * 60)
    print(" Polyglot Pharma Supply Chain Orchestration Check")
    print("=" * 60)
    
    frontend_ok = test_frontend_build()
    tests_ok = run_tests()
    backend_live = check_backend_health()
    frontend_live = check_frontend()

    print("\nSummary:")
    print(f"  Frontend Build:  {'PASS' if frontend_ok else 'FAIL'}")
    print(f"  Unit Tests:      {'PASS' if tests_ok else 'FAIL'}")
    print(f"  Backend Live:    {'YES' if backend_live else 'NO (Start via uvicorn backend.main:app)'}")
    print(f"  Frontend Live:   {'YES' if frontend_live else 'NO (Start via npm run dev in frontend)'}")
    print("=" * 60)
