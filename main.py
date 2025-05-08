"""
Chess Vision - Main Application Entry Point.

This script launches the Chess Vision application.
"""

import sys
import os
import importlib.util

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Print Python path for debugging
print("Python Path:")
for path in sys.path:
    print(f"  {path}")

# Check if required packages are installed
required_packages = ['cv2', 'ultralytics', 'pyautogui', 'chess']
for package in required_packages:
    spec = importlib.util.find_spec(package)
    if spec is None:
        print(f"Package {package} is not installed or not found in the Python path")
    else:
        print(f"Package {package} is installed at: {spec.origin}")

# Try to import the main function
try:
    from src.gui.app import main

    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"Error importing main function: {e}")
    print("Please make sure all required packages are installed.")
    sys.exit(1)
