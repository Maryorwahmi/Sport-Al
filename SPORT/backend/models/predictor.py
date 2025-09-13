import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import joblib
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from database.models import Match, Team, MatchStatistics

logger = logging.getLogger(__name__)

class SportsPredictor:
    def __init__(self, model_path: str = "models/saved_models"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        self.is_trained = False
        
        # Create model directory if it doesn't exist
        os.makedirs(model_path, exist_ok=True)

    def prepare_training_data(self, db: Session) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from database"""
        logger.info("Preparing training data...")
        
        # Get completed matches with scores
        matches = db.query(Match).filter(
            Match.status == 'completed',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).all()
        
        if len(matches) < 50:
            raise ValueError("Not enough match data for training (minimum 50 matches required)")
        
        logger.info(f"Found {len(matches)} completed matches")
        
        # Prepare features and targets
        features_list = []
        targets = []
        
        for match in matches:
            try:
                features = self._extract_match_features(match, db)
                if features is not None:
                    features_list.append(features)
                    targets.append(match.result)
            except Exception as e:
                logger.warning(f"Error processing match {match.id}: {e}")
                continue
        
        if len(features_list) < 50:
            raise ValueError("Not enough valid features extracted for training")
        
        # Convert to DataFrame
        df_features = pd.DataFrame(features_list)
        df_targets = pd.Series(targets)
        
        # Store feature names
        self.feature_names = df_features.columns.tolist()
        
        logger.info(f"Prepared {len(df_features)} training samples with {len(self.feature_names)} features")
        return df_features, df_targets

    def _extract_match_features(self, match: Match, db: Session) -> Optional[Dict]:
        """Extract features for a single match"""
        try:
            # Get team statistics before this match
            home_stats = self._get_team_form(match.home_team_id, match.match_date, db)
            away_stats = self._get_team_form(match.away_team_id, match.match_date, db)
            
            if not home_stats or not away_stats:
                return None
            
            features = {
                # Home team features
                'home_recent_wins': home_stats['wins'],
                'home_recent_draws': home_stats['draws'],
                'home_recent_losses': home_stats['losses'],
                'home_goals_for': home_stats['goals_for'],
                'home_goals_against': home_stats['goals_against'],
                'home_form_points': home_stats['points'],
                'home_win_rate': home_stats['win_rate'],
                
                # Away team features
                'away_recent_wins': away_stats['wins'],
                'away_recent_draws': away_stats['draws'],
                'away_recent_losses': away_stats['losses'],
                'away_goals_for': away_stats['goals_for'],
                'away_goals_against': away_stats['goals_against'],
                'away_form_points': away_stats['points'],
                'away_win_rate': away_stats['win_rate'],
                
                # Relative features
                'goal_diff_home': home_stats['goals_for'] - home_stats['goals_against'],
                'goal_diff_away': away_stats['goals_for'] - away_stats['goals_against'],
                'form_difference': home_stats['points'] - away_stats['points'],
                'win_rate_difference': home_stats['win_rate'] - away_stats['win_rate'],
                
                # Match context
                'is_weekend': 1 if match.match_date and match.match_date.weekday() >= 5 else 0,
                'month': match.match_date.month if match.match_date else 1,
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features for match {match.id}: {e}")
            return None

    def _get_team_form(self, team_id: int, before_date: datetime, db: Session, lookback_matches: int = 10) -> Optional[Dict]:
        """Get team form statistics before a specific date"""
        try:
            # Get recent matches before the given date
            home_matches = db.query(Match).filter(
                Match.home_team_id == team_id,
                Match.match_date < before_date,
                Match.status == 'completed'
            ).order_by(Match.match_date.desc()).limit(lookback_matches // 2).all()
            
            away_matches = db.query(Match).filter(
                Match.away_team_id == team_id,
                Match.match_date < before_date,
                Match.status == 'completed'
            ).order_by(Match.match_date.desc()).limit(lookback_matches // 2).all()
            
            all_matches = home_matches + away_matches
            all_matches.sort(key=lambda x: x.match_date, reverse=True)
            all_matches = all_matches[:lookback_matches]
            
            if len(all_matches) < 3:  # Need at least 3 matches for meaningful stats
                return None
            
            wins = draws = losses = 0
            goals_for = goals_against = 0
            
            for match in all_matches:
                if match.home_team_id == team_id:
                    # Home match
                    goals_for += match.home_score or 0
                    goals_against += match.away_score or 0
                    
                    if match.result == 'home_win':
                        wins += 1
                    elif match.result == 'draw':
                        draws += 1
                    else:
                        losses += 1
                else:
                    # Away match
                    goals_for += match.away_score or 0
                    goals_against += match.home_score or 0
                    
                    if match.result == 'away_win':
                        wins += 1
                    elif match.result == 'draw':
                        draws += 1
                    else:
                        losses += 1
            
            total_matches = len(all_matches)
            win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
            points = wins * 3 + draws
            
            return {
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'goals_for': goals_for,
                'goals_against': goals_against,
                'win_rate': win_rate,
                'points': points
            }
            
        except Exception as e:
            logger.error(f"Error getting team form for team {team_id}: {e}")
            return None

    def train_model(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Train the prediction model"""
        logger.info("Training prediction model...")
        
        # Encode target labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Train Random Forest model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_scaled, y_encoded, cv=5)
        
        # Feature importance
        feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'top_features': top_features,
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        self.is_trained = True
        logger.info(f"Model trained successfully. Accuracy: {accuracy:.3f}, F1: {f1:.3f}")
        
        return metrics

    def predict_match(self, home_team_id: int, away_team_id: int, match_date: datetime, db: Session) -> Dict:
        """Predict the outcome of a match"""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Create a dummy match object for feature extraction
        dummy_match = Match(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            match_date=match_date
        )
        
        # Extract features
        features = self._extract_match_features(dummy_match, db)
        if not features:
            raise ValueError("Unable to extract features for prediction")
        
        # Convert to DataFrame with correct column order
        feature_df = pd.DataFrame([features])[self.feature_names]
        
        # Scale features
        X_scaled = self.scaler.transform(feature_df)
        
        # Make prediction
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        # Get class names
        classes = self.label_encoder.classes_
        
        # Create probability dictionary
        prob_dict = {classes[i]: float(probabilities[i]) for i in range(len(classes))}
        
        # Calculate confidence (highest probability)
        confidence = max(probabilities)
        
        # Get predicted result
        predicted_result = self.label_encoder.inverse_transform([prediction])[0]
        
        return {
            'predicted_result': predicted_result,
            'probabilities': prob_dict,
            'confidence': float(confidence),
            'home_win_prob': prob_dict.get('home_win', 0.0),
            'draw_prob': prob_dict.get('draw', 0.0),
            'away_win_prob': prob_dict.get('away_win', 0.0)
        }

    def save_model(self, model_name: str = "sports_predictor"):
        """Save the trained model"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        model_file = os.path.join(self.model_path, f"{model_name}.joblib")
        scaler_file = os.path.join(self.model_path, f"{model_name}_scaler.joblib")
        encoder_file = os.path.join(self.model_path, f"{model_name}_encoder.joblib")
        features_file = os.path.join(self.model_path, f"{model_name}_features.joblib")
        
        joblib.dump(self.model, model_file)
        joblib.dump(self.scaler, scaler_file)
        joblib.dump(self.label_encoder, encoder_file)
        joblib.dump(self.feature_names, features_file)
        
        logger.info(f"Model saved as {model_name}")

    def load_model(self, model_name: str = "sports_predictor"):
        """Load a trained model"""
        model_file = os.path.join(self.model_path, f"{model_name}.joblib")
        scaler_file = os.path.join(self.model_path, f"{model_name}_scaler.joblib")
        encoder_file = os.path.join(self.model_path, f"{model_name}_encoder.joblib")
        features_file = os.path.join(self.model_path, f"{model_name}_features.joblib")
        
        if not all(os.path.exists(f) for f in [model_file, scaler_file, encoder_file, features_file]):
            raise FileNotFoundError(f"Model files not found for {model_name}")
        
        self.model = joblib.load(model_file)
        self.scaler = joblib.load(scaler_file)
        self.label_encoder = joblib.load(encoder_file)
        self.feature_names = joblib.load(features_file)
        self.is_trained = True
        
        logger.info(f"Model {model_name} loaded successfully")

# Create a global instance
sports_predictor = SportsPredictor()