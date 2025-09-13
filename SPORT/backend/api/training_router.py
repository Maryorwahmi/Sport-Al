from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.database import get_db
from models.predictor import sports_predictor
from typing import Dict
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/train", response_model=Dict)
async def train_model(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Train the prediction model"""
    
    def train_model_task():
        try:
            logger.info("Starting model training...")
            
            # Prepare training data
            X, y = sports_predictor.prepare_training_data(db)
            
            # Train model
            metrics = sports_predictor.train_model(X, y)
            
            # Save model
            sports_predictor.save_model()
            
            logger.info(f"Model training completed. Metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
    
    background_tasks.add_task(train_model_task)
    
    return {"message": "Model training started in background"}

@router.get("/status", response_model=Dict)
async def get_training_status(db: Session = Depends(get_db)):
    """Get training status and model information"""
    try:
        # Try to load model to check if it exists
        if not sports_predictor.is_trained:
            try:
                sports_predictor.load_model()
            except FileNotFoundError:
                return {
                    "model_trained": False,
                    "message": "No trained model available"
                }
        
        # Count available training data
        from database.models import Match
        completed_matches = db.query(Match).filter(
            Match.status == 'completed',
            Match.home_score.isnot(None),
            Match.away_score.isnot(None)
        ).count()
        
        return {
            "model_trained": True,
            "available_training_data": completed_matches,
            "feature_count": len(sports_predictor.feature_names) if sports_predictor.feature_names else 0,
            "model_type": "RandomForestClassifier"
        }
        
    except Exception as e:
        logger.error(f"Error checking training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrain", response_model=Dict)
async def retrain_model(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Retrain the model with updated data"""
    
    def retrain_task():
        try:
            logger.info("Starting model retraining...")
            
            # Prepare updated training data
            X, y = sports_predictor.prepare_training_data(db)
            
            # Retrain model
            metrics = sports_predictor.train_model(X, y)
            
            # Save updated model
            sports_predictor.save_model()
            
            logger.info(f"Model retraining completed. Metrics: {metrics}")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}")
    
    background_tasks.add_task(retrain_task)
    
    return {"message": "Model retraining started in background"}

@router.get("/metrics", response_model=Dict)
async def get_model_metrics():
    """Get model performance metrics"""
    if not sports_predictor.is_trained:
        try:
            sports_predictor.load_model()
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail="No trained model available"
            )
    
    # For now, return basic model info
    # In a production system, you'd store and retrieve detailed metrics
    return {
        "model_type": "RandomForestClassifier",
        "feature_count": len(sports_predictor.feature_names),
        "features": sports_predictor.feature_names,
        "target_classes": sports_predictor.label_encoder.classes_.tolist() if hasattr(sports_predictor.label_encoder, 'classes_') else []
    }

@router.post("/evaluate", response_model=Dict)
async def evaluate_model(db: Session = Depends(get_db)):
    """Evaluate model performance on recent predictions"""
    try:
        from database.models import Prediction
        
        # Get recent predictions with known outcomes
        recent_predictions = db.query(Prediction).filter(
            Prediction.is_accurate.isnot(None)
        ).limit(100).all()
        
        if len(recent_predictions) < 10:
            raise HTTPException(
                status_code=400,
                detail="Not enough evaluated predictions for meaningful analysis"
            )
        
        # Calculate metrics
        total = len(recent_predictions)
        accurate = sum(1 for p in recent_predictions if p.is_accurate)
        accuracy = (accurate / total) * 100
        
        # Calculate confidence distribution
        high_confidence = sum(1 for p in recent_predictions if p.confidence_score > 0.7)
        medium_confidence = sum(1 for p in recent_predictions if 0.5 <= p.confidence_score <= 0.7)
        low_confidence = sum(1 for p in recent_predictions if p.confidence_score < 0.5)
        
        # Accuracy by confidence level
        high_conf_accurate = sum(1 for p in recent_predictions if p.confidence_score > 0.7 and p.is_accurate)
        high_conf_accuracy = (high_conf_accurate / high_confidence * 100) if high_confidence > 0 else 0
        
        return {
            "total_predictions": total,
            "overall_accuracy": round(accuracy, 2),
            "confidence_distribution": {
                "high_confidence": high_confidence,
                "medium_confidence": medium_confidence,
                "low_confidence": low_confidence
            },
            "high_confidence_accuracy": round(high_conf_accuracy, 2),
            "recommendation": "Good performance" if accuracy > 60 else "Consider retraining"
        }
        
    except Exception as e:
        logger.error(f"Model evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))