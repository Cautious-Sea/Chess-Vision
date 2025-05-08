"""
Chess Board View Module.

This module provides a graphical representation of a chess board using PyQt5.
"""

import os
import chess
from PyQt5.QtCore import Qt, QSize, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen
from PyQt5.QtWidgets import QWidget


class ChessBoardView(QWidget):
    """
    A widget that displays a chess board with pieces.

    This widget can display a chess position based on a provided chess.Board object
    or a FEN string. It handles rendering the board, pieces, and highlighting squares.
    """

    # Colors for the chess board
    LIGHT_SQUARE_COLOR = QColor(240, 217, 181)  # Light brown
    DARK_SQUARE_COLOR = QColor(181, 136, 99)    # Dark brown
    HIGHLIGHT_COLOR = QColor(106, 168, 79, 150)  # Green highlight for moves
    LAST_MOVE_COLOR = QColor(205, 210, 106, 150)  # Yellow highlight for last move

    # Piece image directory - we'll need to add these later
    PIECE_IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                  "data", "images", "pieces")

    def __init__(self, parent=None):
        """Initialize the chess board view."""
        super().__init__(parent)

        # Set up the board
        self.board = chess.Board()

        # Set up the board size and square size
        self.board_size = 600  # Increased from 400 to 600
        self.square_size = self.board_size // 8

        # Set up the piece images
        self.piece_images = {}

        # Set up highlighting
        self.highlighted_squares = []
        self.last_move_squares = []

        # Set up the widget
        self.setMinimumSize(self.board_size, self.board_size)
        self.setMaximumSize(self.board_size, self.board_size)

        # Load piece images if the directory exists
        self._load_piece_images()

    def _load_piece_images(self):
        """Load the chess piece images."""
        # Check if the piece image directory exists
        if not os.path.exists(self.PIECE_IMAGE_DIR):
            print(f"Warning: Piece image directory not found: {self.PIECE_IMAGE_DIR}")
            return

        # Load images for each piece
        piece_types = ['p', 'n', 'b', 'r', 'q', 'k']
        colors = ['w', 'b']

        for color in colors:
            for piece_type in piece_types:
                piece_symbol = piece_type.upper() if color == 'w' else piece_type
                file_name = f"{color}{piece_type}.png"
                file_path = os.path.join(self.PIECE_IMAGE_DIR, file_name)

                if os.path.exists(file_path):
                    pixmap = QPixmap(file_path)
                    scaled_pixmap = pixmap.scaled(
                        QSize(self.square_size, self.square_size),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.piece_images[piece_symbol] = scaled_pixmap
                else:
                    print(f"Warning: Piece image not found: {file_path}")

    def set_board(self, board):
        """Set the chess board to display."""
        self.board = board
        self.update()

    def set_board_from_fen(self, fen):
        """Set the chess board from a FEN string."""
        try:
            self.board = chess.Board(fen)
            self.update()
            return True
        except ValueError as e:
            print(f"Error setting board from FEN: {e}")
            return False

    def highlight_squares(self, squares):
        """Highlight the specified squares."""
        self.highlighted_squares = squares
        self.update()

    def highlight_last_move(self, move):
        """Highlight the squares involved in the last move."""
        if move:
            self.last_move_squares = [move.from_square, move.to_square]
        else:
            self.last_move_squares = []
        self.update()

    def clear_highlights(self):
        """Clear all highlighted squares."""
        self.highlighted_squares = []
        self.last_move_squares = []
        self.update()

    def square_at(self, point):
        """Get the chess square at the given point."""
        x, y = point.x(), point.y()

        # Check if the point is within the board
        if x < 0 or x >= self.board_size or y < 0 or y >= self.board_size:
            return None

        # Calculate the file and rank
        file_idx = x // self.square_size
        rank_idx = 7 - (y // self.square_size)  # Invert rank because chess board has rank 1 at the bottom

        # Convert to chess.Square
        return chess.square(file_idx, rank_idx)

    def paintEvent(self, event):
        """Paint the chess board and pieces."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the board
        self._draw_board(painter)

        # Draw the highlights
        self._draw_highlights(painter)

        # Draw the pieces
        self._draw_pieces(painter)

    def _draw_board(self, painter):
        """Draw the chess board squares."""
        for rank in range(8):
            for file in range(8):
                # Determine the square color
                is_light = (rank + file) % 2 == 0
                color = self.LIGHT_SQUARE_COLOR if is_light else self.DARK_SQUARE_COLOR

                # Calculate the square position
                x = file * self.square_size
                y = (7 - rank) * self.square_size  # Invert rank because chess board has rank 1 at the bottom

                # Draw the square
                painter.fillRect(x, y, self.square_size, self.square_size, color)

    def _draw_highlights(self, painter):
        """Draw highlighted squares."""
        # Draw last move highlights
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.LAST_MOVE_COLOR)

        for square in self.last_move_squares:
            file_idx = chess.square_file(square)
            rank_idx = chess.square_rank(square)
            x = file_idx * self.square_size
            y = (7 - rank_idx) * self.square_size
            painter.drawRect(x, y, self.square_size, self.square_size)

        # Draw other highlights
        painter.setBrush(self.HIGHLIGHT_COLOR)

        for square in self.highlighted_squares:
            file_idx = chess.square_file(square)
            rank_idx = chess.square_rank(square)
            x = file_idx * self.square_size
            y = (7 - rank_idx) * self.square_size
            painter.drawRect(x, y, self.square_size, self.square_size)

    def _draw_pieces(self, painter):
        """Draw the chess pieces."""
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)

            if piece:
                # Get the piece symbol
                piece_symbol = piece.symbol()

                # Calculate the square position
                file_idx = chess.square_file(square)
                rank_idx = chess.square_rank(square)
                x = file_idx * self.square_size
                y = (7 - rank_idx) * self.square_size

                # Draw the piece if we have an image for it
                if piece_symbol in self.piece_images:
                    painter.drawPixmap(x, y, self.piece_images[piece_symbol])
                else:
                    # Fallback: draw a colored rectangle with the piece symbol
                    color = Qt.white if piece.color else Qt.black
                    painter.setPen(Qt.black)
                    painter.setBrush(QColor(200, 200, 200, 100))
                    painter.drawRect(x, y, self.square_size, self.square_size)
                    painter.setPen(color)
                    painter.drawText(QRect(x, y, self.square_size, self.square_size),
                                    Qt.AlignCenter, piece_symbol)
