/**
 * Main Dashboard Component
 * Displays trading system overview, signals, and performance metrics
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  CircularProgress,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import { systemAPI, accountAPI, signalsAPI, positionsAPI, wsService } from '../services/api';
import SignalsList from '../components/SignalsList';
import PerformanceMetrics from '../components/PerformanceMetrics';
import MultiTimeframeView from '../components/MultiTimeframeView';

const Dashboard = () => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [account, setAccount] = useState(null);
  const [signals, setSignals] = useState([]);
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial data fetch
    fetchAllData();

    // Connect to WebSocket for real-time updates
    wsService.connect();
    wsService.addListener('SYSTEM_STATUS', handleSystemStatusUpdate);
    wsService.addListener('SIGNAL', handleNewSignal);

    // Set up polling for data refresh
    const interval = setInterval(fetchAllData, 30000); // Refresh every 30 seconds

    return () => {
      clearInterval(interval);
      wsService.disconnect();
    };
  }, []);

  const fetchAllData = async () => {
    try {
      const [statusData, accountData, signalsData, positionsData] = await Promise.all([
        systemAPI.getStatus(),
        accountAPI.getInfo(),
        signalsAPI.getRecent(10),
        positionsAPI.getOpen(),
      ]);

      setSystemStatus(statusData);
      setAccount(accountData);
      setSignals(signalsData);
      setPositions(positionsData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const handleSystemStatusUpdate = (data) => {
    setSystemStatus(data);
  };

  const handleNewSignal = (signal) => {
    setSignals((prev) => [signal, ...prev].slice(0, 10));
  };

  const handleStartSystem = async () => {
    try {
      await systemAPI.start();
      fetchAllData();
    } catch (error) {
      console.error('Error starting system:', error);
    }
  };

  const handleStopSystem = async () => {
    try {
      await systemAPI.stop();
      fetchAllData();
    } catch (error) {
      console.error('Error stopping system:', error);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  const isRunning = systemStatus?.status === 'RUNNING';

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box mb={3}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h4" component="h1" gutterBottom>
              SMC Forez Trading Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Multi-Timeframe Smart Money Concepts Trading System
            </Typography>
          </Grid>
          <Grid item xs={12} md={6} textAlign={{ xs: 'left', md: 'right' }}>
            <Button
              variant="contained"
              color={isRunning ? 'error' : 'success'}
              startIcon={isRunning ? <StopIcon /> : <PlayArrowIcon />}
              onClick={isRunning ? handleStopSystem : handleStartSystem}
              size="large"
            >
              {isRunning ? 'Stop System' : 'Start System'}
            </Button>
            <Chip
              label={systemStatus?.status || 'UNKNOWN'}
              color={isRunning ? 'success' : 'default'}
              sx={{ ml: 2 }}
            />
          </Grid>
        </Grid>
      </Box>

      {/* Account Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <AccountBalanceWalletIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Balance</Typography>
              </Box>
              <Typography variant="h4">${account?.balance?.toFixed(2) || '0.00'}</Typography>
              <Typography variant="body2" color="text.secondary">
                Equity: ${account?.equity?.toFixed(2) || '0.00'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Profit</Typography>
              </Box>
              <Typography
                variant="h4"
                color={account?.profit >= 0 ? 'success.main' : 'error.main'}
              >
                ${account?.profit?.toFixed(2) || '0.00'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {account?.profit >= 0 ? '+' : ''}
                {((account?.profit / account?.balance) * 100 || 0).toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <ShowChartIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Signals Today</Typography>
              </Box>
              <Typography variant="h4">{systemStatus?.signals_today || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                Last scan: {systemStatus?.last_scan ? 'Active' : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Typography variant="h6">Open Positions</Typography>
              </Box>
              <Typography variant="h4">{positions?.length || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                MT5: {systemStatus?.mt5_connected ? 'Connected' : 'Disconnected'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Multi-Timeframe View */}
      <Box mb={3}>
        <MultiTimeframeView />
      </Box>

      {/* Signals and Performance */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <SignalsList signals={signals} />
        </Grid>
        <Grid item xs={12} md={4}>
          <PerformanceMetrics />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
