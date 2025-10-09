# User Manual - Candle Pattern Self-Learning AI

## Getting Started

### First Time Setup

1. **Install and Start the Application**
   - Follow the [Setup Guide](SETUP_GUIDE.md)
   - Start both backend and frontend servers
   - Open http://localhost:3000 in your browser

2. **Train the Pattern Recognition Model**
   - Click on "Training" in the navigation bar
   - Configure:
     - Symbol: EURUSD (or preferred currency pair)
     - Timeframe: H1 (recommended for training)
     - Number of Bars: 5000 (more data = better model)
   - Click "Start Training"
   - Wait 2-5 minutes for completion

3. **Verify Model is Ready**
   - Check Dashboard for "Model Trained: ✓ Yes"
   - Model Info should show number of patterns detected

---

## Main Features

### 1. Dashboard

**Purpose**: Monitor trading opportunities and system status

**How to Use:**
1. Check system status in top cards
2. Click "Scan Markets" to find opportunities
3. Review trading signals:
   - Symbol and direction (BUY/SELL)
   - Entry price, Stop Loss, Take Profit
   - Confluence score (higher = stronger signal)
   - Risk/Reward ratio

**Understanding Signals:**
- **BUY**: Bullish signal, consider long position
- **SELL**: Bearish signal, consider short position
- **WAIT**: Moderate signal, wait for better entry
- **IGNORE**: Low confidence, skip this opportunity

**Confluence Score:**
- **75%+**: High probability, strong confluence
- **50-75%**: Moderate, wait for confirmation
- **<50%**: Low confidence, avoid

### 2. Training Page

**Purpose**: Train ML model on historical candlestick patterns

**Steps:**
1. Select symbol (e.g., EURUSD, GBPUSD)
2. Choose timeframe (H1 recommended)
3. Set number of bars (5000+ for better results)
4. Click "Start Training"
5. Monitor progress in message box

**Tips:**
- More data = better predictions
- Train on timeframe you'll trade
- Retrain weekly with new data
- Different symbols may need separate models

**What Happens During Training:**
- System analyzes thousands of candle patterns
- Identifies recurring patterns
- Learns which patterns predict price movements
- Calculates confidence scores

### 3. Backtest Page

**Purpose**: Test strategy performance on historical data

**How to Run Backtest:**
1. Configure parameters:
   - Symbol: Currency pair to test
   - Timeframe: Trading timeframe
   - Number of Bars: Historical data amount
2. Click "Run Backtest"
3. Wait for results (30 seconds - 2 minutes)

**Understanding Results:**

**Performance Metrics:**
- **Total Trades**: Number of trades executed
- **Win Rate**: % of profitable trades (aim for >50%)
- **Profit Factor**: Gross profit / Gross loss (>1.5 is good)
- **Total Return**: Overall profit/loss percentage
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return (>1 is good)

**Equity Curve:**
- Shows account balance over time
- Upward trend = profitable strategy
- Smooth curve = consistent performance
- Sharp drops = high risk periods

**What Makes a Good Backtest:**
- Win rate > 50%
- Profit factor > 1.5
- Max drawdown < 20%
- Sharpe ratio > 1.0
- Consistent equity curve growth

---

## Trading Workflow

### Recommended Daily Routine

**Morning (Market Open):**
1. Check Dashboard system status
2. Verify model is trained
3. Click "Scan Markets"
4. Review opportunities

**Analysis:**
1. Check confluence score (aim for 75%+)
2. Verify pattern confidence
3. Review entry, SL, TP levels
4. Confirm R:R ratio (minimum 2:1)

**Decision Making:**
1. Only take signals with:
   - Confluence > 75%
   - Confidence > 60%
   - R:R ratio > 2.0
2. Check multiple timeframes
3. Consider market conditions
4. Respect risk limits

**End of Day:**
1. Review executed trades
2. Update trading journal
3. Check overall performance
4. Plan next day

---

## Understanding the Technology

### Smart Money Concepts (SMC)

**Order Blocks (OB)**
- Last opposing candle before impulse move
- Institutional entry zones
- High probability reversal areas
- System tracks unmitigated blocks

**Fair Value Gaps (FVG)**
- Price imbalances on chart
- Areas where no trading occurred
- Often act as support/resistance
- Price tends to fill these gaps

**Break of Structure (BOS)**
- Breaking previous swing high/low
- Confirms trend continuation
- Strong momentum signal

**Change of Character (CHOCH)**
- Failure to make new high/low
- Potential trend reversal
- Warning signal

**Liquidity Sweeps**
- Price briefly breaks level then reverses
- "Stop hunt" by institutions
- Strong reversal signal

### Multi-Timeframe Analysis

**H4 (4-Hour)**
- Determines overall bias
- Trend direction
- Major structure

**H1 (1-Hour)**
- Confirms H4 bias
- Entry zone identification
- Structure validation

**M15 (15-Minute)**
- Precise entry timing
- Risk management levels
- Quick confirmation

**How It Works:**
1. H4 shows bullish bias
2. H1 confirms bullish structure
3. M15 provides exact entry point
4. All timeframes must align for best signals

### Pattern Recognition

**What the AI Learns:**
- Candlestick formations
- Pattern sequences
- Price action context
- Successful vs failed patterns

**Prediction Process:**
1. Current pattern extracted
2. Matched to learned patterns
3. Historical outcomes analyzed
4. Probability calculated
5. Confidence score assigned

---

## Risk Management

### Position Sizing

**Automatic Calculation:**
- Based on account balance
- Fixed % risk per trade (default 1%)
- Adjusts for stop loss distance
- Respects maximum position size

**Example:**
- Account: $10,000
- Risk: 1% = $100
- Stop Loss: 50 pips
- Position Size: Calculated to risk exactly $100

### Risk Limits

**Per Trade:**
- Maximum 1-2% account risk
- Minimum R:R ratio 2:1
- ATR-based stops

**Portfolio:**
- Maximum 3 concurrent trades
- Total exposure < 5%
- Correlation monitoring

**Daily:**
- Maximum 3% daily loss
- Auto-stop on limit breach
- Reset each trading day

### Best Practices

1. **Never risk more than 1% per trade**
2. **Always use stop losses**
3. **Maintain 2:1 minimum R:R**
4. **Limit concurrent positions**
5. **Keep trading journal**
6. **Review performance weekly**
7. **Adjust strategy based on results**

---

## Mobile & Desktop Use

### Progressive Web App (PWA)

**Install on Mobile:**
1. Open app in mobile browser
2. Tap "Add to Home Screen"
3. Confirm installation
4. App icon appears on home screen
5. Works like native app

**Install on Desktop:**
1. Open in Chrome/Edge
2. Click install icon in address bar
3. Confirm installation
4. App opens in standalone window

**Offline Support:**
- Core functionality works offline
- Cached data available
- Syncs when connection restored

---

## Troubleshooting

### "Model Not Trained" Error
**Solution:** Go to Training page and train the model first

### No Trading Signals
**Solution:** 
- Ensure model is trained
- Try different symbols
- Adjust timeframes
- Market may have low volatility

### API Connection Error
**Solution:**
- Check backend is running (port 8000)
- Verify .env file has correct API_URL
- Check firewall settings

### Poor Backtest Results
**Solution:**
- Retrain model with more data
- Adjust risk parameters
- Try different timeframes
- Review confluence settings

---

## Tips for Success

1. **Start with Paper Trading**
   - Use backtest extensively
   - Understand system behavior
   - Build confidence

2. **Quality Over Quantity**
   - Wait for high confluence signals
   - Don't force trades
   - Patience pays off

3. **Continuous Learning**
   - Retrain model weekly
   - Monitor performance
   - Adapt to market changes

4. **Risk Management is Key**
   - Never override risk limits
   - Always use stop losses
   - Protect your capital

5. **Keep a Journal**
   - Record all trades
   - Note market conditions
   - Review regularly
   - Learn from mistakes

---

## Keyboard Shortcuts

- **Ctrl+1**: Dashboard
- **Ctrl+2**: Training
- **Ctrl+3**: Backtest
- **F5**: Refresh data
- **Ctrl+R**: Run scan

---

## Support

For questions or issues:
1. Check this manual
2. Review Setup Guide
3. Check API documentation
4. Run test suite
5. Review logs

---

**Happy Trading! 🚀📈**

Remember: Trading involves risk. Never risk more than you can afford to lose.
