"""
Screen Selector Module.

This module provides functionality for selecting a region of the screen.
"""

import os
import sys
import json
from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QGuiApplication
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QDialog, QDesktopWidget
)


class ScreenSelector(QDialog):
    """
    A dialog for selecting a region of the screen.

    This dialog allows the user to select a fixed-size region (380x380 pixels)
    of the screen for chess board detection.
    """

    def __init__(self, parent=None, selection_size=(380, 380)):
        """
        Initialize the screen selector.

        Args:
            parent: Parent widget
            selection_size: Size of the selection box (width, height)
        """
        # Create the dialog without a parent to ensure it's a top-level window
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Set up the dialog
        self.setWindowTitle("Select Chess Board")

        # Get the screen geometry
        screen = QGuiApplication.primaryScreen()
        self.screen_geometry = screen.geometry()

        # Take a screenshot of the entire screen
        self.screenshot = screen.grabWindow(0)

        # Set the dialog size to match the screen
        self.setGeometry(self.screen_geometry)

        # Set up the selection box
        self.selection_size = selection_size
        self.selection_rect = QRect(
            (self.screen_geometry.width() - selection_size[0]) // 2,
            (self.screen_geometry.height() - selection_size[1]) // 2,
            selection_size[0],
            selection_size[1]
        )

        # Set up dragging variables
        self.dragging = False
        self.drag_start = QPoint()
        self.drag_offset = QPoint()

        # Set up the UI
        self._setup_ui()

        # Make sure the dialog is shown as a full-screen window
        self.showFullScreen()

    def _setup_ui(self):
        """Set up the user interface."""
        # Create a layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a widget to fill the space
        self.content_widget = QWidget(self)
        layout.addWidget(self.content_widget)

        # Create a layout for the content
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Add instructions
        instructions = QLabel(
            "Position the square over the chess board and click 'Select'.\n"
            "Press ESC to cancel."
        )
        instructions.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); padding: 5px;")
        instructions.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(instructions)

        # Add spacer
        content_layout.addStretch(1)

        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)

        # Select button
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.accept)
        self.select_button.setStyleSheet("background-color: rgba(0, 128, 0, 200); color: white;")

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("background-color: rgba(128, 0, 0, 200); color: white;")

        # Add buttons to layout
        button_layout.addStretch(1)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch(1)

        # Add button layout to content layout
        content_layout.addLayout(button_layout)

    def paintEvent(self, event):
        """Paint the dialog."""
        painter = QPainter(self)

        # Draw the screenshot
        painter.drawPixmap(0, 0, self.screenshot)

        # Draw a semi-transparent overlay
        overlay_color = QColor(0, 0, 0, 128)
        painter.setBrush(overlay_color)
        painter.setPen(Qt.NoPen)

        # Draw the overlay in four parts (around the selection rectangle)
        # Top
        painter.drawRect(0, 0, self.width(), self.selection_rect.top())
        # Left
        painter.drawRect(0, self.selection_rect.top(), self.selection_rect.left(), self.selection_rect.height())
        # Right
        painter.drawRect(self.selection_rect.right(), self.selection_rect.top(),
                        self.width() - self.selection_rect.right(), self.selection_rect.height())
        # Bottom
        painter.drawRect(0, self.selection_rect.bottom(), self.width(), self.height() - self.selection_rect.bottom())

        # Draw the selection rectangle
        pen = QPen(Qt.red, 2, Qt.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.selection_rect)

        # Draw the size label
        size_text = f"{self.selection_rect.width()}x{self.selection_rect.height()}"
        painter.setPen(Qt.white)
        painter.drawText(
            self.selection_rect.left(),
            self.selection_rect.top() - 5,
            size_text
        )

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Check if the click is inside the selection rectangle
            if self.selection_rect.contains(event.pos()):
                self.dragging = True
                self.drag_start = event.pos()
                self.drag_offset = event.pos() - self.selection_rect.topLeft()
                self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.dragging:
            # Calculate the new position
            new_pos = event.pos() - self.drag_offset

            # Ensure the selection stays within the screen
            if new_pos.x() < 0:
                new_pos.setX(0)
            if new_pos.y() < 0:
                new_pos.setY(0)
            if new_pos.x() + self.selection_rect.width() > self.width():
                new_pos.setX(self.width() - self.selection_rect.width())
            if new_pos.y() + self.selection_rect.height() > self.height():
                new_pos.setY(self.height() - self.selection_rect.height())

            # Update the selection rectangle
            self.selection_rect.moveTopLeft(new_pos)
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.reject()

    def get_selection(self):
        """
        Get the selected region.

        Returns:
            A tuple (x, y, width, height) representing the selected region
        """
        return (
            self.selection_rect.x(),
            self.selection_rect.y(),
            self.selection_rect.width(),
            self.selection_rect.height()
        )


def select_screen_region(parent=None, selection_size=(380, 380)):
    """
    Show the screen selector dialog and return the selected region.

    Args:
        parent: Parent widget
        selection_size: Size of the selection box (width, height)

    Returns:
        A tuple (x, y, width, height) representing the selected region,
        or None if the user cancelled
    """
    # Create the selector without a parent to ensure it's a top-level window
    selector = ScreenSelector(None, selection_size)

    # Use exec_ to make it modal
    result = selector.exec_()

    if result == QDialog.Accepted:
        return selector.get_selection()
    else:
        return None


def save_selection(selection, file_path):
    """
    Save the selection to a file.

    Args:
        selection: A tuple (x, y, width, height) representing the selected region
        file_path: Path to save the selection to
    """
    if selection is None:
        return

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save the selection
    with open(file_path, 'w') as f:
        json.dump({
            'x': selection[0],
            'y': selection[1],
            'width': selection[2],
            'height': selection[3]
        }, f)


def load_selection(file_path):
    """
    Load the selection from a file.

    Args:
        file_path: Path to load the selection from

    Returns:
        A tuple (x, y, width, height) representing the selected region,
        or None if the file doesn't exist
    """
    if not os.path.exists(file_path):
        return None

    # Load the selection
    with open(file_path, 'r') as f:
        data = json.load(f)
        return (data['x'], data['y'], data['width'], data['height'])
