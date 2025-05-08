"""
Detection Module.

This module provides functionality for detecting chess pieces using a YOLO model.
"""

from src.detection.detector import ChessPieceDetector
from src.detection.fen_generator import FENGenerator

__all__ = ['ChessPieceDetector', 'FENGenerator']
