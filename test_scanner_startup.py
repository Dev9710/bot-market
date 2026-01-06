"""
Test script to verify the GeckoTerminal Scanner can start properly
"""

import sys
import time
from datetime import datetime

def log(msg):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

log("=" * 80)
log("TEST: GeckoTerminal Scanner Startup")
log("=" * 80)
log("")

# Test 1: Import the module
log("Test 1: Importing geckoterminal_scanner_v3_main...")
try:
    import geckoterminal_scanner_v3_main as scanner
    log("[OK] Import successful")
except Exception as e:
    log(f"[FAIL] Import failed: {e}")
    sys.exit(1)

# Test 2: Check main() function exists
log("")
log("Test 2: Checking main() function exists...")
if hasattr(scanner, 'main'):
    log("[OK] main() function found")
else:
    log("[FAIL] main() function not found")
    sys.exit(1)

# Test 3: Try to start the scanner (will run for 10 seconds then stop)
log("")
log("Test 3: Starting scanner for 10 seconds...")
log("This will run one scan cycle to verify it works...")
log("")

import threading

def run_scanner_test():
    try:
        scanner.main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log(f"[FAIL] Scanner crashed: {e}")
        import traceback
        traceback.print_exc()

# Start scanner in thread
scanner_thread = threading.Thread(target=run_scanner_test, daemon=True)
scanner_thread.start()

# Wait 10 seconds
time.sleep(10)

if scanner_thread.is_alive():
    log("")
    log("[OK] Scanner is running without crashing!")
    log("Stopping test...")
    log("")
    log("=" * 80)
    log("ALL TESTS PASSED")
    log("=" * 80)
    log("")
    log("Summary:")
    log("  [OK] Module imports correctly")
    log("  [OK] main() function exists")
    log("  [OK] Scanner starts without crashing")
    log("")
    log("You can now run: python alerte.py")
    log("")
else:
    log("")
    log("[FAIL] Scanner thread died - check error messages above")
    sys.exit(1)
