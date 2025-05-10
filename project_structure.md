# Chess Vision Project Structure

```
Chess-Vision/
├── README.md                  # Project overview and documentation
├── requirements.txt           # Python dependencies
├── setup.py                   # Package installation script
├── .gitignore                 # Git ignore file
├── main.py                    # Main application entry point
│
├── stockfish/                 # Directory for Stockfish engine
│   └── README.md              # Instructions for adding Stockfish executable
│
├── models/                    # Directory for YOLO model files
│   └── README.md              # Instructions for adding trained model
│
├── data/                      # Data directory
│   ├── config/                # Configuration files
│   │   └── settings.json      # Application settings
│   └── samples/               # Sample images for testing
│
├── src/                       # Source code
│   ├── __init__.py            # Package initialization
│   │
│   ├── screen/                # Screen handling module
│   │   ├── __init__.py        # Package initialization
│   │   ├── selector.py        # Screen region selection
│   │   └── capture.py         # Screen capture functionality
│   │
│   ├── detection/             # Chess piece detection module
│   │   ├── __init__.py        # Package initialization
│   │   ├── model.py           # YOLO model wrapper
│   │   ├── detector.py        # Chess piece detection logic
│   │   └── orientation.py     # Board orientation detection
│   │
│   ├── chess/                 # Chess logic module
│   │   ├── __init__.py        # Package initialization
│   │   ├── board.py           # Chess board representation
│   │   ├── fen.py             # FEN generation and parsing
│   │   ├── move_detector.py   # Move detection by comparing board states
│   │   ├── history.py         # Move history tracking
│   │   └── engine.py          # Stockfish integration with customizable analysis
│   │
│   ├── gui/                   # GUI module
│   │   ├── __init__.py        # Package initialization
│   │   ├── app.py             # Main application window
│   │   ├── board_view.py      # Chess board visualization
│   │   ├── analysis_view.py   # Analysis panel
│   │   ├── analysis_config.py # Analysis configuration options
│   │   ├── history_view.py    # Move history display
│   │   └── settings_view.py   # Settings panel
│   │
│   └── utils/                 # Utility functions
│       ├── __init__.py        # Package initialization
│       ├── config.py          # Configuration handling
│       ├── logger.py          # Logging functionality
│       └── helpers.py         # Helper functions
│
├── tests/                     # Test directory
│   ├── __init__.py            # Package initialization
│   ├── test_screen.py         # Tests for screen module
│   ├── test_detection.py      # Tests for detection module
│   ├── test_chess.py          # Tests for chess module
│   ├── test_gui.py            # Tests for GUI module
│   └── test_utils.py          # Tests for utility functions
│
└── docs/                      # Documentation
    ├── images/                # Images for documentation
    ├── usage.md               # Usage guide
    ├── development.md         # Development guide
    └── api.md                 # API documentation
```

## Module Descriptions

### Main Application (`main.py`)
The entry point for the application that initializes and coordinates all modules.

### Screen Module (`src/screen/`)
- `selector.py`: Implements the UI for selecting a 395x395 region of the screen
- `capture.py`: Handles capturing the selected region at regular intervals

### Detection Module (`src/detection/`)
- `model.py`: Wrapper for the Ultralytics YOLO model
- `detector.py`: Processes captured images to detect chess pieces
- `orientation.py`: Determines whether white or black pieces are at the bottom of the board

### Chess Module (`src/chess/`)
- `board.py`: Represents the chess board and its state
- `fen.py`: Converts detected pieces to FEN notation and vice versa
- `move_detector.py`: Detects chess moves by comparing consecutive board states
- `history.py`: Tracks and manages the history of moves in the game
- `engine.py`: Interfaces with Stockfish for position analysis with customizable options

### GUI Module (`src/gui/`)
- `app.py`: Main application window and coordination
- `board_view.py`: Visual representation of the chess board
- `analysis_view.py`: Display for Stockfish analysis
- `analysis_config.py`: Configuration interface for customizing analysis options
- `history_view.py`: Interface for displaying and navigating move history
- `settings_view.py`: UI for application settings

### Utilities (`src/utils/`)
- `config.py`: Handles loading and saving configuration
- `logger.py`: Logging functionality
- `helpers.py`: Miscellaneous helper functions

## Configuration

The application will use a JSON configuration file (`data/config/settings.json`) to store:
- Screen region coordinates
- Stockfish path
- Detection confidence threshold
- Analysis preferences (depth, number of lines, time constraints)
- Move history settings (auto-save, export format)
- UI preferences
- Other settings

## Testing

Each module will have corresponding test files in the `tests/` directory to ensure functionality works as expected.

## Move Detection Approach

The application uses an efficient approach for detecting chess moves:

1. **Initial Position Detection**:
   - Generate a complete FEN for the starting position
   - Initialize the chess board in the GUI with this position

2. **Change Detection**:
   - Monitor the board for visual changes (pieces moving)
   - When a change is detected, analyze what pieces moved from where to where

3. **Move Inference**:
   - Use chess logic to determine the legal move that explains the observed changes
   - Handle special cases like castling, en passant, and promotion

4. **Move Application**:
   - Apply the inferred move to the internal chess board representation
   - Update the GUI to reflect the new position
   - Add the move to the history

5. **Validation**:
   - Periodically perform a full board scan to verify the accumulated state matches reality
   - If discrepancies are found, perform a correction

This approach is more efficient than regenerating the entire FEN for each frame, as it only processes the changes between consecutive positions.
