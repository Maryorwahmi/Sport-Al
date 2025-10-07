/**
 * Backtest Results Page
 * Displays comprehensive backtest metrics and visualizations
 */
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  Chip,
  Divider,
  Button,
} from '@mui/material';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const BacktestResults = () => {
  // Mock data - replace with actual backtest results
  const [results] = useState({
    config: {
      name: 'Standard Run',
      symbol: 'EURUSD',
      timeframe: 'H1',
      multi_timeframes: ['H4', 'H1', 'M15'],
      days: 30,
      start_date: '2024-01-01',
      end_date: '2024-01-31',
    },
    initial_balance: 10000,
    final_balance: 11250,
    metrics: {
      total_trades: 45,
      winning_trades: 27,
      losing_trades: 18,
      win_rate: 60.0,
      profit_factor: 2.3,
      expected_payoff: 27.78,
      expected_payoff_pips: 15.5,
      max_drawdown: 450,
      max_drawdown_pct: 4.5,
      sharpe_ratio: 1.85,
      recovery_factor: 2.78,
      avg_win: 85.5,
      avg_loss: 52.3,
      avg_win_pips: 45.2,
      avg_loss_pips: 28.7,
      largest_win: 245.0,
      largest_loss: 105.0,
      max_consecutive_wins: 6,
      max_consecutive_losses: 4,
      avg_trade_duration: '4 hours, 15 minutes',
      avg_rr_ratio: 2.45,
    },
  });

  // Mock equity curve data
  const equityCurve = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    balance: results.initial_balance + (i * 50) + Math.random() * 100,
  }));

  // Mock trade distribution
  const tradeDistribution = [
    { name: 'Wins', value: results.metrics.winning_trades, fill: '#4caf50' },
    { name: 'Losses', value: results.metrics.losing_trades, fill: '#f44336' },
  ];

  const MetricCard = ({ title, value, subtitle, color = 'primary' }) => (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {title}
        </Typography>
        <Typography variant="h5" color={`${color}.main`} fontWeight="bold">
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  const netPnL = results.final_balance - results.initial_balance;
  const netPnLPct = ((netPnL / results.initial_balance) * 100).toFixed(2);

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Backtest Results
        </Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
          <Chip label={results.config.name} color="primary" />
          <Chip label={results.config.symbol} variant="outlined" />
          <Chip label={results.config.timeframe} variant="outlined" />
          <Chip label={`${results.config.days} days`} variant="outlined" />
          <Chip
            label={results.config.multi_timeframes.join(', ')}
            icon={<ShowChartIcon />}
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Net P&L"
            value={`$${netPnL.toFixed(2)}`}
            subtitle={`${netPnLPct >= 0 ? '+' : ''}${netPnLPct}%`}
            color={netPnL >= 0 ? 'success' : 'error'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Win Rate"
            value={`${results.metrics.win_rate.toFixed(1)}%`}
            subtitle={`${results.metrics.winning_trades}/${results.metrics.total_trades} trades`}
            color={results.metrics.win_rate >= 50 ? 'success' : 'warning'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Profit Factor"
            value={results.metrics.profit_factor.toFixed(2)}
            subtitle={results.metrics.profit_factor >= 2 ? 'Excellent' : 'Good'}
            color={results.metrics.profit_factor >= 2 ? 'success' : 'warning'}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Sharpe Ratio"
            value={results.metrics.sharpe_ratio.toFixed(2)}
            subtitle="Risk-adjusted returns"
            color={results.metrics.sharpe_ratio >= 1.5 ? 'success' : 'warning'}
          />
        </Grid>
      </Grid>

      {/* Equity Curve */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <ShowChartIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Equity Curve
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={equityCurve}>
              <defs>
                <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1976d2" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#1976d2" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" label={{ value: 'Days', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Balance ($)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="balance"
                stroke="#1976d2"
                fillOpacity={1}
                fill="url(#colorBalance)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Performance Metrics
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Expected Payoff</TableCell>
                      <TableCell align="right">
                        ${results.metrics.expected_payoff.toFixed(2)} ({results.metrics.expected_payoff_pips.toFixed(1)} pips)
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Max Drawdown</TableCell>
                      <TableCell align="right">
                        ${results.metrics.max_drawdown.toFixed(2)} ({results.metrics.max_drawdown_pct.toFixed(2)}%)
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Recovery Factor</TableCell>
                      <TableCell align="right">{results.metrics.recovery_factor.toFixed(2)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Avg Win</TableCell>
                      <TableCell align="right">
                        ${results.metrics.avg_win.toFixed(2)} ({results.metrics.avg_win_pips.toFixed(1)} pips)
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Avg Loss</TableCell>
                      <TableCell align="right">
                        ${results.metrics.avg_loss.toFixed(2)} ({results.metrics.avg_loss_pips.toFixed(1)} pips)
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Avg R:R Ratio</TableCell>
                      <TableCell align="right">1:{results.metrics.avg_rr_ratio.toFixed(2)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Avg Trade Duration</TableCell>
                      <TableCell align="right">{results.metrics.avg_trade_duration}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Stress Test
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Max Consecutive Wins</TableCell>
                      <TableCell align="right">
                        <Chip label={results.metrics.max_consecutive_wins} color="success" size="small" />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Max Consecutive Losses</TableCell>
                      <TableCell align="right">
                        <Chip label={results.metrics.max_consecutive_losses} color="error" size="small" />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Largest Win</TableCell>
                      <TableCell align="right">${results.metrics.largest_win.toFixed(2)}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Largest Loss</TableCell>
                      <TableCell align="right">${results.metrics.largest_loss.toFixed(2)}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>

              <Box mt={3}>
                <Typography variant="subtitle2" gutterBottom>
                  Trade Distribution
                </Typography>
                <ResponsiveContainer width="100%" height={150}>
                  <BarChart data={tradeDistribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Multi-Timeframe Robustness */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Multi-Timeframe Robustness
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Timeframes Used
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {results.config.multi_timeframes.map((tf) => (
                    <Chip key={tf} label={tf} color="primary" size="small" />
                  ))}
                </Box>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Analysis Method
                </Typography>
                <Typography variant="body2">
                  Synchronous multi-timeframe with cached data
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Alignment
                </Typography>
                <Typography variant="body2">
                  All timeframes aligned to same timestamps
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default BacktestResults;
