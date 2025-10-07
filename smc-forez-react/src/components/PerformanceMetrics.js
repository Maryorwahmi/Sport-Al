/**
 * PerformanceMetrics Component
 * Displays key performance indicators
 */
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Divider,
  LinearProgress,
} from '@mui/material';

const PerformanceMetrics = () => {
  // Mock data - replace with actual data from API
  const metrics = {
    winRate: 58.5,
    profitFactor: 2.3,
    sharpeRatio: 1.8,
    maxDrawdown: 8.2,
    recoveryFactor: 3.5,
    avgTradeDuration: '4h 23m',
    consecutiveLosses: 3,
  };

  const MetricItem = ({ label, value, color = 'primary', showProgress = false }) => (
    <Box mb={2}>
      <Box display="flex" justifyContent="space-between" mb={0.5}>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="body2" fontWeight="medium">
          {value}
        </Typography>
      </Box>
      {showProgress && (
        <LinearProgress
          variant="determinate"
          value={parseFloat(value)}
          color={color}
          sx={{ height: 6, borderRadius: 3 }}
        />
      )}
    </Box>
  );

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Performance Metrics
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <MetricItem
          label="Win Rate"
          value={`${metrics.winRate}%`}
          color={metrics.winRate >= 50 ? 'success' : 'warning'}
          showProgress
        />

        <MetricItem label="Profit Factor" value={metrics.profitFactor.toFixed(2)} />

        <MetricItem label="Sharpe Ratio" value={metrics.sharpeRatio.toFixed(2)} />

        <MetricItem
          label="Max Drawdown"
          value={`${metrics.maxDrawdown}%`}
          color="error"
          showProgress={false}
        />

        <MetricItem label="Recovery Factor" value={metrics.recoveryFactor.toFixed(2)} />

        <MetricItem label="Avg Trade Duration" value={metrics.avgTradeDuration} />

        <MetricItem
          label="Max Consecutive Losses"
          value={metrics.consecutiveLosses}
          color="error"
        />

        <Box mt={3}>
          <Typography variant="caption" color="text.secondary">
            Last updated: {new Date().toLocaleTimeString()}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default PerformanceMetrics;
