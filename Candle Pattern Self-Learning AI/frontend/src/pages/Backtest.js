import React, { useState } from 'react';
import { Container, Typography, Card, CardContent, Grid, TextField, Button, CircularProgress, Box } from '@mui/material';
import { Assessment } from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiService from '../services/api';

function Backtest() {
  const [config, setConfig] = useState({
    symbol: 'EURUSD',
    timeframe: 'H1',
    n_bars: 1000
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const runBacktest = async () => {
    setLoading(true);
    try {
      const response = await apiService.runBacktest(config);
      setResults(response.data);
    } catch (error) {
      console.error('Error running backtest:', error);
      alert('Error running backtest. Make sure the model is trained first.');
    }
    setLoading(false);
  };

  const chartData = results?.equity_curve?.map((value, index) => ({
    index,
    equity: value
  })) || [];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        <Assessment sx={{ fontSize: 40, mr: 2, verticalAlign: 'middle' }} />
        Backtesting
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Configuration</Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <TextField
                    label="Symbol"
                    value={config.symbol}
                    onChange={(e) => setConfig({...config, symbol: e.target.value})}
                    fullWidth
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    label="Timeframe"
                    value={config.timeframe}
                    onChange={(e) => setConfig({...config, timeframe: e.target.value})}
                    fullWidth
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    label="Number of Bars"
                    type="number"
                    value={config.n_bars}
                    onChange={(e) => setConfig({...config, n_bars: parseInt(e.target.value)})}
                    fullWidth
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    onClick={runBacktest}
                    disabled={loading}
                    fullWidth
                  >
                    {loading ? <CircularProgress size={24} /> : 'Run Backtest'}
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Performance Metrics</Typography>
              {results ? (
                <Box>
                  <Typography variant="body2">
                    Total Trades: {results.metrics?.total_trades || 0}
                  </Typography>
                  <Typography variant="body2">
                    Win Rate: {((results.metrics?.win_rate || 0) * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2">
                    Profit Factor: {(results.metrics?.profit_factor || 0).toFixed(2)}
                  </Typography>
                  <Typography variant="body2">
                    Total Return: {((results.metrics?.total_return || 0) * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2">
                    Max Drawdown: {((results.metrics?.max_drawdown || 0) * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2">
                    Sharpe Ratio: {(results.metrics?.sharpe_ratio || 0).toFixed(2)}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Run a backtest to see metrics
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {results && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Equity Curve</Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="index" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="equity" stroke="#8884d8" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
}

export default Backtest;
