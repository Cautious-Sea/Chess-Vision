"""
Chess Board View Module.

This module provides a graphical representation of a chess board using PyQt5.
"""

import os
import chess
from PyQt5.QtCore import Qt, QSize, QRect, QPoint, QPointF
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen, QPolygonF
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

    # Colors for arrows
    ARROW_COLORS = [
        QColor(255, 0, 0, 180),    # Red for best move
        QColor(0, 0, 255, 180),    # Blue for second best
        QColor(0, 128, 0, 180),    # Green for third best
        QColor(128, 0, 128, 180),  # Purple for fourth best
        QColor(255, 165, 0, 180)   # Orange for fifth best
    ]

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

        # Set up arrows for best moves
        self.arrows = []  # List of (from_square, to_square, color_index) tuples

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
        self.arrows = []
        self.update()

    def set_arrows(self, arrows):
        """
        Set arrows to display on the board.

        Args:
            arrows: List of (from_square, to_square, color_index) tuples
        """
        self.arrows = arrows
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

        # Draw the arrows
        self._draw_arrows(painter)

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

    def _draw_arrows(self, painter):
        """Draw arrows for best moves."""
        if not self.arrows:
            return

        # Set up the arrow properties
        arrow_width = self.square_size // 10
        head_size = self.square_size // 4

        for from_square, to_square, color_idx in self.arrows:
            # Get the color for this arrow
            color = self.ARROW_COLORS[color_idx % len(self.ARROW_COLORS)]

            # Calculate the center points of the squares
            from_file = chess.square_file(from_square)
            from_rank = chess.square_rank(from_square)
            to_file = chess.square_file(to_square)
            to_rank = chess.square_rank(to_square)

            # Calculate center coordinates
            from_x = from_file * self.square_size + self.square_size // 2
            from_y = (7 - from_rank) * self.square_size + self.square_size // 2
            to_x = to_file * self.square_size + self.square_size // 2
            to_y = (7 - to_rank) * self.square_size + self.square_size // 2

            # Create points for the arrow
            from_point = QPointF(from_x, from_y)
            to_point = QPointF(to_x, to_y)

            # Calculate the direction vector
            dx = to_x - from_x
            dy = to_y - from_y
            length = (dx**2 + dy**2)**0.5

            if length < 1e-6:  # Avoid division by zero
                continue

            # Normalize the direction vector
            dx /= length
            dy /= length

            # Calculate perpendicular vector for arrow width
            perpx = -dy
            perpy = dx

            # Shorten the arrow to not cover the pieces completely
            from_point = QPointF(from_x + dx * self.square_size * 0.3, from_y + dy * self.square_size * 0.3)
            to_point = QPointF(to_x - dx * self.square_size * 0.3, to_y - dy * self.square_size * 0.3)

            # Recalculate with new points
            dx = to_point.x() - from_point.x()
            dy = to_point.y() - from_point.y()
            length = (dx**2 + dy**2)**0.5

            if length < 1e-6:  # Avoid division by zero
                continue

            # Normalize again
            dx /= length
            dy /= length

            # Calculate the arrow shaft points
            shaft_left_start = QPointF(from_point.x() + perpx * arrow_width, from_point.y() + perpy * arrow_width)
            shaft_right_start = QPointF(from_point.x() - perpx * arrow_width, from_point.y() - perpy * arrow_width)

            # Calculate where the arrowhead starts
            head_base = QPointF(to_point.x() - dx * head_size, to_point.y() - dy * head_size)

            # Calculate the arrowhead points
            shaft_left_end = QPointF(head_base.x() + perpx * arrow_width, head_base.y() + perpy * arrow_width)
            shaft_right_end = QPointF(head_base.x() - perpx * arrow_width, head_base.y() - perpy * arrow_width)

            # Calculate the arrowhead side points
            head_left = QPointF(head_base.x() + perpx * head_size, head_base.y() + perpy * head_size)
            head_right = QPointF(head_base.x() - perpx * head_size, head_base.y() - perpy * head_size)

            # Create polygons for the arrow
            shaft_polygon = QPolygonF()
            shaft_polygon.append(shaft_left_start)
            shaft_polygon.append(shaft_left_end)
            shaft_polygon.append(shaft_right_end)
            shaft_polygon.append(shaft_right_start)

            head_polygon = QPolygonF()
            head_polygon.append(head_left)
            head_polygon.append(to_point)
            head_polygon.append(head_right)
            head_polygon.append(head_base)

            # Draw the arrow
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawPolygon(shaft_polygon)
            painter.drawPolygon(head_polygon)
