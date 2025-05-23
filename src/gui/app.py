"""
Chess Vision Application Module.

This module provides the main application window for the Chess Vision application.
"""

import os
import sys
import chess
import threading
import time
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QGroupBox, QSpinBox, QMessageBox,
    QRadioButton
)
from src.gui.piece_palette import ChessPiecePalette

from src.gui.board_view import ChessBoardView
from src.chess.engine import StockfishEngine
from src.screen.selector import select_screen_region, save_selection, load_selection
from src.detection.detector import ChessPieceDetector
from src.detection.fen_generator import FENGenerator


class ChessVisionApp(QMainWindow):
    """
    Main application window for Chess Vision.

    This class provides the main GUI for the Chess Vision application, including
    the chess board view, controls, and analysis display.
    """

    def __init__(self):
        """Initialize the application window."""
        super().__init__()

        # Set up the window
        self.setWindowTitle("Chess Vision")
        self.setMinimumSize(900, 750)  # Increased window size to accommodate the piece palette

        # Set up the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create horizontal layout for board and controls
        self.board_controls_layout = QHBoxLayout()

        # Create the board view
        self.board_view = ChessBoardView()

        # Initialize the Stockfish engine
        self.engine = StockfishEngine(depth=15)
        self.is_analyzing = False
        self.analysis_thread = None
        self.analysis_running = False

        # Set up the screen selection
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "config")
        self.selection_file = os.path.join(self.config_dir, "screen_selection.json")
        self.screen_selection = load_selection(self.selection_file)

        # Initialize the detector and FEN generator
        self.detector = ChessPieceDetector()
        self.fen_generator = FENGenerator()

        # Set up detection variables
        self.detection_running = False
        self.detection_thread = None
        self.current_detections = []
        self.current_image = None
        self.last_fen = None
        self.pending_fen = None
        self.auto_update_enabled = False  # Flag to track if auto-update is enabled

        # Variables for FEN stability detection
        self.recent_fens = []  # List to store recent FENs
        self.consecutive_identical_fens = 0  # Counter for consecutive identical FENs
        self.stable_fen_threshold = 10  # Number of consecutive identical FENs required for stability

        # Set up board state tracking
        self.previous_board = chess.Board()  # Track the previous board state

        # Set up board state history for undo/redo
        self.board_history = []  # Stack of previous board states for undo
        self.redo_stack = []     # Stack of undone board states for redo

        # Create the control panel
        self.control_panel = self._create_control_panel()

        # Create the piece palette
        self.piece_palette = ChessPiecePalette()

        # Add widgets to the board controls layout with a 4:1 ratio (board:controls)
        self.board_controls_layout.addWidget(self.board_view, 4)
        self.board_controls_layout.addWidget(self.control_panel, 1)

        # Add the board controls layout to the main layout (giving it more space)
        self.main_layout.addLayout(self.board_controls_layout, 10)

        # Add the piece palette to the main layout (giving it less space but enough to be visible)
        self.main_layout.addWidget(self.piece_palette, 1)

        # Set up the board with the initial position
        self.board_view.set_board(chess.Board())

        # Set up the move callback
        self.board_view.set_move_made_callback(self._on_move_made)

        # Set up move history
        self.move_history = []

        # Set up a timer for periodic UI updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(500)  # Update every 500ms

        # Analysis results
        self.current_analysis = []

    def _create_control_panel(self):
        """Create the control panel widget."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        layout.setSpacing(5)  # Reduce spacing between widgets

        # Position control group
        position_group = QGroupBox("Position")
        position_layout = QVBoxLayout(position_group)
        position_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins
        position_layout.setSpacing(8)  # Increase spacing

        # FEN input - more compact layout
        fen_layout = QHBoxLayout()
        fen_layout.setSpacing(3)  # Reduce spacing
        fen_label = QLabel("FEN:")
        self.fen_input = QLineEdit()
        self.fen_input.setText(chess.STARTING_FEN)
        self.fen_input.setMaximumWidth(250)  # Limit width
        fen_layout.addWidget(fen_label)
        fen_layout.addWidget(self.fen_input)

        # Button layout - horizontal to save space
        button_layout = QHBoxLayout()
        button_layout.setSpacing(3)  # Reduce spacing

        # Set position button
        set_position_button = QPushButton("Set Position")
        set_position_button.clicked.connect(self._on_set_position)
        set_position_button.setMaximumWidth(100)

        # Reset button
        reset_button = QPushButton("Reset")  # Shorter text
        reset_button.clicked.connect(self._on_reset)
        reset_button.setMaximumWidth(70)

        # Add buttons to layout
        button_layout.addWidget(set_position_button)
        button_layout.addWidget(reset_button)
        button_layout.addStretch(1)

        # Auto-update button layout
        auto_update_layout = QHBoxLayout()
        auto_update_layout.setSpacing(3)  # Reduce spacing

        # Auto-update button
        self.auto_update_button = QPushButton("Auto Update: OFF")
        self.auto_update_button.clicked.connect(self._on_toggle_auto_update)
        self.auto_update_button.setMaximumWidth(120)

        # Add auto-update button to layout
        auto_update_layout.addWidget(self.auto_update_button)
        auto_update_layout.addStretch(1)

        # Add widgets to position layout
        position_layout.addLayout(fen_layout)
        position_layout.addLayout(button_layout)
        position_layout.addLayout(auto_update_layout)



        # Analysis group
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins
        analysis_layout.setSpacing(3)  # Reduce spacing

        # Analysis display
        self.analysis_label = QLabel("No analysis available")
        self.analysis_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.analysis_label.setWordWrap(True)
        self.analysis_label.setMinimumHeight(80)  # Reduced height

        # Analysis options
        options_layout = QHBoxLayout()
        options_layout.setSpacing(3)  # Reduce spacing

        # Depth selection
        depth_label = QLabel("Depth:")
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 30)
        self.depth_spin.setValue(15)
        self.depth_spin.setMaximumWidth(50)
        self.depth_spin.valueChanged.connect(self._on_depth_changed)

        # Lines selection
        lines_label = QLabel("Lines:")
        self.lines_spin = QSpinBox()
        self.lines_spin.setRange(1, 5)
        self.lines_spin.setValue(1)
        self.lines_spin.setMaximumWidth(50)
        self.lines_spin.valueChanged.connect(self._on_lines_changed)

        # Add to options layout
        options_layout.addWidget(depth_label)
        options_layout.addWidget(self.depth_spin)
        options_layout.addWidget(lines_label)
        options_layout.addWidget(self.lines_spin)
        options_layout.addStretch(1)

        # Start/stop analysis button
        self.analysis_button = QPushButton("Start Analysis")
        self.analysis_button.clicked.connect(self._on_toggle_analysis)
        self.analysis_button.setMaximumWidth(100)

        # Add widgets to analysis layout
        analysis_layout.addWidget(self.analysis_label)
        analysis_layout.addLayout(options_layout)
        analysis_layout.addWidget(self.analysis_button, 0, Qt.AlignLeft)  # Align left



        # Screen selection group
        screen_group = QGroupBox("Screen Selection")
        screen_layout = QVBoxLayout(screen_group)
        screen_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins
        screen_layout.setSpacing(3)  # Reduce spacing

        # Selection status
        self.selection_label = QLabel("No region selected")
        if self.screen_selection:
            x, y, w, h = self.screen_selection
            self.selection_label.setText(f"Selected region: ({x}, {y}, {w}x{h})")

        # Select button
        select_button = QPushButton("Select Chess Board")
        select_button.clicked.connect(self._on_select_board)

        # Add widgets to screen layout
        screen_layout.addWidget(self.selection_label)
        screen_layout.addWidget(select_button)

        # Detection group
        detection_group = QGroupBox("Detection")
        detection_layout = QVBoxLayout(detection_group)
        detection_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins
        detection_layout.setSpacing(3)  # Reduce spacing

        # Detection status
        self.detection_label = QLabel("Detection not running")

        # Start/stop detection button
        self.detection_button = QPushButton("Start Detection")
        self.detection_button.clicked.connect(self._on_toggle_detection)

        # Reset to detected position button
        reset_to_detected_button = QPushButton("Reset to Detected Position")
        reset_to_detected_button.clicked.connect(self._on_reset_to_detected)

        # Adjust detection area button
        adjust_area_button = QPushButton("Adjust Detection Area")
        adjust_area_button.clicked.connect(self._on_adjust_detection_area)

        # Add widgets to detection layout
        detection_layout.addWidget(self.detection_label)
        detection_layout.addWidget(self.detection_button)
        detection_layout.addWidget(reset_to_detected_button)
        detection_layout.addWidget(adjust_area_button)

        # Board Controls group
        board_controls_group = QGroupBox("Board Controls")
        board_controls_layout = QVBoxLayout(board_controls_group)
        board_controls_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins
        board_controls_layout.setSpacing(3)  # Reduce spacing

        # Flip board button
        flip_board_button = QPushButton("Flip Board")
        flip_board_button.clicked.connect(self._on_flip_board)

        # Undo/Redo buttons layout
        undo_redo_layout = QHBoxLayout()
        undo_redo_layout.setSpacing(3)

        # Undo button
        self.undo_button = QPushButton("Undo")
        self.undo_button.clicked.connect(self._on_undo)
        self.undo_button.setMaximumWidth(80)
        self.undo_button.setEnabled(False)  # Disabled initially

        # Redo button
        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self._on_redo)
        self.redo_button.setMaximumWidth(80)
        self.redo_button.setEnabled(False)  # Disabled initially

        # Add undo/redo buttons to layout
        undo_redo_layout.addWidget(self.undo_button)
        undo_redo_layout.addWidget(self.redo_button)
        undo_redo_layout.addStretch(1)

        # Turn selector
        turn_layout = QHBoxLayout()
        turn_layout.setSpacing(3)
        turn_label = QLabel("Turn:")

        # Create radio buttons for white and black
        self.white_turn_radio = QRadioButton("White")
        self.black_turn_radio = QRadioButton("Black")
        self.white_turn_radio.setChecked(True)  # White moves first by default

        # Connect radio buttons to handler
        self.white_turn_radio.toggled.connect(self._on_turn_changed)
        self.black_turn_radio.toggled.connect(self._on_turn_changed)

        # Add radio buttons to layout
        turn_layout.addWidget(turn_label)
        turn_layout.addWidget(self.white_turn_radio)
        turn_layout.addWidget(self.black_turn_radio)

        # Add widgets to board controls layout
        board_controls_layout.addWidget(flip_board_button)
        board_controls_layout.addLayout(undo_redo_layout)
        board_controls_layout.addLayout(turn_layout)

        # Add groups to main layout in the specified order
        layout.addWidget(position_group)        # 1. Position Section
        layout.addWidget(board_controls_group)  # 2. Board Controls
        layout.addWidget(analysis_group)        # 3. Analysis
        layout.addWidget(screen_group)          # 4. Screen Selection
        layout.addWidget(detection_group)       # 5. Detections
        layout.addStretch(1)

        # Set a fixed width for the panel
        panel.setMaximumWidth(280)  # Limit the width of the control panel

        return panel

    def _on_set_position(self):
        """
        Handle the Set Position button click.

        This method takes the FEN string from the input field and sets the board position.
        This is the only place where the board is updated from the FEN input during detection.
        """
        fen = self.fen_input.text()
        print(f"Setting position from FEN: {fen}")

        try:
            # Save the current board state for undo
            self.board_history.append(self.board_view.board.copy())

            # Clear the redo stack since we're making a new change
            self.redo_stack.clear()

            # Create a new board from the FEN
            new_board = chess.Board(fen)

            # Update the previous board state
            self.previous_board = new_board.copy()

            # Update the board view
            self.board_view.set_board(new_board)

            # Reset the move history
            self.move_history = []

            # Update the turn radio buttons
            self._update_turn_radio_buttons()

            # Store this as the last valid FEN
            self.last_fen = fen

            # Reset FEN stability tracking
            self.recent_fens = []
            self.consecutive_identical_fens = 0

            # Enable the undo button
            self.undo_button.setEnabled(True)

            # Disable the redo button since we've made a new change
            self.redo_button.setEnabled(False)

            print(f"Successfully set position from FEN: {fen}")

            # Show a confirmation message
            QMessageBox.information(
                self,
                "Position Set",
                "Board has been updated with the FEN position."
            )
        except Exception as e:
            print(f"Failed to set position from FEN: {fen}, error: {e}")
            self.fen_input.setText(self.board_view.board.fen())

            # Show an error message
            QMessageBox.warning(
                self,
                "Invalid FEN",
                f"Failed to set position from FEN: {e}"
            )

    def _on_reset(self):
        """Handle the Reset button click."""
        # Save the current board state for undo
        self.board_history.append(self.board_view.board.copy())

        # Clear the redo stack since we're making a new change
        self.redo_stack.clear()

        # Create a new board with the starting position
        new_board = chess.Board()

        # Update the previous board state
        self.previous_board = new_board.copy()

        # Update the board view
        self.board_view.set_board(new_board)

        # Update the FEN input field
        self.fen_input.setText(chess.STARTING_FEN)

        # Reset the move history
        self.move_history = []

        # Update the turn radio buttons
        self._update_turn_radio_buttons()

        # Reset FEN stability tracking
        self.recent_fens = []
        self.consecutive_identical_fens = 0

        # Enable the undo button
        self.undo_button.setEnabled(True)

        # Disable the redo button since we've made a new change
        self.redo_button.setEnabled(False)

    def _on_toggle_analysis(self):
        """Toggle analysis on/off."""
        self.is_analyzing = not self.is_analyzing

        if self.is_analyzing:
            self.analysis_button.setText("Stop Analysis")
            self._start_analysis()
        else:
            self.analysis_button.setText("Start Analysis")
            self._stop_analysis()
            self.analysis_label.setText("Analysis stopped")

    def _start_analysis(self):
        """Start the analysis thread."""
        if not self.engine.is_running():
            success = self.engine.start()
            if not success:
                self.analysis_label.setText("Error: Could not start Stockfish engine")
                self.is_analyzing = False
                self.analysis_button.setText("Start Analysis")
                return

        # Start the analysis thread
        self.analysis_running = True
        self.analysis_thread = threading.Thread(target=self._analysis_worker)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()

    def _stop_analysis(self):
        """Stop the analysis thread."""
        self.analysis_running = False
        if self.analysis_thread is not None:
            self.analysis_thread.join(timeout=1.0)
            self.analysis_thread = None

    def _analysis_worker(self):
        """Worker function for the analysis thread."""
        consecutive_errors = 0
        max_consecutive_errors = 3

        while self.analysis_running:
            # Get the current board position
            board = self.board_view.board

            # Analyze the position
            try:
                # The engine.analyze method now has built-in error handling and recovery
                self.current_analysis = self.engine.analyze(board, limit_time=0.1)

                # If we got here without an exception, reset the error counter
                consecutive_errors = 0

            except Exception as e:
                print(f"Analysis error in worker thread: {e}")
                consecutive_errors += 1

                # Provide a placeholder analysis result
                self.current_analysis = [{"score": "Engine error", "pv": "", "moves": []}]

                # If we've had too many consecutive errors, try to restart the engine
                if consecutive_errors >= max_consecutive_errors:
                    print(f"Too many consecutive errors ({consecutive_errors}), restarting engine...")
                    try:
                        # Stop the engine
                        self.engine.stop()
                        # Wait a moment
                        time.sleep(1)
                        # Start it again
                        success = self.engine.start()
                        if success:
                            print("Engine successfully restarted")
                            consecutive_errors = 0
                        else:
                            print("Failed to restart engine")
                    except Exception as restart_error:
                        print(f"Error restarting engine: {restart_error}")

                # Sleep a bit longer after an error
                time.sleep(1)
                continue

            # Sleep to avoid excessive CPU usage
            time.sleep(0.5)

    def _update_ui(self):
        """Update the UI with the latest data."""
        # Update the analysis display
        self._update_analysis_display()

        # Update the detection label
        self._update_detection_label()

        # Check if there's a pending FEN update
        if self.pending_fen:
            # Get the FEN and clear the pending update
            fen = self.pending_fen
            self.pending_fen = None

            # Update the board with the FEN
            self._direct_update_board(fen)

    def _update_detection_label(self):
        """Update the detection label with the latest status."""
        if not self.detection_running:
            return

        # Update the detection label with the number of detected pieces
        if self.current_detections:
            self.detection_label.setText(f"Detected {len(self.current_detections)} pieces")
        else:
            self.detection_label.setText("Detecting...")

    def _update_analysis_display(self):
        """Update the analysis display with the latest results."""
        if not self.is_analyzing or not self.current_analysis:
            return

        # Format the analysis results
        analysis_text = ""
        arrows = []

        for i, analysis in enumerate(self.current_analysis):
            if "score" in analysis:
                line_number = i + 1
                score = analysis["score"]

                # Check if this is an error message
                if score in ["Engine error", "Engine restarting...", "Analysis error"]:
                    # Display the error message
                    analysis_text = f"Engine status: {score}\nPlease wait while the engine recovers..."
                    break

                # Normal analysis processing
                if "moves" in analysis:
                    moves = analysis["moves"]  # This is a list of SAN moves

                    # Limit the number of moves shown in text
                    if len(moves) > 5:
                        moves_text = " ".join(moves[:5]) + "..."
                    else:
                        moves_text = " ".join(moves)

                    analysis_text += f"Line {line_number}: {score} - {moves_text}\n"

                    # Add arrow for the first move of each line
                    if moves and i < 5:  # Limit to 5 arrows
                        # Get the move from the analysis
                        board = self.board_view.board.copy()

                        # Find the move in UCI format
                        for move in board.legal_moves:
                            try:
                                if board.san(move) == moves[0]:
                                    # Add arrow (from_square, to_square, color_index)
                                    arrows.append((move.from_square, move.to_square, i))
                                    break
                            except Exception as e:
                                print(f"Error processing move for arrow: {e}")
                                continue

        # Update the analysis text
        if analysis_text:
            self.analysis_label.setText(analysis_text)
        else:
            self.analysis_label.setText("Waiting for analysis...")

        # Update the arrows on the board
        self.board_view.set_arrows(arrows)

    def _on_depth_changed(self, depth):
        """Handle changes to the analysis depth."""
        self.engine.set_depth(depth)

    def _on_lines_changed(self, lines):
        """Handle changes to the number of analysis lines."""
        self.engine.set_multipv(lines)

    def _on_flip_board(self):
        """Handle the Flip Board button click."""
        # Flip the board
        flipped = self.board_view.flip_board()

        # Update the UI to reflect the new board orientation
        if flipped:
            print("Board flipped: Black pieces at bottom")
        else:
            print("Board flipped: White pieces at bottom")

    def _on_undo(self):
        """Handle the Undo button click."""
        if not self.board_history:
            print("No moves to undo")
            return

        # Get the current board state for potential redo
        current_board = self.board_view.board.copy()

        # Add current state to redo stack
        self.redo_stack.append(current_board)

        # Get the previous board state
        previous_board = self.board_history.pop()

        # Update the board view
        self.board_view.set_board(previous_board)

        # Update the previous board state
        self.previous_board = previous_board.copy()

        # Update the FEN input field
        self.fen_input.setText(previous_board.fen())

        # Update the turn radio buttons
        self._update_turn_radio_buttons()

        # Update button states
        self.redo_button.setEnabled(True)
        self.undo_button.setEnabled(len(self.board_history) > 0)

        print("Undid last move/action")

    def _on_redo(self):
        """Handle the Redo button click."""
        if not self.redo_stack:
            print("No moves to redo")
            return

        # Get the current board state for undo
        current_board = self.board_view.board.copy()

        # Add current state to undo stack
        self.board_history.append(current_board)

        # Get the next board state
        next_board = self.redo_stack.pop()

        # Update the board view
        self.board_view.set_board(next_board)

        # Update the previous board state
        self.previous_board = next_board.copy()

        # Update the FEN input field
        self.fen_input.setText(next_board.fen())

        # Update the turn radio buttons
        self._update_turn_radio_buttons()

        # Update button states
        self.undo_button.setEnabled(True)
        self.redo_button.setEnabled(len(self.redo_stack) > 0)

        print("Redid last undone move/action")

    def _on_toggle_auto_update(self):
        """Toggle auto-update on/off."""
        self.auto_update_enabled = not self.auto_update_enabled

        if self.auto_update_enabled:
            self.auto_update_button.setText("Auto Update: ON")
            print("Auto update enabled")

            # Reset FEN stability tracking
            self.recent_fens = []
            self.consecutive_identical_fens = 0

            # If we have a last_fen, update the board immediately
            if self.last_fen:
                self._auto_update_board(self.last_fen)
        else:
            self.auto_update_button.setText("Auto Update: OFF")
            print("Auto update disabled")

    def _on_turn_changed(self):
        """Handle changes to the turn selector."""
        # Check which radio button is checked
        if self.white_turn_radio.isChecked():
            # Set white to move
            self.board_view.set_turn(True)
            print("Turn set to White")
        else:
            # Set black to move
            self.board_view.set_turn(False)
            print("Turn set to Black")

    def update_from_board_change(self, new_board):
        """
        Update the application state when the board changes.

        Args:
            new_board: The new chess.Board object
        """
        # Update the FEN input field
        self.fen_input.setText(new_board.fen())

        # Update the previous board state
        self.previous_board = new_board.copy()

        # Update the turn radio buttons
        self._update_turn_radio_buttons()

        print(f"Board updated with new FEN: {new_board.fen()}")

    def handle_piece_drop(self, piece_symbol, position):
        """
        Handle a piece being dropped from the palette onto the board.

        Args:
            piece_symbol: The symbol of the piece being dropped (e.g., 'K', 'q', etc.)
            position: The position where the piece was dropped (in parent coordinates)
        """
        print(f"Piece {piece_symbol} dropped at position {position}")

        # Get the global position of the board view (for debugging if needed)
        # board_global_pos = self.board_view.mapToGlobal(self.board_view.rect().topLeft())

        # Get the global position of the drop
        drop_global_pos = self.central_widget.mapToGlobal(position)

        # Calculate the position relative to the board view
        board_pos = self.board_view.mapFromGlobal(drop_global_pos)

        print(f"Board position: {board_pos}")

        # Check if the position is within the board view
        if not self.board_view.rect().contains(board_pos):
            print("Drop position is outside the board view")
            return

        # Get the square at the position
        square = self.board_view.square_at(board_pos)

        if square is not None:
            print(f"Square: {chess.square_name(square)}")

            # Save the current board state for undo
            self.board_history.append(self.board_view.board.copy())

            # Clear the redo stack since we're making a new change
            self.redo_stack.clear()

            # Create a copy of the current board
            new_board = self.board_view.board.copy()

            # Handle the clear square button
            if piece_symbol == 'X':
                # Just remove any existing piece at the square
                new_board.remove_piece_at(square)
                print(f"Cleared square {chess.square_name(square)}")
            else:
                # Remove any existing piece at the square
                new_board.remove_piece_at(square)

                # Add the new piece
                piece_color = chess.WHITE if piece_symbol.isupper() else chess.BLACK
                piece_type = chess.PIECE_SYMBOLS.index(piece_symbol.lower())
                new_board.set_piece_at(square, chess.Piece(piece_type, piece_color))

            # Update the board
            self.board_view.set_board(new_board)

            # Update the FEN input field
            self.fen_input.setText(new_board.fen())

            # Update the previous board state
            self.previous_board = new_board.copy()

            # Update the turn radio buttons
            self._update_turn_radio_buttons()

            # Enable the undo button
            self.undo_button.setEnabled(True)

            # Disable the redo button since we've made a new change
            self.redo_button.setEnabled(False)

            print(f"Piece {piece_symbol} placed at {chess.square_name(square)}")
        else:
            print("Drop position is not on a valid square")

    def _on_reset_to_detected(self):
        """Reset the board to the latest detected position."""
        if self.last_fen:
            print(f"Resetting to detected position: {self.last_fen}")

            try:
                # Save the current board state for undo
                self.board_history.append(self.board_view.board.copy())

                # Clear the redo stack since we're making a new change
                self.redo_stack.clear()

                # Create a new board from the FEN
                new_board = chess.Board(self.last_fen)

                # Update the previous board state
                self.previous_board = new_board.copy()

                # Update the board view
                self.board_view.set_board(new_board)

                # Update the FEN input field
                self.fen_input.setText(self.last_fen)

                # Reset the move history
                self.move_history = []

                # Reset FEN stability tracking
                self.recent_fens = []
                self.consecutive_identical_fens = 0

                # Update the turn radio buttons
                self._update_turn_radio_buttons()

                # Enable the undo button
                self.undo_button.setEnabled(True)

                # Disable the redo button since we've made a new change
                self.redo_button.setEnabled(False)

                # Show a confirmation message
                QMessageBox.information(
                    self,
                    "Position Reset",
                    "Board has been reset to the latest detected position."
                )
            except Exception as e:
                print(f"Error resetting to detected position: {e}")
                QMessageBox.warning(
                    self,
                    "Reset Failed",
                    f"Failed to reset to detected position: {e}"
                )
        else:
            print("No detected position available")
            QMessageBox.warning(
                self,
                "No Position Available",
                "No detected position is available. Start detection first."
            )

    def _on_adjust_detection_area(self):
        """
        Handle the Adjust Detection Area button click.

        This method adjusts the y-coordinate of the detection area by decreasing it by 30 pixels.
        """
        # Check if a screen region is selected
        if self.screen_selection is None:
            QMessageBox.warning(
                self,
                "No Region Selected",
                "Please select a chess board region first."
            )
            return

        # Get the current selection
        x, y, w, h = self.screen_selection

        # Decrease the y-coordinate by 30 pixels (move up)
        new_y = max(0, y - 30)  # Ensure y doesn't go below 0

        # Create the new selection
        new_selection = (x, new_y, w, h)
        self.screen_selection = new_selection

        # Update the selection label
        self.selection_label.setText(f"Selected region: ({x}, {new_y}, {w}x{h})")

        # Save the new selection
        save_selection(new_selection, self.selection_file)

        # Update the detector with the new selection
        self.detector.set_screen_region(new_selection)

        # Show a confirmation message
        QMessageBox.information(
            self,
            "Detection Area Adjusted",
            f"Detection area moved up by 30 pixels.\nNew position: ({x}, {new_y}, {w}x{h})"
        )

        # If detection is running, restart it to apply the new area
        if self.detection_running:
            # Stop and restart detection
            self._stop_detection()
            self._start_detection()

    def _on_select_board(self):
        """Handle the Select Chess Board button click."""
        # Stop analysis if it's running
        was_analyzing = self.is_analyzing
        if was_analyzing:
            self._on_toggle_analysis()

        # Stop detection if it's running
        was_detecting = self.detection_running
        if was_detecting:
            self._on_toggle_detection()

        # Minimize the main window temporarily
        self.showMinimized()

        # Wait a moment for the window to minimize
        QApplication.processEvents()

        # Show the screen selector (without a parent to ensure it's a top-level window)
        selection = select_screen_region(None)

        # Restore the main window
        self.showNormal()
        self.activateWindow()

        # Process the selection
        if selection:
            self.screen_selection = selection
            x, y, w, h = selection
            self.selection_label.setText(f"Selected region: ({x}, {y}, {w}x{h})")

            # Save the selection
            save_selection(selection, self.selection_file)

            # Update the detector with the new selection
            self.detector.set_screen_region(selection)

            # Show a confirmation message
            QMessageBox.information(
                self,
                "Region Selected",
                f"Chess board region selected: ({x}, {y}, {w}x{h})"
            )

            # Restart analysis if it was running
            if was_analyzing:
                self._on_toggle_analysis()

            # Restart detection if it was running
            if was_detecting:
                self._on_toggle_detection()

    def update_from_fen(self, fen):
        """Update the board from a FEN string."""
        print(f"Updating board with FEN: {fen}")

        try:
            # Create a new board from the FEN
            new_board = chess.Board(fen)

            # Try to find what move was made
            move = self._find_move_between_positions(self.previous_board, new_board)

            if move:
                # A move was found, apply it to the previous board
                print(f"Detected move: {self.previous_board.san(move)}")

                # Make the move on the previous board
                self.previous_board.push(move)

                # Use the updated previous board (which has the correct turn)
                self.board_view.set_board(self.previous_board)

                # Add the move to the history
                self.add_move_to_history(self.previous_board.san(move))

                # Update the FEN input field with the current board FEN
                self.fen_input.setText(self.previous_board.fen())

                print(f"Board updated with move: {self.previous_board.san(move)}")
            else:
                # No move was found, just set the board directly
                print("No move detected, setting board directly")

                # Update the previous board
                self.previous_board = new_board.copy()

                # Use the set_board method to update the board
                self.board_view.set_board(new_board)

                # Update the FEN input field
                self.fen_input.setText(fen)

                print(f"Board directly updated with FEN: {fen}")

            return True
        except Exception as e:
            print(f"Error updating board with FEN: {fen}, error: {e}")
            return False

    def add_move_to_history(self, move_san):
        """Add a move to the history display."""
        current_text = self.history_label.text()

        if current_text == "No moves yet":
            self.history_label.setText(move_san)
        else:
            self.history_label.setText(f"{current_text}, {move_san}")

    def _on_toggle_detection(self):
        """Toggle detection on/off."""
        self.detection_running = not self.detection_running

        if self.detection_running:
            # Check if a screen region is selected
            if self.screen_selection is None:
                QMessageBox.warning(
                    self,
                    "No Region Selected",
                    "Please select a chess board region first."
                )
                self.detection_running = False
                return

            # Update the button text
            self.detection_button.setText("Stop Detection")

            # Update the detector with the screen region
            self.detector.set_screen_region(self.screen_selection)

            # Start the detection thread
            self._start_detection()
        else:
            # Update the button text
            self.detection_button.setText("Start Detection")

            # Stop the detection thread
            self._stop_detection()

            # Update the detection label
            self.detection_label.setText("Detection stopped")

    def _start_detection(self):
        """Start the detection thread."""
        # Start the detection thread
        self.detection_running = True
        self.detection_thread = threading.Thread(target=self._detection_worker)
        self.detection_thread.daemon = True
        self.detection_thread.start()

    def _stop_detection(self):
        """Stop the detection thread."""
        self.detection_running = False
        if self.detection_thread is not None:
            self.detection_thread.join(timeout=1.0)
            self.detection_thread = None

    def _detection_worker(self):
        """Worker function for the detection thread."""
        while self.detection_running:
            # Capture and detect
            img, detections = self.detector.detect()

            if img is not None and detections:
                # Save the current image and detections
                self.current_image = img
                self.current_detections = detections

                # Generate FEN
                fen = self.fen_generator.generate_fen(detections)

                # Print debug info
                print(f"Detected {len(detections)} pieces")
                print(f"Generated FEN: {fen}")

                # Validate the FEN
                try:
                    # Validate the FEN by creating a board from it
                    _ = chess.Board(fen)  # Just validate, we don't need the board object

                    # Check if this is a new FEN or the same as the last one
                    if not self.recent_fens or fen != self.recent_fens[-1]:
                        # New FEN detected, reset the counter
                        self.consecutive_identical_fens = 1
                        self.recent_fens.append(fen)
                        # Keep only the last 5 FENs to avoid memory growth
                        if len(self.recent_fens) > 5:
                            self.recent_fens.pop(0)
                        print(f"New FEN detected: {fen}, consecutive count: {self.consecutive_identical_fens}")
                    else:
                        # Same FEN as before, increment the counter
                        self.consecutive_identical_fens += 1
                        print(f"Same FEN detected: {fen}, consecutive count: {self.consecutive_identical_fens}")

                    # If we've seen the same FEN enough times, it's stable
                    if self.consecutive_identical_fens >= self.stable_fen_threshold:
                        # If the FEN has changed from the last processed one, update the board
                        if fen != self.last_fen:
                            self.last_fen = fen
                            print(f"Stable FEN detected ({self.consecutive_identical_fens} times), updating board: {fen}")
                            # Store the FEN to be processed in the main thread
                            self.pending_fen = fen
                    else:
                        print(f"Waiting for stable FEN ({self.consecutive_identical_fens}/{self.stable_fen_threshold})")

                except Exception as e:
                    print(f"Invalid FEN generated: {fen}, error: {e}")
                    # Reset the counter for invalid FENs
                    self.consecutive_identical_fens = 0

            # Sleep to avoid excessive CPU usage
            time.sleep(0.1)

    def _direct_update_board(self, fen):
        """
        Update the FEN input field with the detected FEN string.

        This method is designed to be called from the main UI thread
        to update the FEN input field with a new FEN string from detection.
        If auto-update is enabled, it will also update the board.
        Otherwise, the board is not updated until the user clicks "Set Position".
        """
        print(f"Updating FEN input field with: {fen}")

        try:
            # Validate the FEN by creating a board from it
            _ = chess.Board(fen)  # Just validate, we don't need the board object

            # Update the FEN input field only
            self.fen_input.setText(fen)

            # Store the last valid FEN
            self.last_fen = fen

            print(f"FEN input field updated with: {fen}")

            # If auto-update is enabled, update the board as well
            # Note: The FEN has already been validated as stable by the detection worker
            if self.auto_update_enabled:
                self._auto_update_board(fen)

        except Exception as e:
            print(f"Error updating FEN input field: {e}")

    def _auto_update_board(self, fen):
        """
        Automatically update the board with the detected FEN string.

        This method updates the board and handles the turn correctly based on
        the changes between the previous board state and the new FEN.
        """
        print(f"Auto-updating board with FEN: {fen}")

        try:
            # Save the current board state for undo
            self.board_history.append(self.board_view.board.copy())

            # Clear the redo stack since we're making a new change
            self.redo_stack.clear()

            # Create a new board from the FEN
            new_board = chess.Board(fen)

            # Try to find what move was made
            move = self._find_move_between_positions(self.previous_board, new_board)

            if move:
                # A move was found, apply it to the previous board
                print(f"Detected move: {self.previous_board.san(move)}")

                # Make the move on the previous board
                self.previous_board.push(move)

                # Use the updated previous board (which has the correct turn)
                self.board_view.set_board(self.previous_board)

                # Add the move to the history
                self.add_move_to_history(self.previous_board.san(move))

                # Update the FEN input field with the current board FEN
                self.fen_input.setText(self.previous_board.fen())

                print(f"Board auto-updated with move: {self.previous_board.san(move)}")
            else:
                # No move was found, just set the board directly
                print("No move detected, setting board directly")

                # Update the previous board
                self.previous_board = new_board.copy()

                # Use the set_board method to update the board
                self.board_view.set_board(new_board)

                print(f"Board directly auto-updated with FEN: {fen}")

            # Update the turn radio buttons
            self._update_turn_radio_buttons()

            # Enable the undo button
            self.undo_button.setEnabled(True)

            # Disable the redo button since we've made a new change
            self.redo_button.setEnabled(False)

        except Exception as e:
            print(f"Error auto-updating board: {e}")

    def _safe_update_board(self, fen):
        """
        Safely update the board from a FEN string.

        This method is designed to be called from a QTimer.singleShot to avoid
        recursive repaint issues when updating the board from a background thread.
        """
        print(f"Safely updating board with FEN: {fen}")

        try:
            # Create a new board from the FEN
            new_board = chess.Board(fen)

            # Use the set_board method instead of directly setting the board property
            self.board_view.set_board(new_board)

            # Update the FEN input field
            self.fen_input.setText(fen)

            # Force the application to process events to ensure the UI updates
            QApplication.processEvents()

            print(f"Board safely updated with FEN: {fen}")
        except Exception as e:
            print(f"Error safely updating board: {e}")

    def _update_board_in_gui(self, board, fen):
        """Update the board in the GUI thread."""
        print(f"Updating board in GUI thread with FEN: {fen}")

        try:
            # Use the set_board method instead of directly setting the board property
            self.board_view.set_board(board)

            # Update the FEN input field
            self.fen_input.setText(fen)

            # Force the application to process events to ensure the UI updates
            QApplication.processEvents()

            print(f"Board updated in GUI thread with FEN: {fen}")
        except Exception as e:
            print(f"Error updating board in GUI thread: {e}")

    def _find_move_between_positions(self, previous_board, new_board):
        """
        Find the move that was made between two board positions.

        Args:
            previous_board: The previous board position
            new_board: The new board position

        Returns:
            The move that was made, or None if no move could be determined
        """
        # Check if it's a legal move from the previous position
        for move in previous_board.legal_moves:
            # Create a copy of the previous board
            test_board = previous_board.copy()

            # Apply the move
            test_board.push(move)

            # Compare the resulting position with the new board
            # We only compare the piece placement part of the FEN
            if test_board.board_fen() == new_board.board_fen():
                return move

        # No matching move found
        return None

    def _on_move_made(self, _, san):
        """
        Handle a move made on the board.

        Args:
            _: The chess.Move object (unused)
            san: The move in Standard Algebraic Notation
        """
        print(f"Move made: {san}")

        # Save the previous board state for undo
        self.board_history.append(self.previous_board.copy())

        # Clear the redo stack since we're making a new move
        self.redo_stack.clear()

        # Add the move to the history
        self.add_move_to_history(san)

        # Update the FEN input field
        self.fen_input.setText(self.board_view.board.fen())

        # Update the turn radio buttons
        self._update_turn_radio_buttons()

        # Update the previous board state
        self.previous_board = self.board_view.board.copy()

        # Enable the undo button
        self.undo_button.setEnabled(True)

        # Disable the redo button since we've made a new move
        self.redo_button.setEnabled(False)

    def add_move_to_history(self, move_san):
        """
        Add a move to the history.

        Args:
            move_san: The move in Standard Algebraic Notation
        """
        # Get the current position
        position = self.board_view.board.fullmove_number

        # Add the move to the history
        if self.board_view.board.turn:  # If it's white's turn, this was a black move
            self.move_history.append(f"{position-1}. ... {move_san}")
        else:  # If it's black's turn, this was a white move
            self.move_history.append(f"{position}. {move_san}")

        # Limit the history to the last 10 moves
        if len(self.move_history) > 10:
            self.move_history = self.move_history[-10:]

        # Print move to console for debugging
        print(f"Move added to history: {move_san}")

    def _update_turn_radio_buttons(self):
        """Update the turn radio buttons based on the current board state."""
        # Get the current turn from the board
        is_white_turn = self.board_view.board.turn

        # Update the radio buttons without triggering the event handler
        self.white_turn_radio.blockSignals(True)
        self.black_turn_radio.blockSignals(True)

        if is_white_turn:
            self.white_turn_radio.setChecked(True)
            self.black_turn_radio.setChecked(False)
        else:
            self.white_turn_radio.setChecked(False)
            self.black_turn_radio.setChecked(True)

        self.white_turn_radio.blockSignals(False)
        self.black_turn_radio.blockSignals(False)

    def closeEvent(self, event):
        """Handle the window close event."""
        # Stop the analysis thread
        self._stop_analysis()

        # Stop the detection thread
        self._stop_detection()

        # Stop the engine
        if self.engine is not None:
            self.engine.stop()

        # Accept the close event
        event.accept()


def main():
    """Run the Chess Vision application."""
    app = QApplication(sys.argv)
    window = ChessVisionApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
