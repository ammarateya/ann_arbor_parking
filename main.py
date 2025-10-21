#!/usr/bin/env python3
"""
Parking Citation Scraper - Main Entry Point

This is the main entry point for the parking citation scraper.
The actual application logic is in the src/ directory.
"""

import sys
import os
import traceback

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 50)
print("MAIN.PY STARTING")
print("=" * 50)
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")

try:
    print("Attempting to import main_combined...")
    import main_combined
    print("✓ main_combined imported successfully")
    
    print("Starting main application...")
    main_combined.main()
    
except Exception as e:
    print(f"✗ Failed to run application: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)
