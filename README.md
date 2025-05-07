# Chess Vision

A Python application that uses computer vision and AI to analyze chess games in real-time from your screen.

## Overview

Chess Vision monitors a selected region of your screen where a chess game is being played, detects the pieces using a YOLO model, generates a FEN (Forsyth-Edwards Notation) representation of the board, and provides real-time analysis using Stockfish.

![Chess Vision Demo](docs/demo_placeholder.png)

## Features

- **Screen Region Selection**: Manually select a 380x380 pixel region of your screen where the chess board is displayed
- **Real-time Chess Piece Detection**: Uses a custom-trained YOLOv11 model to detect all chess pieces
- **Board Orientation Detection**: Automatically determines whether white or black pieces are at the bottom of the board
- **FEN Generation**: Converts the detected board state into standard FEN notation
- **Interactive Chess GUI**: Displays the detected position in a chess board interface
- **Stockfish Analysis**: Provides real-time engine analysis and best move suggestions
- **Move Detection**: Automatically updates when moves are made on the monitored board

## Requirements

### Hardware
- Intel i5 13th gen or equivalent processor (recommended)
- NVIDIA GPU (for optimal performance)
- Display resolution sufficient for chess application + Chess Vision interface

### Software
- Python 3.12
- Anaconda environment
- Stockfish chess engine

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/Chess-Vision.git
   cd Chess-Vision
   ```

2. Create and activate the Anaconda environment:
   ```
   conda create -n Chess-Vision python=3.12
   conda activate Chess-Vision
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Download Stockfish:
   - Download the latest version of Stockfish from the [official website](https://stockfishchess.org/download/)
   - Place the `stockfish.exe` (Windows) or `stockfish` (Linux/Mac) executable in the `stockfish/` directory

## Usage

1. Activate the Anaconda environment:
   ```
   conda activate Chess-Vision
   ```

2. Run the main application:
   ```
   python main.py
   ```

3. Use the selection tool to define the 380x380 chess board region on your screen

4. The application will begin monitoring the selected region and display the detected position in the chess GUI

5. Stockfish analysis will automatically update as the position changes

## Project Structure

```
Chess-Vision/
├── main.py                  # Main application entry point
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── stockfish/               # Directory for Stockfish engine
├── models/                  # Directory for YOLO model files
│   └── chess_model.pt       # Trained YOLOv11 model
├── src/                     # Source code
│   ├── screen_selector.py   # Screen region selection module
│   ├── chess_detector.py    # Chess piece detection using YOLO
│   ├── fen_generator.py     # FEN notation generator
│   ├── chess_gui.py         # Chess board GUI
│   └── stockfish_engine.py  # Stockfish integration
└── docs/                    # Documentation and images
```

## Development

### Modules

1. **Screen Selection Module**
   - Allows users to select a 380x380 region of the screen
   - Saves coordinates for continuous monitoring

2. **Chess Detection Module**
   - Captures the selected screen region
   - Uses Ultralytics YOLO to detect chess pieces
   - Maps detected pieces to their positions on the chess board
   - Determines board orientation (white or black at bottom)

3. **FEN Generator Module**
   - Converts the detected pieces and positions to FEN notation

4. **Chess GUI Module**
   - Displays the chess board using python-chess
   - Shows Stockfish analysis

5. **Main Application**
   - Coordinates all modules
   - Handles user settings and preferences

## Model Information

The application uses a custom-trained YOLOv11 model to detect chess pieces. The model recognizes the following classes:
- `wb`: White Bishop
- `wk`: White King
- `wn`: White Knight
- `wp`: White Pawn
- `wq`: White Queen
- `wr`: White Rook
- `bb`: Black Bishop
- `bk`: Black King
- `bn`: Black Knight
- `bp`: Black Pawn
- `bq`: Black Queen
- `br`: Black Rook

## License

[MIT License](LICENSE)

## Acknowledgments

- [Ultralytics](https://github.com/ultralytics/ultralytics) for the YOLO implementation
- [python-chess](https://github.com/niklasf/python-chess) for chess logic and visualization
- [Stockfish](https://stockfishchess.org/) for chess analysis
