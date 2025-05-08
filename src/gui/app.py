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
    QPushButton, QLabel, QLineEdit, QGroupBox, QGridLayout, QFileDialog,
    QComboBox, QSpinBox
)

from src.gui.board_view import ChessBoardView
from src.chess.engine import StockfishEngine


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
        self.setMinimumSize(900, 650)  # Increased window size

        # Set up the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Create the board view
        self.board_view = ChessBoardView()

        # Initialize the Stockfish engine
        self.engine = StockfishEngine(depth=15)
        self.is_analyzing = False
        self.analysis_thread = None
        self.analysis_running = False

        # Create the control panel
        self.control_panel = self._create_control_panel()

        # Add widgets to the main layout with a 4:1 ratio (board:controls)
        self.main_layout.addWidget(self.board_view, 4)
        self.main_layout.addWidget(self.control_panel, 1)

        # Set up the board with the initial position
        self.board_view.set_board(chess.Board())

        # Set up a timer for periodic UI updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_analysis_display)
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
        position_layout.setSpacing(3)  # Reduce spacing

        # FEN input - more compact layout
        fen_layout = QHBoxLayout()
        fen_layout.setSpacing(3)
        fen_label = QLabel("FEN:")
        self.fen_input = QLineEdit()
        self.fen_input.setText(chess.STARTING_FEN)
        self.fen_input.setMaximumWidth(250)  # Limit width
        fen_layout.addWidget(fen_label)
        fen_layout.addWidget(self.fen_input)

        # Button layout - horizontal to save space
        button_layout = QHBoxLayout()
        button_layout.setSpacing(3)

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

        # Add widgets to position layout
        position_layout.addLayout(fen_layout)
        position_layout.addLayout(button_layout)

        # Analysis group
        analysis_group = QGroupBox("Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins
        analysis_layout.setSpacing(3)  # Reduce spacing

        # Analysis display
        self.analysis_label = QLabel("No analysis available")
        self.analysis_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.analysis_label.setWordWrap(True)
        self.analysis_label.setMinimumHeight(100)  # Increased height a bit

        # Analysis options
        options_layout = QHBoxLayout()
        options_layout.setSpacing(3)

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

        # Move history group
        history_group = QGroupBox("Move History")
        history_layout = QVBoxLayout(history_group)
        history_layout.setContentsMargins(5, 10, 5, 5)  # Reduce margins

        # Move history display
        self.history_label = QLabel("No moves yet")
        self.history_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.history_label.setWordWrap(True)
        self.history_label.setMinimumHeight(80)  # Reduced height

        # Add widgets to history layout
        history_layout.addWidget(self.history_label)

        # Add groups to main layout
        layout.addWidget(position_group)
        layout.addWidget(analysis_group)
        layout.addWidget(history_group)
        layout.addStretch(1)

        # Set a fixed width for the panel
        panel.setMaximumWidth(280)  # Limit the width of the control panel

        return panel

    def _on_set_position(self):
        """Handle the Set Position button click."""
        fen = self.fen_input.text()
        success = self.board_view.set_board_from_fen(fen)

        if not success:
            self.fen_input.setText(self.board_view.board.fen())

    def _on_reset(self):
        """Handle the Reset button click."""
        self.board_view.set_board(chess.Board())
        self.fen_input.setText(chess.STARTING_FEN)
        self.history_label.setText("No moves yet")

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
        while self.analysis_running:
            # Get the current board position
            board = self.board_view.board

            # Analyze the position
            try:
                self.current_analysis = self.engine.analyze(board, limit_time=0.1)
            except Exception as e:
                print(f"Analysis error: {e}")
                self.current_analysis = []

            # Sleep to avoid excessive CPU usage
            time.sleep(0.5)

    def _update_analysis_display(self):
        """Update the analysis display with the latest results."""
        if not self.is_analyzing or not self.current_analysis:
            return

        # Format the analysis results
        analysis_text = ""
        for i, analysis in enumerate(self.current_analysis):
            if "score" in analysis and "pv" in analysis:
                line_number = i + 1
                score = analysis["score"]
                moves = analysis["pv"].split()

                # Limit the number of moves shown
                if len(moves) > 5:
                    moves_text = " ".join(moves[:5]) + "..."
                else:
                    moves_text = " ".join(moves)

                analysis_text += f"Line {line_number}: {score} - {moves_text}\n"

        if analysis_text:
            self.analysis_label.setText(analysis_text)

    def _on_depth_changed(self, depth):
        """Handle changes to the analysis depth."""
        self.engine.set_depth(depth)

    def _on_lines_changed(self, lines):
        """Handle changes to the number of analysis lines."""
        self.engine.set_multipv(lines)

    def update_from_fen(self, fen):
        """Update the board from a FEN string."""
        self.fen_input.setText(fen)
        self._on_set_position()

    def add_move_to_history(self, move_san):
        """Add a move to the history display."""
        current_text = self.history_label.text()

        if current_text == "No moves yet":
            self.history_label.setText(move_san)
        else:
            self.history_label.setText(f"{current_text}, {move_san}")

    def closeEvent(self, event):
        """Handle the window close event."""
        # Stop the analysis thread
        self._stop_analysis()

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
