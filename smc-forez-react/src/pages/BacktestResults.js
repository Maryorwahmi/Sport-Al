/**
 * Backtest Results Page
 * Display and visualize backtest results with charts and metrics
 */
import React, { useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Divider,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DownloadIcon from '@mui/icons-material/Download';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { backtestAPI } from '../services/api';

const TIMEFRAMES = ['M15', 'H1', 'H4', 'D1'];
const SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD'];
const PERIODS = [
  { label: '14 Days', value: 14 },
  { label: '30 Days', value: 30 },
  { label: '60 Days', value: 60 },
  { label: '90 Days', value: 90 },
];

const BacktestResults = () => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [config, setConfig] = useState({
    symbol: 'EURUSD',
    timeframe: 'H1',
    days: 30,
    min_quality: 0.70,
  });

  const handleRunBacktest = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const endDate = new Date();
      const startDate = new Date(endDate.getTime() - config.days * 24 * 60 * 60 * 1000);
      
      const backtestConfig = {
        symbol: config.symbol,
        timeframe: config.timeframe,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        min_signal_quality: config.min_quality,
      };
      
      const data = await backtestAPI.runBacktest(backtestConfig);
      setResults(data);
    } catch (err) {
      console.error('Error running backtest:', err);
      setError('Failed to run backtest. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadResults = () => {
    if (!results) return;
    
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `backtest_${config.symbol}_${config.timeframe}_${Date.now()}.json`;
    link.click();
  };

  const formatEquityCurve = () => {
    if (!results?.equity_curve) return [];
    
    return results.equity_curve.map((point, index) => ({
      index: index + 1,
      balance: point.balance,
      equity: point.equity || point.balance,
    }));
  };

  const metrics = results?.performance_metrics;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Typography variant="h4" gutterBottom>
        Backtesting Results
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Test your strategies on historical data with comprehensive performance metrics
      </Typography>

      {/* Configuration Panel */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Backtest Configuration
        </Typography>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Symbol</InputLabel>
              <Select
                value={config.symbol}
                label="Symbol"
                onChange={(e) => setConfig({ ...config, symbol: e.target.value })}
              >
                {SYMBOLS.map((symbol) => (
                  <MenuItem key={symbol} value={symbol}>
                    {symbol}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Timeframe</InputLabel>
              <Select
                value={config.timeframe}
                label="Timeframe"
                onChange={(e) => setConfig({ ...config, timeframe: e.target.value })}
              >
                {TIMEFRAMES.map((tf) => (
                  <MenuItem key={tf} value={tf}>
                    {tf}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Period</InputLabel>
              <Select
                value={config.days}
                label="Period"
                onChange={(e) => setConfig({ ...config, days: e.target.value })}
              >
                {PERIODS.map((period) => (
                  <MenuItem key={period.value} value={period.value}>
                    {period.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Min Quality"
              type="number"
              inputProps={{ min: 0, max: 1, step: 0.05 }}
              value={config.min_quality}
              onChange={(e) => setConfig({ ...config, min_quality: parseFloat(e.target.value) })}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <PlayArrowIcon />}
              onClick={handleRunBacktest}
              disabled={loading}
              fullWidth
            >
              {loading ? 'Running Backtest...' : 'Run Backtest'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results Display */}
      {results && (
        <>
          {/* Performance Metrics Cards */}
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Total Return
                  </Typography>
                  <Typography variant="h4" color={results.total_return >= 0 ? 'success.main' : 'error.main'}>
                    {results.total_return?.toFixed(2)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Win Rate
                  </Typography>
                  <Typography variant="h4">
                    {((metrics?.win_rate || 0) * 100).toFixed(1)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Profit Factor
                  </Typography>
                  <Typography variant="h4">
                    {metrics?.profit_factor?.toFixed(2) || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" variant="body2">
                    Max Drawdown
                  </Typography>
                  <Typography variant="h4" color="error.main">
                    {metrics?.max_drawdown_pct?.toFixed(2)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Equity Curve Chart */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6">
                Equity Curve
              </Typography>
              <Button
                startIcon={<DownloadIcon />}
                onClick={handleDownloadResults}
              >
                Download Results
              </Button>
            </Box>
            
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={formatEquityCurve()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="index" label={{ value: 'Trade Number', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Balance ($)', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="balance" stroke="#8884d8" name="Balance" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </Paper>

          {/* Detailed Metrics */}
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Detailed Performance Metrics
            </Typography>
            <Divider sx={{ my: 2 }} />
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Trade Statistics
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography>Total Trades:</Typography>
                    <Typography fontWeight="bold">{metrics?.total_trades || 0}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography>Winning Trades:</Typography>
                    <Typography fontWeight="bold" color="success.main">
                      {metrics?.winning_trades || 0}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography>Losing Trades:</Typography>
                    <Typography fontWeight="bold" color="error.main">
                      {metrics?.losing_trades || 0}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography>Consecutive Wins:</Typography>
                    <Typography fontWeight="bold">{metrics?.consecutive_wins || 0}</Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Consecutive Losses:</Typography>
                    <Typography fontWeight="bold">{metrics?.consecutive_losses || 0}</Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Financial Performance
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography>Final Balance:</Typography>
                    <Typography fontWeight="bold">
                      ${results.final_balance?.toFixed(2) || 'N/A'}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography>Total P&L:</Typography>
                    <Typography fontWeight="bold" color={metrics?.total_pnl >= 0 ? 'success.main' : 'error.main'}>
                      ${metrics?.total_pnl?.toFixed(2) || 'N/A'}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography>Average Win:</Typography>
                    <Typography fontWeight="bold" color="success.main">
                      ${metrics?.avg_win?.toFixed(2) || 'N/A'}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography>Average Loss:</Typography>
                    <Typography fontWeight="bold" color="error.main">
                      ${metrics?.avg_loss?.toFixed(2) || 'N/A'}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography>Sharpe Ratio:</Typography>
                    <Typography fontWeight="bold">{metrics?.sharpe_ratio?.toFixed(2) || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </>
      )}
    </Box>
  );
};

export default BacktestResults;
