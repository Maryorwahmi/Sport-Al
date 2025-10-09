"""
Feature engineering for candle pattern recognition
"""
import pandas as pd
import numpy as np
from typing import Dict, List

try:
    from data.data_manager import calculate_atr
except ImportError:
    from ..data.data_manager import calculate_atr


def extract_candle_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract features from each candle
    
    Returns DataFrame with additional feature columns
    """
    df_feat = df.copy()
    
    # Basic candle metrics
    df_feat['body'] = abs(df['Close'] - df['Open'])
    df_feat['wick_up'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df_feat['wick_down'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    df_feat['range'] = df['High'] - df['Low']
    
    # Percentage metrics
    df_feat['body_pct'] = df_feat['body'] / df_feat['range'].replace(0, np.nan)
    df_feat['wick_up_pct'] = df_feat['wick_up'] / df_feat['range'].replace(0, np.nan)
    df_feat['wick_down_pct'] = df_feat['wick_down'] / df_feat['range'].replace(0, np.nan)
    
    # Direction
    df_feat['direction'] = np.where(df['Close'] > df['Open'], 1, -1)
    
    # ATR-normalized features
    atr = calculate_atr(df)
    df_feat['body_atr'] = df_feat['body'] / atr.replace(0, np.nan)
    df_feat['range_atr'] = df_feat['range'] / atr.replace(0, np.nan)
    
    # Price position
    df_feat['close_position'] = (df['Close'] - df['Low']) / df_feat['range'].replace(0, np.nan)
    
    # Moving averages
    for period in [10, 20, 50]:
        df_feat[f'ema_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
        df_feat[f'dist_ema_{period}'] = (df['Close'] - df_feat[f'ema_{period}']) / atr.replace(0, np.nan)
    
    # RSI
    df_feat['rsi_14'] = calculate_rsi(df['Close'], 14)
    
    # VWAP
    df_feat['vwap'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    df_feat['dist_vwap'] = (df['Close'] - df_feat['vwap']) / atr.replace(0, np.nan)
    
    # Volume
    df_feat['volume_sma'] = df['Volume'].rolling(20).mean()
    df_feat['volume_ratio'] = df['Volume'] / df_feat['volume_sma'].replace(0, np.nan)
    
    # Volatility
    df_feat['volatility'] = df['Close'].pct_change().rolling(20).std()
    
    return df_feat.fillna(0)


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.fillna(50)


def create_pattern_windows(df: pd.DataFrame, window_size: int = 20, 
                          features: List[str] = None) -> np.ndarray:
    """
    Create sliding windows of candle patterns
    
    Args:
        df: DataFrame with features
        window_size: Number of candles in each window
        features: List of feature column names to include
        
    Returns:
        3D array of shape (n_windows, window_size, n_features)
    """
    if features is None:
        # Default features for pattern recognition
        features = [
            'body', 'wick_up', 'wick_down', 'body_pct', 'direction',
            'body_atr', 'range_atr', 'close_position',
            'dist_ema_20', 'rsi_14', 'volume_ratio'
        ]
    
    # Ensure features exist in dataframe
    features = [f for f in features if f in df.columns]
    
    data = df[features].values
    n_samples = len(data) - window_size + 1
    
    if n_samples <= 0:
        return np.array([])
    
    # Create sliding windows
    windows = np.array([data[i:i+window_size] for i in range(n_samples)])
    
    return windows


def extract_pattern_signature(window: np.ndarray) -> Dict[str, float]:
    """
    Extract signature features from a pattern window
    
    Args:
        window: Array of shape (window_size, n_features)
        
    Returns:
        Dictionary of signature features
    """
    signature = {}
    
    # Statistical features
    signature['mean'] = np.mean(window)
    signature['std'] = np.std(window)
    signature['min'] = np.min(window)
    signature['max'] = np.max(window)
    signature['range'] = signature['max'] - signature['min']
    
    # Trend features
    if window.shape[0] > 1:
        # Linear trend
        x = np.arange(window.shape[0])
        y = window[:, 0] if window.ndim > 1 else window
        coeffs = np.polyfit(x, y, 1)
        signature['trend_slope'] = coeffs[0]
        signature['trend_intercept'] = coeffs[1]
    
    # Shape features
    if window.ndim > 1 and window.shape[1] > 0:
        # Direction changes
        directions = np.sign(np.diff(window[:, 0]))
        signature['direction_changes'] = np.sum(np.abs(np.diff(directions))) / 2
        
        # Volatility
        signature['volatility'] = np.std(np.diff(window[:, 0]))
    
    return signature


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate comprehensive technical indicators"""
    df_ind = df.copy()
    
    # ATR
    df_ind['atr'] = calculate_atr(df, 14)
    
    # Bollinger Bands
    sma_20 = df['Close'].rolling(20).mean()
    std_20 = df['Close'].rolling(20).std()
    df_ind['bb_upper'] = sma_20 + (2 * std_20)
    df_ind['bb_lower'] = sma_20 - (2 * std_20)
    df_ind['bb_middle'] = sma_20
    df_ind['bb_position'] = (df['Close'] - df_ind['bb_lower']) / \
                            (df_ind['bb_upper'] - df_ind['bb_lower']).replace(0, np.nan)
    
    # MACD
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df_ind['macd'] = ema_12 - ema_26
    df_ind['macd_signal'] = df_ind['macd'].ewm(span=9, adjust=False).mean()
    df_ind['macd_hist'] = df_ind['macd'] - df_ind['macd_signal']
    
    # Stochastic
    low_14 = df['Low'].rolling(14).min()
    high_14 = df['High'].rolling(14).max()
    df_ind['stoch_k'] = 100 * (df['Close'] - low_14) / (high_14 - low_14).replace(0, np.nan)
    df_ind['stoch_d'] = df_ind['stoch_k'].rolling(3).mean()
    
    # ADX (simplified)
    df_ind['adx'] = calculate_adx(df)
    
    return df_ind.fillna(0)


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    # Plus and minus directional movement
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # True range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Smoothed values
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr.replace(0, np.nan))
    
    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(period).mean()
    
    return adx.fillna(0)
