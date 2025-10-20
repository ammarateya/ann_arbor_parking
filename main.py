#!/usr/bin/env python3
"""
Parking Citation Scraper - Main Entry Point

This is the main entry point for the parking citation scraper.
The actual application logic is in the src/ directory.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main application
from main_combined import *

if __name__ == "__main__":
    # The main_combined module will handle everything
    pass
