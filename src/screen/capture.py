"""
Screen Capture Module.

This module provides functionality for capturing regions of the screen.
"""

import numpy as np
import cv2
import pyautogui


class ScreenCapture:
    """
    A class for capturing regions of the screen.

    This class handles capturing screenshots of specified regions of the screen.
    """

    def __init__(self):
        """Initialize the screen capture."""
        pass

    def capture(self, region):
        """
        Capture a region of the screen.

        Args:
            region: A tuple (x, y, width, height) representing the region to capture

        Returns:
            The captured image as a numpy array, or None if the region is invalid
        """
        if region is None:
            return None

        x, y, width, height = region

        # Capture the screen region using PyAutoGUI
        screenshot = pyautogui.screenshot(region=(x, y, width, height))

        # Convert PIL image to numpy array
        img = np.array(screenshot)

        # Convert RGB to BGR (OpenCV uses BGR)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        return img
