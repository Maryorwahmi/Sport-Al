"""
Candle Pattern Recognition Engine with Machine Learning
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import joblib
from pathlib import Path
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import json


class PatternRecognitionEngine:
    """
    ML-based candle pattern recognition and prediction
    """
    
    def __init__(self, model_path: str = "models/pattern_recognition"):
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        
        self.clusterer = None
        self.scaler = StandardScaler()
        self.pattern_outcomes = {}  # Maps cluster to outcome distribution
        self.is_trained = False
        
    def train(self, windows: np.ndarray, outcomes: np.ndarray, 
             n_clusters: int = 50, method: str = 'kmeans'):
        """
        Train pattern recognition model
        
        Args:
            windows: 3D array of shape (n_samples, window_size, n_features)
            outcomes: Array of next-candle outcomes (1 for up, -1 for down, 0 for neutral)
            n_clusters: Number of pattern clusters
            method: Clustering method ('kmeans' or 'dbscan')
        """
        print(f"Training pattern recognition with {len(windows)} samples...")
        
        # Flatten windows for clustering
        n_samples = windows.shape[0]
        flattened = windows.reshape(n_samples, -1)
        
        # Normalize
        flattened_scaled = self.scaler.fit_transform(flattened)
        
        # Cluster patterns
        if method == 'kmeans':
            self.clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        else:
            self.clusterer = DBSCAN(eps=0.5, min_samples=5)
        
        cluster_labels = self.clusterer.fit_predict(flattened_scaled)
        
        # Calculate outcome probabilities for each cluster
        self.pattern_outcomes = {}
        unique_clusters = np.unique(cluster_labels)
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Skip noise in DBSCAN
                continue
            
            mask = cluster_labels == cluster_id
            cluster_outcomes = outcomes[mask]
            
            n_total = len(cluster_outcomes)
            n_up = np.sum(cluster_outcomes == 1)
            n_down = np.sum(cluster_outcomes == -1)
            n_neutral = np.sum(cluster_outcomes == 0)
            
            self.pattern_outcomes[int(cluster_id)] = {
                'count': n_total,
                'prob_up': n_up / n_total if n_total > 0 else 0.33,
                'prob_down': n_down / n_total if n_total > 0 else 0.33,
                'prob_neutral': n_neutral / n_total if n_total > 0 else 0.33,
                'expected_return': (n_up - n_down) / n_total if n_total > 0 else 0
            }
        
        self.is_trained = True
        print(f"Training complete. Found {len(self.pattern_outcomes)} patterns.")
        
        return {
            'n_clusters': len(self.pattern_outcomes),
            'n_samples': n_samples,
            'patterns': self.pattern_outcomes
        }
    
    def predict(self, window: np.ndarray) -> Dict[str, float]:
        """
        Predict next-candle outcome based on pattern matching
        
        Args:
            window: Single pattern window of shape (window_size, n_features)
            
        Returns:
            Dictionary with probabilities and prediction
        """
        if not self.is_trained:
            return {
                'prob_up': 0.33,
                'prob_down': 0.33,
                'prob_neutral': 0.33,
                'prediction': 0,
                'confidence': 0.0,
                'pattern_id': -1
            }
        
        # Flatten and normalize
        flattened = window.reshape(1, -1)
        flattened_scaled = self.scaler.transform(flattened)
        
        # Find matching cluster
        cluster_id = self.clusterer.predict(flattened_scaled)[0]
        
        # Get outcome probabilities
        if cluster_id in self.pattern_outcomes:
            pattern = self.pattern_outcomes[cluster_id]
            prob_up = pattern['prob_up']
            prob_down = pattern['prob_down']
            prob_neutral = pattern['prob_neutral']
        else:
            # Unknown pattern, use neutral priors
            prob_up = 0.33
            prob_down = 0.33
            prob_neutral = 0.33
        
        # Determine prediction
        probs = [prob_down, prob_neutral, prob_up]
        prediction = np.argmax(probs) - 1  # -1, 0, or 1
        confidence = max(probs)
        
        return {
            'prob_up': prob_up,
            'prob_down': prob_down,
            'prob_neutral': prob_neutral,
            'prediction': int(prediction),
            'confidence': float(confidence),
            'pattern_id': int(cluster_id),
            'pattern_count': pattern.get('count', 0) if cluster_id in self.pattern_outcomes else 0
        }
    
    def save_model(self, name: str = "pattern_model"):
        """Save trained model"""
        if not self.is_trained:
            print("Model not trained, nothing to save")
            return
        
        model_data = {
            'clusterer': self.clusterer,
            'scaler': self.scaler,
            'pattern_outcomes': self.pattern_outcomes,
            'timestamp': datetime.now().isoformat()
        }
        
        model_file = self.model_path / f"{name}.pkl"
        joblib.dump(model_data, model_file)
        
        # Save outcomes as JSON for readability
        json_file = self.model_path / f"{name}_patterns.json"
        with open(json_file, 'w') as f:
            json.dump(self.pattern_outcomes, f, indent=2)
        
        print(f"Model saved to {model_file}")
    
    def load_model(self, name: str = "pattern_model"):
        """Load trained model"""
        model_file = self.model_path / f"{name}.pkl"
        
        if not model_file.exists():
            print(f"Model file not found: {model_file}")
            return False
        
        model_data = joblib.load(model_file)
        self.clusterer = model_data['clusterer']
        self.scaler = model_data['scaler']
        self.pattern_outcomes = model_data['pattern_outcomes']
        self.is_trained = True
        
        print(f"Model loaded from {model_file}")
        print(f"Patterns: {len(self.pattern_outcomes)}")
        return True
    
    def get_pattern_statistics(self) -> Dict:
        """Get statistics about learned patterns"""
        if not self.is_trained:
            return {}
        
        stats = {
            'n_patterns': len(self.pattern_outcomes),
            'total_samples': sum(p['count'] for p in self.pattern_outcomes.values()),
        }
        
        # Find best patterns
        patterns_by_return = sorted(
            [(pid, p['expected_return']) for pid, p in self.pattern_outcomes.items()],
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        stats['top_bullish'] = [
            {'pattern_id': pid, 'return': ret, **self.pattern_outcomes[pid]}
            for pid, ret in patterns_by_return if ret > 0
        ][:5]
        
        stats['top_bearish'] = [
            {'pattern_id': pid, 'return': ret, **self.pattern_outcomes[pid]}
            for pid, ret in patterns_by_return if ret < 0
        ][-5:]
        
        return stats


class DeepPatternRecognizer:
    """
    Deep learning-based pattern recognition (LSTM/CNN)
    Placeholder for future implementation
    """
    
    def __init__(self, model_type: str = 'lstm'):
        self.model_type = model_type
        self.model = None
        self.is_trained = False
    
    def build_model(self, input_shape: Tuple, output_shape: int = 3):
        """Build neural network model"""
        try:
            import tensorflow as tf
            from tensorflow import keras
            from tensorflow.keras import layers
            
            if self.model_type == 'lstm':
                model = keras.Sequential([
                    layers.LSTM(128, return_sequences=True, input_shape=input_shape),
                    layers.Dropout(0.2),
                    layers.LSTM(64, return_sequences=False),
                    layers.Dropout(0.2),
                    layers.Dense(32, activation='relu'),
                    layers.Dense(output_shape, activation='softmax')
                ])
            elif self.model_type == 'cnn':
                model = keras.Sequential([
                    layers.Conv1D(64, 3, activation='relu', input_shape=input_shape),
                    layers.MaxPooling1D(2),
                    layers.Conv1D(128, 3, activation='relu'),
                    layers.MaxPooling1D(2),
                    layers.Flatten(),
                    layers.Dense(64, activation='relu'),
                    layers.Dropout(0.2),
                    layers.Dense(output_shape, activation='softmax')
                ])
            
            model.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            self.model = model
            return True
            
        except ImportError:
            print("TensorFlow not installed. Deep learning models unavailable.")
            return False
    
    def train(self, X_train, y_train, epochs: int = 50, batch_size: int = 32):
        """Train deep learning model"""
        if self.model is None:
            print("Model not built")
            return None
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        
        self.is_trained = True
        return history
    
    def predict(self, window: np.ndarray) -> Dict[str, float]:
        """Predict with deep learning model"""
        if not self.is_trained:
            return {
                'prob_down': 0.33,
                'prob_neutral': 0.33,
                'prob_up': 0.33,
                'prediction': 0,
                'confidence': 0.0
            }
        
        probs = self.model.predict(window.reshape(1, *window.shape), verbose=0)[0]
        prediction = np.argmax(probs) - 1
        
        return {
            'prob_down': float(probs[0]),
            'prob_neutral': float(probs[1]),
            'prob_up': float(probs[2]),
            'prediction': int(prediction),
            'confidence': float(max(probs))
        }
