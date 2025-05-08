"""
Chess Vision - Main Application Entry Point.

This script launches the Chess Vision application.
"""

import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.app import main

if __name__ == "__main__":
    main()
