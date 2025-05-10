"""
FEN Generator Module.

This module provides functionality for generating FEN notation from detected chess pieces.
"""

import chess


class FENGenerator:
    """
    A class for generating FEN notation from detected chess pieces.

    This class handles mapping detected pieces to chess squares and
    generating FEN notation for the detected position.
    """

    def __init__(self, board_size=(395, 395)):
        """
        Initialize the FEN generator.

        Args:
            board_size: Size of the chess board (width, height)
        """
        self.board_size = board_size
        self.square_size = (board_size[0] // 8, board_size[1] // 8)

        # Initialize the chess board
        self.board = chess.Board()

        # Map piece classes to FEN symbols
        self.piece_map = {
            'wp': chess.Piece(chess.PAWN, chess.WHITE),
            'wn': chess.Piece(chess.KNIGHT, chess.WHITE),
            'wb': chess.Piece(chess.BISHOP, chess.WHITE),
            'wr': chess.Piece(chess.ROOK, chess.WHITE),
            'wq': chess.Piece(chess.QUEEN, chess.WHITE),
            'wk': chess.Piece(chess.KING, chess.WHITE),
            'bp': chess.Piece(chess.PAWN, chess.BLACK),
            'bn': chess.Piece(chess.KNIGHT, chess.BLACK),
            'bb': chess.Piece(chess.BISHOP, chess.BLACK),
            'br': chess.Piece(chess.ROOK, chess.BLACK),
            'bq': chess.Piece(chess.QUEEN, chess.BLACK),
            'bk': chess.Piece(chess.KING, chess.BLACK)
        }

        # Flag to track board orientation (True if white is at the bottom)
        self.white_at_bottom = True

    def detect_orientation(self, detected_pieces):
        """
        Detect the orientation of the chess board.

        Args:
            detected_pieces: List of detected pieces

        Returns:
            True if white is at the bottom, False otherwise
        """
        # Count white and black pieces in the bottom half of the board
        white_bottom = 0
        black_bottom = 0

        for piece in detected_pieces:
            # Get the piece center
            _, center_y = piece["center"]

            # Check if the piece is in the bottom half of the board
            if center_y > self.board_size[1] // 2:
                if piece["class"].startswith("w"):
                    white_bottom += 1
                elif piece["class"].startswith("b"):
                    black_bottom += 1

        # Determine orientation based on which color has more pieces in the bottom half
        self.white_at_bottom = white_bottom >= black_bottom
        return self.white_at_bottom

    def center_to_square(self, center):
        """
        Convert a center point to a chess square.

        Args:
            center: A tuple (x, y) representing the center point

        Returns:
            A chess.Square representing the square
        """
        x, y = center

        # Calculate the file and rank indices (0-7)
        file_idx = min(7, max(0, int(x * 8 / self.board_size[0])))
        rank_idx = min(7, max(0, int(y * 8 / self.board_size[1])))

        # Adjust for board orientation
        if self.white_at_bottom:
            # If white is at the bottom, rank 0 is at the bottom (rank_idx needs to be flipped)
            rank_idx = 7 - rank_idx
        else:
            # If black is at the bottom, file 0 is at the right (file_idx needs to be flipped)
            file_idx = 7 - file_idx

        # Convert to chess.Square
        return chess.square(file_idx, rank_idx)

    def generate_fen(self, detected_pieces):
        """
        Generate FEN notation from detected pieces.

        Args:
            detected_pieces: List of detected pieces

        Returns:
            The FEN notation for the detected position
        """
        # Detect board orientation
        self.detect_orientation(detected_pieces)

        # Create a new empty board
        self.board.clear()

        # Place the detected pieces on the board
        for piece in detected_pieces:
            # Get the piece class and center
            piece_class = piece["class"]
            center = piece["center"]

            # Skip if the piece class is not in the piece map
            if piece_class not in self.piece_map:
                continue

            # Get the chess piece and square
            chess_piece = self.piece_map[piece_class]
            square = self.center_to_square(center)

            # Place the piece on the board
            self.board.set_piece_at(square, chess_piece)

        # Generate the board part of the FEN
        board_fen = self.board.board_fen()

        # Set default values for the rest of the FEN components
        # Assume white to move, all castling rights, no en passant, 0 halfmove clock, 1 fullmove number
        side_to_move = 'w'
        castling = 'KQkq'
        en_passant = '-'
        halfmove_clock = '0'
        fullmove_number = '1'

        # Combine all components to create the full FEN
        fen = f"{board_fen} {side_to_move} {castling} {en_passant} {halfmove_clock} {fullmove_number}"

        return fen

    def get_board(self):
        """
        Get the current chess board.

        Returns:
            The current chess.Board object
        """
        return self.board
