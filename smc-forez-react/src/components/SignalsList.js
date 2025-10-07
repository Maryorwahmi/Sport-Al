/**
 * SignalsList Component
 * Displays recent trading signals with quality indicators
 */
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Box,
  Paper,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import RemoveIcon from '@mui/icons-material/Remove';

const SignalsList = ({ signals = [] }) => {
  const getSignalIcon = (type) => {
    const signalType = typeof type === 'string' ? type.toUpperCase() : type;
    
    if (signalType === 'BUY') {
      return <TrendingUpIcon color="success" />;
    } else if (signalType === 'SELL') {
      return <TrendingDownIcon color="error" />;
    }
    return <RemoveIcon color="disabled" />;
  };

  const getSignalColor = (type) => {
    const signalType = typeof type === 'string' ? type.toUpperCase() : type;
    
    if (signalType === 'BUY') return 'success';
    if (signalType === 'SELL') return 'error';
    return 'default';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Recent Signals
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Time</TableCell>
                <TableCell>Symbol</TableCell>
                <TableCell>Signal</TableCell>
                <TableCell align="right">Entry</TableCell>
                <TableCell align="right">S/L</TableCell>
                <TableCell align="right">T/P</TableCell>
                <TableCell align="center">R:R</TableCell>
                <TableCell align="center">Confidence</TableCell>
                <TableCell align="center">TF</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {signals.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No signals available
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                signals.map((signal, index) => (
                  <TableRow key={signal.id || index} hover>
                    <TableCell>{formatTime(signal.timestamp)}</TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {signal.symbol}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        {getSignalIcon(signal.type)}
                        <Chip
                          label={signal.type}
                          color={getSignalColor(signal.type)}
                          size="small"
                        />
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {signal.entry_price?.toFixed(5) || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {signal.stop_loss?.toFixed(5) || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {signal.take_profit?.toFixed(5) || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`1:${signal.risk_reward_ratio?.toFixed(1) || 'N/A'}`}
                        color={signal.risk_reward_ratio >= 2 ? 'success' : 'default'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`${(signal.confidence * 100 || 0).toFixed(0)}%`}
                        color={getConfidenceColor(signal.confidence)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Box display="flex" flexWrap="wrap" gap={0.5} justifyContent="center">
                        {signal.timeframes?.map((tf, i) => (
                          <Chip
                            key={i}
                            label={tf}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem', height: '18px' }}
                          />
                        ))}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

export default SignalsList;
