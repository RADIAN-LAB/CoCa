"""Vehicle trajectory prediction integration for VANET cache scheduling.

This module integrates XGBoost-based trajectory prediction with the cache-enabled scheduler
to enable proactive cache placement and dynamic RSU assignment based on predicted vehicle paths.
"""
import pickle
import pandas as pd
from typing import Tuple, List, Optional
from pathlib import Path

# Try to import XGBoost, fallback to mock if not available
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not available. Using mock trajectory prediction.")

class TrajectoryPredictor:
    """Vehicle trajectory prediction using pre-trained XGBoost model."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize trajectory predictor.
        
        Args:
            model_path: Path to pre-trained XGBoost model pickle file
        """
        self.model = None
        self.model_loaded = False
        
        if model_path is None:
            # Resolve relative to this repository. The previous default was an
            # absolute path into a sibling checkout that does not exist here, so
            # the predictor silently fell back to the mock on every run even
            # though enable_trajectory_prediction was True, xgboost was
            # installed, and the model file was present in-tree.
            model_path = str(
                Path(__file__).resolve().parent
                / "models"
                / "files"
                / "PredictTrajectory_model.pkl"
            )
        
        self.load_model(model_path)
    
    def load_model(self, model_path: str) -> bool:
        """Load pre-trained XGBoost model from pickle file.
        
        Args:
            model_path: Path to model pickle file
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            model_file = Path(model_path)
            if model_file.exists() and XGBOOST_AVAILABLE:
                with open(model_file, 'rb') as file:
                    self.model = pickle.load(file)
                self.model_loaded = True
                print(f"Trajectory prediction model loaded from {model_path}")
                return True
            else:
                print(f"Model file not found or XGBoost not available: {model_path}")
                return False
        except Exception as e:
            print(f"Error loading trajectory model: {e}")
            return False
    
    def predict_destination_rsu(self, x: float, y: float, source_rsu: int, 
                               current_time: float, speed: float, 
                               completion_time: float) -> int:
        """Predict destination RSU where vehicle will be at task completion time.
        
        Args:
            x: Current vehicle position X
            y: Current vehicle position Y
            source_rsu: Current RSU ID (1-based)
            current_time: Current timestamp
            speed: Vehicle speed
            completion_time: Predicted task completion time
            
        Returns:
            Predicted destination RSU ID (1-based)
        """
        if not self.model_loaded or not XGBOOST_AVAILABLE:
            # Fallback: use mobility-aware heuristic
            return self._heuristic_prediction(source_rsu, speed, completion_time - current_time)
        
        try:
            # Prepare input data for XGBoost model
            data = [[current_time, speed, source_rsu, x, y, completion_time]]
            df = pd.DataFrame(data, columns=[
                'Timestamp', 'Speed', 'ConnectedRSU', 'PositionX', 'PositionY', 'Timestamp2'
            ])
            
            # Predict destination RSU
            prediction = self.model.predict(df)
            predicted_rsu = int(round(prediction[0]))
            
            # Ensure valid RSU ID (1-5 range)
            predicted_rsu = max(1, min(5, predicted_rsu))
            
            return predicted_rsu
            
        except Exception as e:
            print(f"Error in trajectory prediction: {e}")
            # Fallback to heuristic
            return self._heuristic_prediction(source_rsu, speed, completion_time - current_time)
    
    def _heuristic_prediction(self, source_rsu: int, speed: float, time_duration: float) -> int:
        """Heuristic-based RSU prediction when ML model not available.
        
        Args:
            source_rsu: Current RSU ID
            speed: Vehicle speed
            time_duration: Time until task completion
            
        Returns:
            Predicted RSU ID based on simple mobility model
        """
        # Simple heuristic: vehicles may move to adjacent RSUs based on speed and time
        if speed > 50 and time_duration > 10:  # High speed, long duration
            # Likely to move to adjacent RSU
            direction = 1 if source_rsu < 3 else -1  # Move toward center
            predicted_rsu = source_rsu + direction
        elif speed > 30 and time_duration > 5:  # Medium speed, medium duration
            # May stay or move slightly
            predicted_rsu = source_rsu if time_duration < 8 else source_rsu + 1
        else:
            # Low speed or short duration - likely to stay
            predicted_rsu = source_rsu
        
        # Ensure valid RSU range (1-5)
        return max(1, min(5, predicted_rsu))
    
    def predict_rsu_path(self, x: float, y: float, source_rsu: int, 
                        current_time: float, speed: float, 
                        time_horizon: float, time_steps: int = 5) -> List[int]:
        """Predict sequence of RSUs vehicle will visit over time horizon.
        
        Args:
            x: Current vehicle position X
            y: Current vehicle position Y
            source_rsu: Current RSU ID
            current_time: Current timestamp
            speed: Vehicle speed
            time_horizon: Total prediction time horizon
            time_steps: Number of prediction steps
            
        Returns:
            List of predicted RSU IDs over time horizon
        """
        rsu_path = [source_rsu]
        step_duration = time_horizon / time_steps
        
        current_rsu = source_rsu
        for step in range(1, time_steps + 1):
            step_time = current_time + (step * step_duration)
            predicted_rsu = self.predict_destination_rsu(
                x, y, current_rsu, current_time, speed, step_time
            )
            rsu_path.append(predicted_rsu)
            current_rsu = predicted_rsu  # Update for next prediction
        
        return rsu_path

# Global trajectory predictor instance
_trajectory_predictor = None

def get_trajectory_predictor() -> TrajectoryPredictor:
    """Get global trajectory predictor instance."""
    global _trajectory_predictor
    if _trajectory_predictor is None:
        _trajectory_predictor = TrajectoryPredictor()
    return _trajectory_predictor

def predict_vehicle_destination_rsu(x: float, y: float, source_rsu: int, 
                                   current_time: float, speed: float, 
                                   completion_time: float) -> int:
    """Convenience function for trajectory prediction.
    
    Args:
        x: Vehicle position X
        y: Vehicle position Y
        source_rsu: Current RSU ID
        current_time: Current timestamp
        speed: Vehicle speed
        completion_time: Task completion time
        
    Returns:
        Predicted destination RSU ID
    """
    predictor = get_trajectory_predictor()
    return predictor.predict_destination_rsu(
        x, y, source_rsu, current_time, speed, completion_time
    )

__all__ = [
    "TrajectoryPredictor",
    "get_trajectory_predictor", 
    "predict_vehicle_destination_rsu"
]
