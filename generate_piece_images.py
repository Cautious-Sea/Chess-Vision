"""
Generate Chess Piece Images.

This script generates PNG images for chess pieces using the python-chess library.
"""

import os
import sys
import chess
import chess.svg
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import QByteArray, QSize, Qt
from PyQt5.QtWidgets import QApplication

# Define the output directory
OUTPUT_DIR = os.path.join("data", "images", "pieces")

# Create the output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define the piece types and colors
piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
colors = [chess.WHITE, chess.BLACK]

# Define the size of the piece images
SIZE = 200

def generate_piece_image(piece, output_path):
    """Generate a PNG image for a chess piece."""
    # Generate SVG for the piece
    svg_data = chess.svg.piece(piece=piece, size=SIZE)

    # Create a QSvgRenderer
    renderer = QSvgRenderer(QByteArray(svg_data.encode()))

    # Create a pixmap to render to
    pixmap = QPixmap(SIZE, SIZE)
    pixmap.fill(Qt.transparent)  # Transparent background

    # Create a painter
    painter = QPainter(pixmap)

    # Render the SVG
    renderer.render(painter)

    # End painting
    painter.end()

    # Save the pixmap
    pixmap.save(output_path)

    print(f"Generated {output_path}")

def main():
    """Generate all piece images."""
    # Create a QApplication instance (required for QPixmap)
    app = QApplication(sys.argv)

    for color in colors:
        color_prefix = "w" if color else "b"

        for piece_type in piece_types:
            # Get the piece symbol
            piece = chess.Piece(piece_type, color)
            piece_symbol = piece.symbol().lower()

            # Define the output file name
            file_name = f"{color_prefix}{piece_symbol}.png"
            output_path = os.path.join(OUTPUT_DIR, file_name)

            # Generate the piece image
            generate_piece_image(piece, output_path)

if __name__ == "__main__":
    main()
