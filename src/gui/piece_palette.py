"""
Chess Piece Palette Module.

This module provides a widget for selecting chess pieces to place on the board.
"""

import os
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QMimeData
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen, QDrag
from PyQt5.QtWidgets import QWidget


class ChessPiecePalette(QWidget):
    """
    A widget that displays a palette of chess pieces that can be dragged onto the board.
    """

    def __init__(self, parent=None):
        """Initialize the chess piece palette."""
        super().__init__(parent)

        # Set up the piece images
        self.piece_images = {}

        # Set up the palette size
        self.piece_size = 40  # Size of each piece in the palette
        self.padding = 5      # Padding between pieces

        # Set up the pieces to display
        self.pieces = ['K', 'Q', 'R', 'B', 'N', 'P', 'k', 'q', 'r', 'b', 'n', 'p', 'X']  # X is for clear square

        # Calculate the palette width and height
        self.palette_width = len(self.pieces) * (self.piece_size + self.padding) + self.padding
        self.palette_height = self.piece_size + 2 * self.padding

        # Set up the widget
        self.setMinimumSize(self.palette_width, self.palette_height)
        self.setMaximumHeight(self.palette_height)

        # Enable focus to receive key events
        self.setFocusPolicy(Qt.StrongFocus)

        # Set up the piece image directory
        self.piece_image_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                          "data", "images", "pieces")

        # Load piece images
        self._load_piece_images()

    def _load_piece_images(self):
        """Load the chess piece images."""
        # Check if the piece image directory exists
        if not os.path.exists(self.piece_image_dir):
            print(f"Warning: Piece image directory not found: {self.piece_image_dir}")
            return

        # Load images for each piece
        piece_types = ['p', 'n', 'b', 'r', 'q', 'k']
        colors = ['w', 'b']

        for color in colors:
            for piece_type in piece_types:
                piece_symbol = piece_type.upper() if color == 'w' else piece_type
                file_name = f"{color}{piece_type}.png"
                file_path = os.path.join(self.piece_image_dir, file_name)

                if os.path.exists(file_path):
                    pixmap = QPixmap(file_path)
                    scaled_pixmap = pixmap.scaled(
                        QSize(self.piece_size, self.piece_size),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.piece_images[piece_symbol] = scaled_pixmap
                else:
                    print(f"Warning: Piece image not found: {file_path}")

    def paintEvent(self, _):
        """Paint the piece palette."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the background
        painter.fillRect(0, 0, self.width(), self.height(), QColor(240, 240, 240))

        # Draw each piece
        x = self.padding
        y = self.padding

        for piece_symbol in self.pieces:
            # Special case for the clear square button
            if piece_symbol == 'X':
                # Draw a red X for the clear square button
                painter.setPen(Qt.black)
                painter.setBrush(QColor(240, 240, 240))
                painter.drawRect(x, y, self.piece_size, self.piece_size)

                # Draw the X
                painter.setPen(QPen(Qt.red, 2))
                painter.drawLine(x + 5, y + 5, x + self.piece_size - 5, y + self.piece_size - 5)
                painter.drawLine(x + self.piece_size - 5, y + 5, x + 5, y + self.piece_size - 5)
            # Draw the piece if we have an image for it
            elif piece_symbol in self.piece_images:
                painter.drawPixmap(x, y, self.piece_images[piece_symbol])
            else:
                # Fallback: draw a colored rectangle with the piece symbol
                color = Qt.white if piece_symbol.isupper() else Qt.black
                painter.setPen(Qt.black)
                painter.setBrush(QColor(200, 200, 200, 100))
                painter.drawRect(x, y, self.piece_size, self.piece_size)
                painter.setPen(color)
                painter.drawText(QRect(x, y, self.piece_size, self.piece_size),
                                Qt.AlignCenter, piece_symbol)

            # Move to the next piece position
            x += self.piece_size + self.padding

    def mousePressEvent(self, event):
        """Handle mouse press events for piece selection."""
        if event.button() == Qt.LeftButton:
            # Get the piece at the mouse position
            piece = self._piece_at_position(event.pos())

            if piece:
                # Create a mime data object to store the piece symbol
                mime_data = QMimeData()
                mime_data.setText(piece)

                # Create a pixmap for the drag image
                if piece in self.piece_images:
                    pixmap = self.piece_images[piece]
                else:
                    # Create a fallback pixmap
                    pixmap = QPixmap(self.piece_size, self.piece_size)
                    pixmap.fill(Qt.transparent)
                    painter = QPainter(pixmap)
                    color = Qt.white if piece.isupper() else Qt.black
                    painter.setPen(Qt.black)
                    painter.setBrush(QColor(200, 200, 200, 100))
                    painter.drawRect(0, 0, self.piece_size, self.piece_size)
                    painter.setPen(color)
                    painter.drawText(QRect(0, 0, self.piece_size, self.piece_size),
                                    Qt.AlignCenter, piece)
                    painter.end()

                # Create a drag object
                drag = QDrag(self)
                drag.setMimeData(mime_data)
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(self.piece_size // 2, self.piece_size // 2))

                # Execute the drag operation
                result = drag.exec_(Qt.CopyAction)
                print(f"Drag result: {result}")

    def mouseMoveEvent(self, _):
        """Handle mouse move events."""
        # We don't need to do anything here since we're using QDrag
        pass

    def mouseReleaseEvent(self, _):
        """Handle mouse release events."""
        # We don't need to do anything here since we're using QDrag
        pass

    def _piece_at_position(self, pos):
        """Get the piece at the given position."""
        # Check if the position is within the palette
        if pos.y() < self.padding or pos.y() >= self.padding + self.piece_size:
            return None

        # Calculate the piece index
        x = pos.x() - self.padding
        piece_index = x // (self.piece_size + self.padding)

        # Check if the index is valid
        if piece_index < 0 or piece_index >= len(self.pieces):
            return None

        # Check if the position is within the piece
        piece_x = self.padding + piece_index * (self.piece_size + self.padding)
        if pos.x() < piece_x or pos.x() >= piece_x + self.piece_size:
            return None

        # Return the piece symbol
        return self.pieces[piece_index]
