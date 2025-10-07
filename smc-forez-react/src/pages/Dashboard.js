/**
 * Main Dashboard Component
 * Displays live signals, performance metrics, and system status
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import SignalCellularAltIcon from '@mui/icons-material/SignalCellularAlt';
import AssessmentIcon from '@mui/icons-material/Assessment';
import { signalsAPI, statsAPI, healthCheck } from '../services/api';

const Dashboard = () => {
  const [signals, setSignals] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [systemStatus, setSystemStatus] = useState('checking');

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Check system health
      try {
        await healthCheck();
        setSystemStatus('healthy');
      } catch {
        setSystemStatus('offline');
      }

      // Load signals and stats
      const [signalsData, statsData] = await Promise.all([
        signalsAPI.getCurrentSignals(),
        statsAPI.getPerformanceStats()
      ]);

      setSignals(signalsData.signals || []);
      setStats(statsData);
      setError(null);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data. Please check if the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const getSignalTypeColor = (type) => {
    return type === 'BUY' ? 'success' : 'error';
  };

  const getQualityColor = (quality) => {
    if (quality >= 0.85) return 'success';
    if (quality >= 0.70) return 'info';
    return 'warning';
  };

  const getQualityLabel = (quality) => {
    if (quality >= 0.85) return 'Institutional';
    if (quality >= 0.70) return 'Professional';
    return 'Standard';
  };

  const formatPrice = (price) => {
    return price ? price.toFixed(5) : 'N/A';
  };

  const formatPercentage = (value) => {
    return value ? `${(value * 100).toFixed(1)}%` : 'N/A';
  };

  if (loading && !signals.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          SMC-Forez-H4 Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Smart Money Concepts Multi-Timeframe Analysis
        </Typography>
      </Box>

      {/* System Status */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {systemStatus === 'offline' && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Backend system is offline. Please start the API server.
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Active Signals
                  </Typography>
                  <Typography variant="h4">
                    {signals.length}
                  </Typography>
                </Box>
                <SignalCellularAltIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Win Rate
                  </Typography>
                  <Typography variant="h4">
                    {stats?.win_rate ? formatPercentage(stats.win_rate) : 'N/A'}
                  </Typography>
                </Box>
                <AssessmentIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Profit Factor
                  </Typography>
                  <Typography variant="h4">
                    {stats?.profit_factor?.toFixed(2) || 'N/A'}
                  </Typography>
                </Box>
                <TrendingUpIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Total Trades
                  </Typography>
                  <Typography variant="h4">
                    {stats?.total_trades || 0}
                  </Typography>
                </Box>
                <AssessmentIcon color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Live Signals Table */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Live Trading Signals
        </Typography>
        
        {signals.length === 0 ? (
          <Alert severity="info">
            No active signals at the moment. The system is monitoring markets for opportunities.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Time</TableCell>
                  <TableCell>Symbol</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Entry</TableCell>
                  <TableCell>Stop Loss</TableCell>
                  <TableCell>Take Profit</TableCell>
                  <TableCell>R:R</TableCell>
                  <TableCell>Quality</TableCell>
                  <TableCell>Timeframe</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {signals.map((signal, index) => (
                  <TableRow key={index} hover>
                    <TableCell>
                      {new Date(signal.timestamp).toLocaleTimeString()}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {signal.symbol}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={signal.signal_type}
                        color={getSignalTypeColor(signal.signal_type)}
                        size="small"
                        icon={signal.signal_type === 'BUY' ? 
                          <TrendingUpIcon /> : <TrendingDownIcon />}
                      />
                    </TableCell>
                    <TableCell>{formatPrice(signal.entry_price)}</TableCell>
                    <TableCell>{formatPrice(signal.stop_loss)}</TableCell>
                    <TableCell>{formatPrice(signal.take_profit)}</TableCell>
                    <TableCell>
                      <Typography variant="body2" color="success.main">
                        1:{signal.rr_ratio?.toFixed(1) || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={getQualityLabel(signal.quality_score)}
                        color={getQualityColor(signal.quality_score)}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{signal.timeframe || 'H1'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
};

export default Dashboard;
