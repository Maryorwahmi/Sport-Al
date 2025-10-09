"""
Multi-timeframe confluence scorer and signal generator
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class TradingSignal:
    """Trading signal with entry/exit levels"""
    symbol: str
    timeframe: str
    timestamp: datetime
    action: str  # 'BUY', 'SELL', 'WAIT', 'IGNORE'
    confidence: float
    confluence_score: float
    
    # Entry/Exit levels
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    
    # Supporting factors
    pattern_prediction: Dict
    smc_factors: Dict
    structure_bias: str
    
    # Additional info
    notes: List[str]
    
    def to_dict(self):
        return asdict(self)


class ConfluenceScorer:
    """Multi-timeframe confluence scoring"""
    
    def __init__(self, settings=None):
        self.settings = settings or {}
        
        # Weights from settings
        self.weights = {
            'h4_bias': self.settings.get('h4_bias_weight', 0.20),
            'h1_structure': self.settings.get('h1_structure_weight', 0.20),
            'm15_poi': self.settings.get('m15_poi_weight', 0.20),
            'ob_proximity': self.settings.get('ob_proximity_weight', 0.15),
            'fvg_presence': self.settings.get('fvg_presence_weight', 0.08),
            'liquidity_sweep': self.settings.get('liquidity_sweep_weight', 0.07),
            'momentum': self.settings.get('momentum_weight', 0.05),
            'session': self.settings.get('session_weight', 0.05),
        }
        
        # Thresholds
        self.execute_threshold = self.settings.get('execute_threshold', 0.75)
        self.watch_threshold = self.settings.get('watch_threshold', 0.50)
    
    def calculate_confluence(self, mtf_data: Dict, current_price: float) -> Dict[str, float]:
        """
        Calculate confluence score from multi-timeframe data
        
        Args:
            mtf_data: Dict with H4, H1, M15 analysis data
            current_price: Current market price
            
        Returns:
            Dictionary with scores for each factor
        """
        scores = {}
        
        # H4 bias
        scores['h4_bias'] = self._score_htf_bias(mtf_data.get('H4', {}))
        
        # H1 structure
        scores['h1_structure'] = self._score_structure(mtf_data.get('H1', {}))
        
        # M15 POI proximity
        scores['m15_poi'] = self._score_poi_proximity(
            mtf_data.get('M15', {}), current_price
        )
        
        # Order Block proximity
        scores['ob_proximity'] = self._score_ob_proximity(
            mtf_data.get('M15', {}), current_price
        )
        
        # FVG presence
        scores['fvg_presence'] = self._score_fvg_presence(mtf_data.get('M15', {}))
        
        # Liquidity sweep
        scores['liquidity_sweep'] = self._score_liquidity_sweep(mtf_data.get('M15', {}))
        
        # Momentum
        scores['momentum'] = self._score_momentum(mtf_data.get('M15', {}))
        
        # Session timing
        scores['session'] = self._score_session()
        
        return scores
    
    def _score_htf_bias(self, h4_data: Dict) -> float:
        """Score H4 timeframe bias"""
        if not h4_data:
            return 0.5
        
        structure = h4_data.get('structure', {})
        bos_list = structure.get('bos', [])
        
        if not bos_list:
            return 0.5
        
        # Get most recent BOS
        recent_bos = bos_list[-1] if bos_list else None
        
        if recent_bos:
            if 'bullish' in recent_bos['type']:
                return 0.8  # Strong bullish bias
            elif 'bearish' in recent_bos['type']:
                return 0.2  # Strong bearish bias
        
        return 0.5  # Neutral
    
    def _score_structure(self, h1_data: Dict) -> float:
        """Score H1 structure alignment"""
        if not h1_data:
            return 0.5
        
        structure = h1_data.get('structure', {})
        bos_list = structure.get('bos', [])
        choch_list = structure.get('choch', [])
        
        # More BOS = stronger trend
        bos_score = min(len(bos_list) / 5.0, 1.0)
        
        # Recent CHOCH reduces score
        choch_penalty = len(choch_list) * 0.1
        
        return max(0.1, min(bos_score - choch_penalty, 1.0))
    
    def _score_poi_proximity(self, m15_data: Dict, current_price: float) -> float:
        """Score proximity to Point of Interest"""
        if not m15_data:
            return 0.3
        
        smc = m15_data.get('smc', {})
        obs = smc.get('order_blocks', {}).get('active', [])
        
        if not obs:
            return 0.3
        
        # Find closest OB
        min_distance = float('inf')
        for ob in obs:
            ob_mid = (ob.price_high + ob.price_low) / 2
            distance = abs(current_price - ob_mid) / current_price
            min_distance = min(min_distance, distance)
        
        # Convert distance to score (closer = higher score)
        if min_distance < 0.001:  # Very close (< 0.1%)
            return 1.0
        elif min_distance < 0.005:  # Close (< 0.5%)
            return 0.8
        elif min_distance < 0.01:  # Moderate (< 1%)
            return 0.6
        else:
            return 0.3
    
    def _score_ob_proximity(self, m15_data: Dict, current_price: float) -> float:
        """Score Order Block proximity specifically"""
        if not m15_data:
            return 0.0
        
        smc = m15_data.get('smc', {})
        obs = smc.get('order_blocks', {}).get('active', [])
        
        if not obs:
            return 0.0
        
        # Use proximity scores from OBs
        max_proximity = 0.0
        for ob in obs:
            max_proximity = max(max_proximity, ob.proximity_score)
        
        return max_proximity
    
    def _score_fvg_presence(self, m15_data: Dict) -> float:
        """Score Fair Value Gap presence"""
        if not m15_data:
            return 0.0
        
        smc = m15_data.get('smc', {})
        fvgs = smc.get('fair_value_gaps', {}).get('active', [])
        
        # Score based on number and size of active FVGs
        if len(fvgs) >= 2:
            return 1.0
        elif len(fvgs) == 1:
            return 0.6
        else:
            return 0.0
    
    def _score_liquidity_sweep(self, m15_data: Dict) -> float:
        """Score liquidity sweep confirmation"""
        if not m15_data:
            return 0.0
        
        smc = m15_data.get('smc', {})
        sweeps = smc.get('liquidity_sweeps', {}).get('confirmed', [])
        
        # Recent confirmed sweep is strong signal
        if len(sweeps) > 0:
            return 1.0
        else:
            return 0.0
    
    def _score_momentum(self, m15_data: Dict) -> float:
        """Score momentum indicators"""
        if not m15_data or 'features' not in m15_data:
            return 0.5
        
        features = m15_data['features']
        
        # Check RSI
        rsi = features.get('rsi_14', 50)
        if 30 < rsi < 70:  # Not overbought/oversold
            rsi_score = 0.8
        else:
            rsi_score = 0.3
        
        # Check MACD
        macd_hist = features.get('macd_hist', 0)
        macd_score = 0.8 if abs(macd_hist) > 0 else 0.5
        
        return (rsi_score + macd_score) / 2
    
    def _score_session(self) -> float:
        """Score based on trading session"""
        now = datetime.now()
        hour = now.hour
        
        # London session (7-16 UTC): High volume
        if 7 <= hour < 16:
            return 1.0
        # New York session (12-21 UTC): High volume
        elif 12 <= hour < 21:
            return 1.0
        # Asian session (0-9 UTC): Lower volume
        elif 0 <= hour < 9:
            return 0.6
        else:
            return 0.4
    
    def get_weighted_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted confluence score"""
        total_score = 0.0
        for factor, score in scores.items():
            weight = self.weights.get(factor, 0.0)
            total_score += score * weight
        
        return total_score


class SignalGenerator:
    """Generate trading signals from confluence analysis"""
    
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.scorer = ConfluenceScorer(settings)
        self.min_rr = self.settings.get('min_rr_ratio', 2.0)
    
    def generate_signal(self, symbol: str, mtf_data: Dict, 
                       pattern_pred: Dict, current_price: float) -> TradingSignal:
        """
        Generate trading signal from all analysis
        
        Args:
            symbol: Trading symbol
            mtf_data: Multi-timeframe data
            pattern_pred: Pattern recognition prediction
            current_price: Current market price
            
        Returns:
            TradingSignal object
        """
        # Calculate confluence
        scores = self.scorer.calculate_confluence(mtf_data, current_price)
        confluence_score = self.scorer.get_weighted_score(scores)
        
        # Determine action
        if confluence_score >= self.scorer.execute_threshold:
            if pattern_pred.get('prediction', 0) > 0:
                action = 'BUY'
            elif pattern_pred.get('prediction', 0) < 0:
                action = 'SELL'
            else:
                action = 'WAIT'
        elif confluence_score >= self.scorer.watch_threshold:
            action = 'WAIT'
        else:
            action = 'IGNORE'
        
        # Calculate entry/exit levels
        entry, sl, tp, rr = self._calculate_levels(
            action, current_price, mtf_data, pattern_pred
        )
        
        # Build notes
        notes = self._build_notes(scores, pattern_pred, confluence_score)
        
        # Determine structure bias
        h4_score = scores.get('h4_bias', 0.5)
        if h4_score > 0.6:
            bias = 'BULLISH'
        elif h4_score < 0.4:
            bias = 'BEARISH'
        else:
            bias = 'NEUTRAL'
        
        signal = TradingSignal(
            symbol=symbol,
            timeframe='M15',
            timestamp=datetime.now(),
            action=action,
            confidence=pattern_pred.get('confidence', 0.0),
            confluence_score=confluence_score,
            entry_price=entry,
            stop_loss=sl,
            take_profit=tp,
            risk_reward=rr,
            pattern_prediction=pattern_pred,
            smc_factors=scores,
            structure_bias=bias,
            notes=notes
        )
        
        return signal
    
    def _calculate_levels(self, action: str, current_price: float, 
                         mtf_data: Dict, pattern_pred: Dict) -> tuple:
        """Calculate entry, SL, TP levels"""
        atr = mtf_data.get('M15', {}).get('features', {}).get('atr', current_price * 0.001)
        
        if action == 'BUY':
            entry = current_price
            sl = current_price - (2.0 * atr)
            tp = current_price + (4.0 * atr)  # 2:1 R:R minimum
            rr = (tp - entry) / (entry - sl) if entry > sl else 0
        elif action == 'SELL':
            entry = current_price
            sl = current_price + (2.0 * atr)
            tp = current_price - (4.0 * atr)
            rr = (entry - tp) / (sl - entry) if sl > entry else 0
        else:
            entry = current_price
            sl = current_price
            tp = current_price
            rr = 0
        
        return entry, sl, tp, rr
    
    def _build_notes(self, scores: Dict, pattern_pred: Dict, 
                    confluence_score: float) -> List[str]:
        """Build explanatory notes for signal"""
        notes = []
        
        notes.append(f"Confluence Score: {confluence_score:.2%}")
        notes.append(f"Pattern Confidence: {pattern_pred.get('confidence', 0):.2%}")
        
        # Highlight strong factors
        for factor, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0.7:
                notes.append(f"✓ Strong {factor}: {score:.2%}")
            elif score < 0.3:
                notes.append(f"✗ Weak {factor}: {score:.2%}")
        
        return notes
