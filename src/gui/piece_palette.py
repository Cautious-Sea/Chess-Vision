"""
Chess Piece Palette Module.

This module provides a widget for selecting chess pieces to place on the board.
"""

import os
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QMimeData
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen, QDrag
from PyQt5.QtWidgets import QWidget, QSizePolicy


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
        self.piece_size = 60  # Restore original piece size
        self.padding = 5      # Restore original padding

        # Set up the pieces to display in two rows, limiting to 4 pieces per row to match board width
        # This will create two rows with 4 pieces each, plus the clear button
        self.white_pieces = ['K', 'Q', 'R', 'B']  # White pieces (first row)
        self.black_pieces = ['k', 'q', 'r', 'b']  # Black pieces (second row)
        self.second_white_pieces = ['N', 'P']  # Additional white pieces (third row)
        self.second_black_pieces = ['n', 'p']  # Additional black pieces (third row)
        self.clear_button = 'X'  # Clear square button (added to the end of the third row)

        # Calculate the number of pieces per row (limit to 4 to match board width)
        self.pieces_per_row = 4  # Limit to 4 pieces per row to match board width

        # Calculate the palette width and height
        self.palette_width = self.pieces_per_row * (self.piece_size + self.padding) + self.padding
        self.palette_height = 2 * (self.piece_size + self.padding) + self.padding  # Two rows

        # Set up the widget
        self.setMinimumSize(self.palette_width, self.palette_height)
        self.setMaximumHeight(self.palette_height)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

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

        # Draw the background as light gray to match the control panel
        painter.fillRect(0, 0, self.width(), self.height(), QColor(240, 240, 240))

        # Draw white pieces (first row)
        x = self.padding
        y = self.padding

        for piece_symbol in self.white_pieces:
            self._draw_piece(painter, piece_symbol, x, y)
            x += self.piece_size + self.padding

        # Draw black pieces (second row)
        x = self.padding
        y += self.piece_size + self.padding

        for piece_symbol in self.black_pieces:
            self._draw_piece(painter, piece_symbol, x, y)
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

    def _draw_piece(self, painter, piece_symbol, x, y):
        """Draw a chess piece at the specified position."""
        if piece_symbol in self.piece_images:
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

    def _draw_clear_button(self, painter, x, y):
        """Draw the clear square button at the specified position."""
        # Draw a red X for the clear square button
        painter.setPen(Qt.black)
        painter.setBrush(QColor(240, 240, 240))  # Match the light gray background
        painter.drawRect(x, y, self.piece_size, self.piece_size)

        # Draw the X
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(x + 5, y + 5, x + self.piece_size - 5, y + self.piece_size - 5)
        painter.drawLine(x + self.piece_size - 5, y + 5, x + 5, y + self.piece_size - 5)

    def _piece_at_position(self, pos):
        """Get the piece at the given position."""
        # Calculate the row and column
        row = (pos.y() - self.padding) // (self.piece_size + self.padding)
        col = (pos.x() - self.padding) // (self.piece_size + self.padding)

        # Check if the position is within the palette
        if row < 0 or row >= 2 or col < 0 or col >= self.pieces_per_row:
            return None

        # Check if the position is within a piece
        piece_x = self.padding + col * (self.piece_size + self.padding)
        piece_y = self.padding + row * (self.piece_size + self.padding)

        if pos.x() < piece_x or pos.x() >= piece_x + self.piece_size or \
           pos.y() < piece_y or pos.y() >= piece_y + self.piece_size:
            return None

        # Determine which piece is at this position
        if row == 0:  # First row (white pieces)
            if col < len(self.white_pieces):
                return self.white_pieces[col]
        else:  # Second row (black pieces)
            if col < len(self.black_pieces):
                return self.black_pieces[col]

        return None
