from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Team, Match, Prediction
from models.predictor import sports_predictor
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class PredictionRequest(BaseModel):
    home_team_id: int
    away_team_id: int
    match_date: Optional[datetime] = None

class PredictionResponse(BaseModel):
    prediction: Dict
    confidence: float
    probabilities: Dict

@router.post("/predict", response_model=PredictionResponse)
async def predict_match(request: PredictionRequest, db: Session = Depends(get_db)):
    """Predict the outcome of a match"""
    try:
        # Validate teams exist
        home_team = db.query(Team).filter(Team.id == request.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == request.away_team_id).first()
        
        if not home_team or not away_team:
            raise HTTPException(status_code=404, detail="One or both teams not found")
        
        # Use current time if no match date provided
        match_date = request.match_date or datetime.utcnow()
        
        # Load model if not already loaded
        try:
            if not sports_predictor.is_trained:
                sports_predictor.load_model()
        except FileNotFoundError:
            raise HTTPException(
                status_code=503,
                detail="Prediction model not available. Please train the model first."
            )
        
        # Make prediction
        prediction_result = sports_predictor.predict_match(
            request.home_team_id,
            request.away_team_id,
            match_date,
            db
        )
        
        # Save prediction to database
        prediction_record = Prediction(
            home_team_id=request.home_team_id,
            away_team_id=request.away_team_id,
            model_name="sports_predictor",
            predicted_result=prediction_result['predicted_result'],
            home_win_probability=prediction_result['home_win_prob'],
            away_win_probability=prediction_result['away_win_prob'],
            draw_probability=prediction_result['draw_prob'],
            confidence_score=prediction_result['confidence']
        )
        
        db.add(prediction_record)
        db.commit()
        
        return PredictionResponse(
            prediction={
                "predicted_result": prediction_result['predicted_result'],
                "home_team": home_team.name,
                "away_team": away_team.name,
                "match_date": match_date.isoformat()
            },
            confidence=prediction_result['confidence'],
            probabilities=prediction_result['probabilities']
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upcoming-matches", response_model=List[Dict])
async def get_upcoming_matches_with_predictions(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get upcoming matches with predictions if available"""
    # Get upcoming matches
    upcoming_matches = db.query(Match).filter(
        Match.status == 'scheduled',
        Match.match_date >= datetime.utcnow()
    ).order_by(Match.match_date).limit(limit).all()
    
    results = []
    for match in upcoming_matches:
        home_team = db.query(Team).filter(Team.id == match.home_team_id).first()
        away_team = db.query(Team).filter(Team.id == match.away_team_id).first()
        
        # Check if we have a prediction for this match
        prediction = db.query(Prediction).filter(
            Prediction.match_id == match.id
        ).first()
        
        match_data = {
            "id": match.id,
            "date": match.match_date.isoformat() if match.match_date else None,
            "home_team": {
                "id": home_team.id,
                "name": home_team.name
            } if home_team else None,
            "away_team": {
                "id": away_team.id,
                "name": away_team.name
            } if away_team else None,
            "league": match.league,
            "prediction": None
        }
        
        if prediction:
            match_data["prediction"] = {
                "predicted_result": prediction.predicted_result,
                "confidence": prediction.confidence_score,
                "probabilities": {
                    "home_win": prediction.home_win_probability,
                    "draw": prediction.draw_probability,
                    "away_win": prediction.away_win_probability
                }
            }
        
        results.append(match_data)
    
    return results

@router.get("/predictions/history", response_model=List[Dict])
async def get_prediction_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get historical predictions with accuracy"""
    predictions = db.query(Prediction).order_by(
        Prediction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    results = []
    for pred in predictions:
        # Get match details
        match = None
        if pred.match_id:
            match = db.query(Match).filter(Match.id == pred.match_id).first()
        
        home_team = db.query(Team).filter(Team.id == pred.home_team_id).first() if pred.home_team_id else None
        away_team = db.query(Team).filter(Team.id == pred.away_team_id).first() if pred.away_team_id else None
        
        pred_data = {
            "id": pred.id,
            "predicted_result": pred.predicted_result,
            "confidence": pred.confidence_score,
            "home_team": home_team.name if home_team else "Unknown",
            "away_team": away_team.name if away_team else "Unknown",
            "created_at": pred.created_at.isoformat(),
            "is_accurate": pred.is_accurate,
            "actual_result": None
        }
        
        if match and match.status == 'completed':
            pred_data["actual_result"] = match.result
            pred_data["actual_score"] = f"{match.home_score}-{match.away_score}"
            
            # Update accuracy if not already set
            if pred.is_accurate is None:
                pred.is_accurate = (pred.predicted_result == match.result)
                db.commit()
                pred_data["is_accurate"] = pred.is_accurate
        
        results.append(pred_data)
    
    return results

@router.get("/predictions/accuracy", response_model=Dict)
async def get_prediction_accuracy(db: Session = Depends(get_db)):
    """Get overall prediction accuracy statistics"""
    # Get all predictions with known accuracy
    accurate_predictions = db.query(Prediction).filter(
        Prediction.is_accurate == True
    ).count()
    
    inaccurate_predictions = db.query(Prediction).filter(
        Prediction.is_accurate == False
    ).count()
    
    total_evaluated = accurate_predictions + inaccurate_predictions
    accuracy = (accurate_predictions / total_evaluated * 100) if total_evaluated > 0 else 0
    
    # Get accuracy by result type
    home_win_accurate = db.query(Prediction).filter(
        Prediction.predicted_result == 'home_win',
        Prediction.is_accurate == True
    ).count()
    
    home_win_total = db.query(Prediction).filter(
        Prediction.predicted_result == 'home_win',
        Prediction.is_accurate.isnot(None)
    ).count()
    
    away_win_accurate = db.query(Prediction).filter(
        Prediction.predicted_result == 'away_win',
        Prediction.is_accurate == True
    ).count()
    
    away_win_total = db.query(Prediction).filter(
        Prediction.predicted_result == 'away_win',
        Prediction.is_accurate.isnot(None)
    ).count()
    
    draw_accurate = db.query(Prediction).filter(
        Prediction.predicted_result == 'draw',
        Prediction.is_accurate == True
    ).count()
    
    draw_total = db.query(Prediction).filter(
        Prediction.predicted_result == 'draw',
        Prediction.is_accurate.isnot(None)
    ).count()
    
    return {
        "overall_accuracy": round(accuracy, 2),
        "total_predictions": total_evaluated,
        "accurate_predictions": accurate_predictions,
        "by_result_type": {
            "home_win": {
                "accuracy": round((home_win_accurate / home_win_total * 100) if home_win_total > 0 else 0, 2),
                "total": home_win_total,
                "accurate": home_win_accurate
            },
            "away_win": {
                "accuracy": round((away_win_accurate / away_win_total * 100) if away_win_total > 0 else 0, 2),
                "total": away_win_total,
                "accurate": away_win_accurate
            },
            "draw": {
                "accuracy": round((draw_accurate / draw_total * 100) if draw_total > 0 else 0, 2),
                "total": draw_total,
                "accurate": draw_accurate
            }
        }
    }

@router.post("/batch-predict")
async def batch_predict_upcoming_matches(db: Session = Depends(get_db)):
    """Generate predictions for all upcoming matches"""
    try:
        # Load model if not already loaded
        if not sports_predictor.is_trained:
            sports_predictor.load_model()
        
        # Get upcoming matches without predictions
        upcoming_matches = db.query(Match).filter(
            Match.status == 'scheduled',
            Match.match_date >= datetime.utcnow()
        ).limit(50).all()
        
        predictions_made = 0
        
        for match in upcoming_matches:
            try:
                # Check if prediction already exists
                existing_prediction = db.query(Prediction).filter(
                    Prediction.match_id == match.id
                ).first()
                
                if existing_prediction:
                    continue
                
                # Make prediction
                prediction_result = sports_predictor.predict_match(
                    match.home_team_id,
                    match.away_team_id,
                    match.match_date,
                    db
                )
                
                # Save prediction
                prediction_record = Prediction(
                    match_id=match.id,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    model_name="sports_predictor",
                    predicted_result=prediction_result['predicted_result'],
                    home_win_probability=prediction_result['home_win_prob'],
                    away_win_probability=prediction_result['away_win_prob'],
                    draw_probability=prediction_result['draw_prob'],
                    confidence_score=prediction_result['confidence']
                )
                
                db.add(prediction_record)
                predictions_made += 1
                
            except Exception as e:
                logger.warning(f"Failed to predict match {match.id}: {e}")
                continue
        
        db.commit()
        
        return {
            "message": f"Generated {predictions_made} predictions",
            "predictions_made": predictions_made
        }
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))