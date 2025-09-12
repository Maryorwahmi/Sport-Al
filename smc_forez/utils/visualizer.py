"""
Visual plotting module for SMC Forez
Creates professional charts with market structure and SMC analysis
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set professional chart style
plt.style.use('seaborn-v0_8' if 'seaborn-v0_8' in plt.style.available else 'default')
colors = {
    'background': '#0e1117',
    'grid': '#262730',
    'text': '#fafafa',
    'buy': '#00ff88',
    'sell': '#ff4444',
    'neutral': '#888888',
    'fvg': '#ffaa00',
    'order_block': '#aa88ff',
    'liquidity': '#00aaff',
    'support': '#00ff88',
    'resistance': '#ff4444'
}


class SMCChartPlotter:
    """
    Professional chart plotter for SMC analysis
    """
    
    def __init__(self, style: str = "dark", figsize: Tuple[int, int] = (16, 10)):
        """
        Initialize chart plotter
        
        Args:
            style: Chart style ("dark" or "light")
            figsize: Figure size (width, height)
        """
        self.style = style
        self.figsize = figsize
        self._setup_style()
    
    def _setup_style(self):
        """Setup chart styling"""
        if self.style == "dark":
            plt.rcParams.update({
                'figure.facecolor': colors['background'],
                'axes.facecolor': colors['background'],
                'axes.edgecolor': colors['grid'],
                'axes.labelcolor': colors['text'],
                'text.color': colors['text'],
                'xtick.color': colors['text'],
                'ytick.color': colors['text'],
                'grid.color': colors['grid'],
                'axes.grid': True,
                'grid.alpha': 0.3
            })
    
    def plot_market_structure(self, 
                            data: pd.DataFrame,
                            market_structure: Dict,
                            smc_analysis: Dict,
                            title: str = "SMC Market Analysis",
                            save_path: Optional[str] = None) -> str:
        """
        Plot comprehensive market structure and SMC analysis
        
        Args:
            data: OHLC data with datetime index
            market_structure: Market structure analysis results
            smc_analysis: SMC analysis results
            title: Chart title
            save_path: Path to save chart (optional)
            
        Returns:
            Path to saved chart
        """
        try:
            # Create figure and subplots
            fig = plt.figure(figsize=self.figsize)
            gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1], hspace=0.1)
            
            # Main price chart
            ax_main = fig.add_subplot(gs[0])
            self._plot_candlesticks(ax_main, data)
            self._plot_market_structure(ax_main, data, market_structure)
            self._plot_smc_patterns(ax_main, data, smc_analysis)
            
            # Volume subplot
            ax_volume = fig.add_subplot(gs[1], sharex=ax_main)
            self._plot_volume(ax_volume, data)
            
            # Indicator subplot
            ax_indicators = fig.add_subplot(gs[2], sharex=ax_main)
            self._plot_indicators(ax_indicators, data, market_structure)
            
            # Format and style
            self._format_chart(ax_main, title)
            self._format_subplot(ax_volume, "Volume")
            self._format_subplot(ax_indicators, "Momentum")
            
            # Add legend
            self._add_legend(ax_main)
            
            # Save or show
            if save_path:
                plt.savefig(save_path, facecolor=colors['background'], 
                           dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"chart_analysis_{timestamp}.png"
                plt.savefig(save_path, facecolor=colors['background'], 
                           dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
                
        except Exception as e:
            print(f"Error plotting chart: {str(e)}")
            plt.close()
            return None
    
    def _plot_candlesticks(self, ax, data: pd.DataFrame):
        """Plot candlestick chart"""
        try:
            # Calculate candlestick data
            up = data['Close'] >= data['Open']
            down = ~up
            
            # Plot wicks
            ax.vlines(data.index[up], data['Low'][up], data['High'][up], 
                     color=colors['buy'], linewidth=1, alpha=0.8)
            ax.vlines(data.index[down], data['Low'][down], data['High'][down], 
                     color=colors['sell'], linewidth=1, alpha=0.8)
            
            # Plot bodies
            width = (data.index[1] - data.index[0]).total_seconds() / (24 * 3600) * 0.6
            
            for i, (idx, row) in enumerate(data.iterrows()):
                if row['Close'] >= row['Open']:
                    color = colors['buy']
                    bottom = row['Open']
                    height = row['Close'] - row['Open']
                else:
                    color = colors['sell']
                    bottom = row['Close']
                    height = row['Open'] - row['Close']
                
                rect = Rectangle((mdates.date2num(idx) - width/2, bottom), 
                               width, height, facecolor=color, alpha=0.8)
                ax.add_patch(rect)
                
        except Exception as e:
            print(f"Error plotting candlesticks: {str(e)}")
    
    def _plot_market_structure(self, ax, data: pd.DataFrame, market_structure: Dict):
        """Plot market structure levels and patterns"""
        try:
            # Plot swing points
            swing_highs = market_structure.get('swing_high_levels', [])
            swing_lows = market_structure.get('swing_low_levels', [])
            
            for level in swing_highs:
                if 'price' in level and 'timestamp' in level:
                    ax.scatter(level['timestamp'], level['price'], 
                             color=colors['resistance'], marker='v', s=100, 
                             alpha=0.8, label='Swing High' if level == swing_highs[0] else "")
            
            for level in swing_lows:
                if 'price' in level and 'timestamp' in level:
                    ax.scatter(level['timestamp'], level['price'], 
                             color=colors['support'], marker='^', s=100, 
                             alpha=0.8, label='Swing Low' if level == swing_lows[0] else "")
            
            # Plot support/resistance levels
            support_levels = market_structure.get('support_levels', [])
            resistance_levels = market_structure.get('resistance_levels', [])
            
            for level in support_levels[-5:]:  # Show last 5 levels
                if 'price' in level:
                    ax.axhline(y=level['price'], color=colors['support'], 
                             linestyle='--', alpha=0.6, linewidth=1)
            
            for level in resistance_levels[-5:]:  # Show last 5 levels
                if 'price' in level:
                    ax.axhline(y=level['price'], color=colors['resistance'], 
                             linestyle='--', alpha=0.6, linewidth=1)
            
            # Plot trend lines
            trend_direction = market_structure.get('trend_direction', 'SIDEWAYS')
            if trend_direction != 'SIDEWAYS':
                self._plot_trend_line(ax, data, trend_direction)
                
        except Exception as e:
            print(f"Error plotting market structure: {str(e)}")
    
    def _plot_smc_patterns(self, ax, data: pd.DataFrame, smc_analysis: Dict):
        """Plot Smart Money Concepts patterns"""
        try:
            # Plot Fair Value Gaps
            fvgs = smc_analysis.get('fair_value_gaps', {}).get('active', [])
            for fvg in fvgs[-10:]:  # Show last 10 FVGs
                if all(k in fvg for k in ['top', 'bottom', 'start_time', 'end_time']):
                    start_time = fvg['start_time']
                    end_time = fvg.get('end_time', data.index[-1])
                    
                    ax.fill_between([start_time, end_time], 
                                  fvg['bottom'], fvg['top'],
                                  color=colors['fvg'], alpha=0.3,
                                  label='Fair Value Gap' if fvg == fvgs[0] else "")
            
            # Plot Order Blocks
            order_blocks = smc_analysis.get('order_blocks', {}).get('valid', [])
            for ob in order_blocks[-5:]:  # Show last 5 order blocks
                if all(k in ob for k in ['top', 'bottom', 'timestamp']):
                    timestamp = ob['timestamp']
                    
                    # Draw order block rectangle
                    width = (data.index[-1] - timestamp).total_seconds() / (24 * 3600) * 0.1
                    rect = Rectangle((mdates.date2num(timestamp), ob['bottom']), 
                                   width, ob['top'] - ob['bottom'],
                                   facecolor=colors['order_block'], alpha=0.3,
                                   edgecolor=colors['order_block'])
                    ax.add_patch(rect)
                    
                    if ob == order_blocks[0]:
                        rect.set_label('Order Block')
            
            # Plot Liquidity Zones
            liquidity_zones = smc_analysis.get('liquidity_zones', {}).get('unswept', [])
            for lz in liquidity_zones[-5:]:  # Show last 5 liquidity zones
                if 'price' in lz and 'timestamp' in lz:
                    ax.scatter(lz['timestamp'], lz['price'], 
                             color=colors['liquidity'], marker='o', s=80, 
                             alpha=0.8, label='Liquidity Zone' if lz == liquidity_zones[0] else "")
            
            # Plot Supply/Demand Zones
            supply_zones = smc_analysis.get('supply_demand_zones', {}).get('supply', [])
            demand_zones = smc_analysis.get('supply_demand_zones', {}).get('demand', [])
            
            for sz in supply_zones[-3:]:  # Show last 3 supply zones
                if all(k in sz for k in ['top', 'bottom', 'timestamp']):
                    self._plot_zone(ax, sz, colors['sell'], 'Supply Zone' if sz == supply_zones[0] else "")
            
            for dz in demand_zones[-3:]:  # Show last 3 demand zones
                if all(k in dz for k in ['top', 'bottom', 'timestamp']):
                    self._plot_zone(ax, dz, colors['buy'], 'Demand Zone' if dz == demand_zones[0] else "")
                    
        except Exception as e:
            print(f"Error plotting SMC patterns: {str(e)}")
    
    def _plot_zone(self, ax, zone: Dict, color: str, label: str):
        """Plot supply/demand zone"""
        try:
            timestamp = zone['timestamp']
            top = zone['top']
            bottom = zone['bottom']
            
            # Draw zone as rectangle
            width = 20  # Fixed width in days
            rect = Rectangle((mdates.date2num(timestamp), bottom), 
                           width, top - bottom,
                           facecolor=color, alpha=0.2,
                           edgecolor=color, linestyle='-', linewidth=1)
            ax.add_patch(rect)
            
            if label:
                rect.set_label(label)
                
        except Exception as e:
            print(f"Error plotting zone: {str(e)}")
    
    def _plot_trend_line(self, ax, data: pd.DataFrame, trend_direction: str):
        """Plot trend line"""
        try:
            if len(data) < 20:
                return
            
            # Simple trend line using linear regression on highs/lows
            x_vals = np.arange(len(data))
            
            if trend_direction == 'UPTREND':
                # Use swing lows for uptrend line
                lows = data['Low'].rolling(window=5).min()
                valid_indices = ~lows.isna()
                if valid_indices.sum() > 1:
                    coeffs = np.polyfit(x_vals[valid_indices], lows[valid_indices], 1)
                    trend_line = np.poly1d(coeffs)(x_vals)
                    ax.plot(data.index, trend_line, color=colors['buy'], 
                           linestyle='-', linewidth=2, alpha=0.7, label='Uptrend Line')
            
            elif trend_direction == 'DOWNTREND':
                # Use swing highs for downtrend line
                highs = data['High'].rolling(window=5).max()
                valid_indices = ~highs.isna()
                if valid_indices.sum() > 1:
                    coeffs = np.polyfit(x_vals[valid_indices], highs[valid_indices], 1)
                    trend_line = np.poly1d(coeffs)(x_vals)
                    ax.plot(data.index, trend_line, color=colors['sell'], 
                           linestyle='-', linewidth=2, alpha=0.7, label='Downtrend Line')
                    
        except Exception as e:
            print(f"Error plotting trend line: {str(e)}")
    
    def _plot_volume(self, ax, data: pd.DataFrame):
        """Plot volume bars"""
        try:
            if 'Volume' not in data.columns:
                # Create mock volume data if not available
                data['Volume'] = np.random.randint(1000, 10000, len(data))
            
            up = data['Close'] >= data['Open']
            ax.bar(data.index[up], data['Volume'][up], 
                  color=colors['buy'], alpha=0.6, width=0.8)
            ax.bar(data.index[~up], data['Volume'][~up], 
                  color=colors['sell'], alpha=0.6, width=0.8)
                  
        except Exception as e:
            print(f"Error plotting volume: {str(e)}")
    
    def _plot_indicators(self, ax, data: pd.DataFrame, market_structure: Dict):
        """Plot technical indicators"""
        try:
            # Calculate RSI
            rsi = self._calculate_rsi(data['Close'])
            ax.plot(data.index, rsi, color=colors['neutral'], linewidth=1.5, label='RSI')
            
            # Add RSI levels
            ax.axhline(y=70, color=colors['sell'], linestyle='--', alpha=0.5)
            ax.axhline(y=30, color=colors['buy'], linestyle='--', alpha=0.5)
            ax.axhline(y=50, color=colors['neutral'], linestyle='-', alpha=0.3)
            
            ax.set_ylim(0, 100)
            
        except Exception as e:
            print(f"Error plotting indicators: {str(e)}")
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def _format_chart(self, ax, title: str):
        """Format main chart"""
        ax.set_title(title, fontsize=16, fontweight='bold', color=colors['text'], pad=20)
        ax.set_ylabel('Price', fontsize=12, color=colors['text'])
        ax.tick_params(axis='both', which='major', labelsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(ax.get_xticklabels())//10)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    def _format_subplot(self, ax, ylabel: str):
        """Format subplot"""
        ax.set_ylabel(ylabel, fontsize=10, color=colors['text'])
        ax.tick_params(axis='both', which='major', labelsize=9)
        ax.grid(True, alpha=0.3)
    
    def _add_legend(self, ax):
        """Add legend to chart"""
        try:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc='upper left', frameon=True, 
                         fancybox=True, shadow=True, fontsize=9,
                         facecolor=colors['background'], edgecolor=colors['grid'])
        except Exception as e:
            print(f"Error adding legend: {str(e)}")
    
    def plot_backtest_results(self, 
                            results: Dict,
                            save_path: Optional[str] = None) -> str:
        """
        Plot backtest results with equity curve and trade analysis
        
        Args:
            results: Backtest results dictionary
            save_path: Path to save chart
            
        Returns:
            Path to saved chart
        """
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=self.figsize)
            
            # Equity curve
            trades = results.get('trades', [])
            if trades:
                cumulative_pnl = np.cumsum([t.get('pnl', 0) for t in trades])
                ax1.plot(cumulative_pnl, color=colors['buy'], linewidth=2)
                ax1.set_title('Equity Curve', fontweight='bold')
                ax1.set_ylabel('P&L ($)')
                ax1.grid(True, alpha=0.3)
            
            # Trade distribution
            pnls = [t.get('pnl', 0) for t in trades if t.get('pnl') is not None]
            if pnls:
                ax2.hist(pnls, bins=20, color=colors['neutral'], alpha=0.7)
                ax2.set_title('P&L Distribution', fontweight='bold')
                ax2.set_xlabel('P&L ($)')
                ax2.set_ylabel('Frequency')
                ax2.grid(True, alpha=0.3)
            
            # Monthly returns
            metrics = results.get('performance_metrics', {})
            ax3.bar(['Win Rate', 'Profit Factor', 'Sharpe Ratio'], 
                   [metrics.get('win_rate', 0)*100, 
                    metrics.get('profit_factor', 0), 
                    metrics.get('sharpe_ratio', 0)],
                   color=[colors['buy'], colors['neutral'], colors['sell']])
            ax3.set_title('Performance Metrics', fontweight='bold')
            ax3.grid(True, alpha=0.3)
            
            # Drawdown
            if trades:
                running_max = np.maximum.accumulate(cumulative_pnl)
                drawdown = (cumulative_pnl - running_max) / running_max * 100
                ax4.fill_between(range(len(drawdown)), drawdown, 0, 
                               color=colors['sell'], alpha=0.6)
                ax4.set_title('Drawdown (%)', fontweight='bold')
                ax4.set_ylabel('Drawdown (%)')
                ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save
            if save_path:
                plt.savefig(save_path, facecolor=colors['background'], 
                           dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"backtest_results_{timestamp}.png"
                plt.savefig(save_path, facecolor=colors['background'], 
                           dpi=300, bbox_inches='tight')
                plt.close()
                return save_path
                
        except Exception as e:
            print(f"Error plotting backtest results: {str(e)}")
            plt.close()
            return None


def create_chart(data: pd.DataFrame, 
                market_structure: Dict, 
                smc_analysis: Dict,
                title: str = "SMC Analysis") -> str:
    """
    Quick function to create a chart
    
    Args:
        data: OHLC data
        market_structure: Market structure analysis
        smc_analysis: SMC analysis
        title: Chart title
        
    Returns:
        Path to saved chart
    """
    plotter = SMCChartPlotter()
    return plotter.plot_market_structure(data, market_structure, smc_analysis, title)