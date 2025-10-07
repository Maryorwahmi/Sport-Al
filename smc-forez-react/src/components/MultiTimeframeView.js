/**
 * MultiTimeframeView Component
 * Displays trend and signal alignment across multiple timeframes
 */
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  Chip,
  Paper,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import RemoveIcon from '@mui/icons-material/Remove';

const MultiTimeframeView = () => {
  // Mock data - replace with actual data from API
  const timeframes = [
    {
      name: 'H4',
      trend: 'UPTREND',
      strength: 0.75,
      signal: 'BUY',
      confluence: 12,
      weight: '50%',
    },
    {
      name: 'H1',
      trend: 'UPTREND',
      strength: 0.68,
      signal: 'BUY',
      confluence: 10,
      weight: '30%',
    },
    {
      name: 'M15',
      trend: 'UPTREND',
      strength: 0.85,
      signal: 'BUY',
      confluence: 8,
      weight: '20%',
    },
  ];

  const getTrendIcon = (trend) => {
    if (trend === 'UPTREND') return <TrendingUpIcon color="success" />;
    if (trend === 'DOWNTREND') return <TrendingDownIcon color="error" />;
    return <RemoveIcon color="disabled" />;
  };

  const getTrendColor = (trend) => {
    if (trend === 'UPTREND') return 'success';
    if (trend === 'DOWNTREND') return 'error';
    return 'default';
  };

  const getSignalColor = (signal) => {
    if (signal === 'BUY') return 'success';
    if (signal === 'SELL') return 'error';
    return 'default';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Multi-Timeframe Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>
          Synchronized timeframe analysis with weighted confluence
        </Typography>

        <Grid container spacing={2}>
          {timeframes.map((tf) => (
            <Grid item xs={12} md={4} key={tf.name}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="h5" fontWeight="bold">
                    {tf.name}
                  </Typography>
                  <Chip label={`Weight: ${tf.weight}`} size="small" variant="outlined" />
                </Box>

                <Box mb={2}>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    {getTrendIcon(tf.trend)}
                    <Chip
                      label={tf.trend}
                      color={getTrendColor(tf.trend)}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Strength: {(tf.strength * 100).toFixed(0)}%
                  </Typography>
                </Box>

                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Signal
                  </Typography>
                  <Chip label={tf.signal} color={getSignalColor(tf.signal)} />
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Confluence Score
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {tf.confluence}/15
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>

        <Box mt={2} p={2} bgcolor="primary.light" borderRadius={1}>
          <Typography variant="body2" fontWeight="medium">
            ✓ All timeframes aligned - HIGH CONFIDENCE signal
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Weighted score: 75% (H4: 50%, H1: 30%, M15: 20%)
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default MultiTimeframeView;
