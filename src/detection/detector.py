"""
Chess Piece Detector Module.

This module provides functionality for detecting chess pieces using a YOLO model.
"""

import os
import numpy as np
import pyautogui

try:
    import cv2
except ImportError:
    print("OpenCV (cv2) not found. Please install it with: pip install opencv-python")
    raise

try:
    from ultralytics import YOLO
except ImportError:
    print("Ultralytics not found. Please install it with: pip install ultralytics")
    raise


class ChessPieceDetector:
    """
    A class for detecting chess pieces using a YOLO model.

    This class handles loading the YOLO model, capturing the screen,
    and detecting chess pieces in the captured image.
    """

    def __init__(self, model_path=None, conf_threshold=0.5):
        """
        Initialize the chess piece detector.

        Args:
            model_path: Path to the YOLO model file
            conf_threshold: Confidence threshold for detections
        """
        # Set default model path if not provided
        if model_path is None:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "models",
                "my_model.pt"
            )

        # Check if model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Load the model
        self.model = YOLO(model_path, task='detect')
        self.labels = self.model.names

        # Set confidence threshold
        self.conf_threshold = conf_threshold

        # Set up colors for visualization
        self.colors = [
            (164, 120, 87), (68, 148, 228), (93, 97, 209), (178, 182, 133),
            (88, 159, 106), (96, 202, 231), (159, 124, 168), (169, 162, 241),
            (98, 118, 150), (172, 176, 184)
        ]

        # Initialize screen region
        self.screen_region = None

    def set_screen_region(self, region):
        """
        Set the screen region to capture.

        Args:
            region: A tuple (x, y, width, height) representing the screen region
        """
        self.screen_region = region

    def capture_screen(self):
        """
        Capture the screen region.

        Returns:
            The captured image as a numpy array, or None if no region is set
        """
        if self.screen_region is None:
            return None

        x, y, width, height = self.screen_region

        # Capture the screen region using PyAutoGUI
        screenshot = pyautogui.screenshot(region=(x, y, width, height))

        # Convert PIL image to numpy array
        img = np.array(screenshot)

        # Convert RGB to BGR (OpenCV uses BGR)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        return img

    def detect(self, img=None):
        """
        Detect chess pieces in an image.

        Args:
            img: The image to detect pieces in, or None to capture the screen

        Returns:
            A tuple (img, detections) where img is the image with detections drawn
            and detections is a list of detected pieces
        """
        if img is None:
            img = self.capture_screen()

        if img is None:
            return None, []

        # Run inference on the image
        results = self.model.track(img, verbose=False)

        # Extract results
        detections = results[0].boxes

        # Create a copy of the image for drawing
        img_with_detections = img.copy()

        # List to hold detected pieces
        detected_pieces = []

        # Process each detection
        for i in range(len(detections)):
            # Get bounding box coordinates
            xyxy_tensor = detections[i].xyxy.cpu()
            xyxy = xyxy_tensor.numpy().squeeze()
            xmin, ymin, xmax, ymax = xyxy.astype(int)

            # Get class ID and name
            classidx = int(detections[i].cls.item())
            classname = self.labels[classidx]

            # Get confidence
            conf = detections[i].conf.item()

            # Process detection if confidence is high enough
            if conf > self.conf_threshold:
                # Calculate center of the bounding box
                center_x = (xmin + xmax) // 2
                center_y = (ymin + ymax) // 2

                # Add to detected pieces
                detected_pieces.append({
                    "class": classname,
                    "confidence": conf,
                    "bbox": (xmin, ymin, xmax, ymax),
                    "center": (center_x, center_y)
                })

                # Draw bounding box
                color = self.colors[classidx % len(self.colors)]
                cv2.rectangle(img_with_detections, (xmin, ymin), (xmax, ymax), color, 2)

                # Draw label
                label = f'{classname}: {int(conf*100)}%'
                label_size, base_line = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                label_ymin = max(ymin, label_size[1] + 10)
                cv2.rectangle(
                    img_with_detections,
                    (xmin, label_ymin - label_size[1] - 10),
                    (xmin + label_size[0], label_ymin + base_line - 10),
                    color,
                    cv2.FILLED
                )
                cv2.putText(
                    img_with_detections,
                    label,
                    (xmin, label_ymin - 7),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1
                )

        return img_with_detections, detected_pieces
