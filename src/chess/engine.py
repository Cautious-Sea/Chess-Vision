"""
Chess Engine Module.

This module provides an interface to the Stockfish chess engine.
"""

import os
import chess
import chess.engine
from typing import List, Dict, Optional, Tuple, Union


class StockfishEngine:
    """
    A wrapper for the Stockfish chess engine.
    
    This class provides methods to analyze positions, get best moves,
    and manage the Stockfish process.
    """
    
    def __init__(self, depth: int = 15, threads: int = 1, hash_size: int = 128):
        """
        Initialize the Stockfish engine.
        
        Args:
            depth: The search depth for analysis
            threads: Number of CPU threads to use
            hash_size: Hash table size in MB
        """
        self.depth = depth
        self.threads = threads
        self.hash_size = hash_size
        self.engine = None
        self.engine_path = self._find_engine()
        
        # Analysis options
        self.multipv = 1  # Number of principal variations (lines) to calculate
        self.show_score = True  # Whether to show the evaluation score
        self.show_mate = True  # Whether to show mate announcements
        self.show_wdl = False  # Whether to show win/draw/loss statistics
        
    def _find_engine(self) -> str:
        """
        Find the Stockfish executable.
        
        Returns:
            The path to the Stockfish executable
        """
        # Look in the stockfish directory
        stockfish_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "stockfish")
        
        # Check for Windows executable
        stockfish_exe = os.path.join(stockfish_dir, "stockfish.exe")
        if os.path.exists(stockfish_exe):
            return stockfish_exe
        
        # Check for Linux/Mac executable
        stockfish_bin = os.path.join(stockfish_dir, "stockfish")
        if os.path.exists(stockfish_bin):
            return stockfish_bin
        
        # If not found, raise an error
        raise FileNotFoundError(
            f"Stockfish executable not found in {stockfish_dir}. "
            "Please download Stockfish from https://stockfishchess.org/download/ "
            "and place the executable in the 'stockfish' directory."
        )
    
    def start(self) -> bool:
        """
        Start the Stockfish engine.
        
        Returns:
            True if the engine started successfully, False otherwise
        """
        try:
            if self.engine is None:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
                
                # Configure the engine
                self.engine.configure({
                    "Threads": self.threads,
                    "Hash": self.hash_size
                })
            return True
        except Exception as e:
            print(f"Error starting Stockfish: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the Stockfish engine."""
        if self.engine is not None:
            self.engine.quit()
            self.engine = None
    
    def is_running(self) -> bool:
        """
        Check if the engine is running.
        
        Returns:
            True if the engine is running, False otherwise
        """
        return self.engine is not None
    
    def set_position(self, board: chess.Board) -> None:
        """
        Set the position to analyze.
        
        Args:
            board: The chess board position
        """
        if not self.is_running():
            self.start()
    
    def analyze(self, board: chess.Board, limit_time: float = 0.1) -> List[Dict]:
        """
        Analyze the current position.
        
        Args:
            board: The chess board position
            limit_time: Time limit for analysis in seconds
            
        Returns:
            A list of analysis results, one for each principal variation
        """
        if not self.is_running():
            self.start()
        
        # Create the limit object
        limit = chess.engine.Limit(time=limit_time, depth=self.depth)
        
        # Analyze the position
        result = self.engine.analyse(
            board, 
            limit, 
            multipv=self.multipv
        )
        
        # If result is not a list (single PV), convert it to a list
        if not isinstance(result, list):
            result = [result]
        
        # Process the results
        analysis_results = []
        for i, info in enumerate(result):
            analysis = {}
            
            # Get the score
            if "score" in info:
                score = info["score"]
                if self.show_score:
                    # Convert the score to a string representation
                    if score.is_mate():
                        analysis["score"] = f"Mate in {score.mate()}"
                    else:
                        # Convert centipawns to pawns
                        cp_score = score.white().score(mate_score=10000) / 100.0
                        analysis["score"] = f"{cp_score:+.2f}"
                
                # Add raw score for sorting/comparison
                analysis["raw_score"] = score.white().score(mate_score=10000)
            
            # Get the principal variation (PV)
            if "pv" in info:
                pv = info["pv"]
                analysis["moves"] = []
                
                # Convert the moves to SAN notation
                temp_board = board.copy()
                for move in pv:
                    san = temp_board.san(move)
                    analysis["moves"].append(san)
                    temp_board.push(move)
                
                # Create a string representation of the PV
                analysis["pv"] = " ".join(analysis["moves"])
            
            # Get the depth
            if "depth" in info:
                analysis["depth"] = info["depth"]
            
            analysis_results.append(analysis)
        
        return analysis_results
    
    def get_best_move(self, board: chess.Board, limit_time: float = 0.1) -> Tuple[chess.Move, str]:
        """
        Get the best move for the current position.
        
        Args:
            board: The chess board position
            limit_time: Time limit for analysis in seconds
            
        Returns:
            A tuple containing the best move and its SAN notation
        """
        if not self.is_running():
            self.start()
        
        # Create the limit object
        limit = chess.engine.Limit(time=limit_time, depth=self.depth)
        
        # Get the best move
        result = self.engine.play(board, limit)
        
        # Convert to SAN notation
        san = board.san(result.move)
        
        return result.move, san
    
    def set_depth(self, depth: int) -> None:
        """
        Set the search depth.
        
        Args:
            depth: The search depth
        """
        self.depth = depth
    
    def set_threads(self, threads: int) -> None:
        """
        Set the number of CPU threads.
        
        Args:
            threads: Number of CPU threads to use
        """
        self.threads = threads
        if self.is_running():
            self.engine.configure({"Threads": threads})
    
    def set_hash_size(self, hash_size: int) -> None:
        """
        Set the hash table size.
        
        Args:
            hash_size: Hash table size in MB
        """
        self.hash_size = hash_size
        if self.is_running():
            self.engine.configure({"Hash": hash_size})
    
    def set_multipv(self, multipv: int) -> None:
        """
        Set the number of principal variations to calculate.
        
        Args:
            multipv: Number of principal variations
        """
        self.multipv = multipv
    
    def __del__(self):
        """Clean up resources when the object is destroyed."""
        self.stop()
