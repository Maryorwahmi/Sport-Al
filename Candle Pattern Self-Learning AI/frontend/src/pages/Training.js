import React, { useState } from 'react';
import { Container, Typography, Card, CardContent, Grid, TextField, Button, CircularProgress, Box } from '@mui/material';
import { School } from '@mui/icons-material';
import apiService from '../services/api';

function Training() {
  const [config, setConfig] = useState({
    symbol: 'EURUSD',
    timeframe: 'H1',
    n_bars: 5000
  });
  const [training, setTraining] = useState(false);
  const [message, setMessage] = useState('');

  const startTraining = async () => {
    setTraining(true);
    setMessage('Training started in background...');
    try {
      const response = await apiService.trainModel(config);
      setMessage(`Training started for ${config.symbol} on ${config.timeframe}. Check logs for progress.`);
      // Wait a bit then check model info
      setTimeout(checkTrainingStatus, 5000);
    } catch (error) {
      console.error('Error starting training:', error);
      setMessage('Error starting training: ' + error.message);
      setTraining(false);
    }
  };

  const checkTrainingStatus = async () => {
    try {
      const response = await apiService.getModelInfo();
      if (response.data.model_info.pattern_engine_trained) {
        setMessage('Training complete! Model is ready for use.');
        setTraining(false);
      } else {
        setMessage('Training in progress... Please wait.');
        setTimeout(checkTrainingStatus, 5000);
      }
    } catch (error) {
      console.error('Error checking status:', error);
      setTraining(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        <School sx={{ fontSize: 40, mr: 2, verticalAlign: 'middle' }} />
        Model Training
      </Typography>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Training Configuration</Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Train the pattern recognition model on historical data. This process analyzes candlestick
            patterns and learns to predict future price movements.
          </Typography>

          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <TextField
                label="Symbol"
                value={config.symbol}
                onChange={(e) => setConfig({...config, symbol: e.target.value})}
                fullWidth
                disabled={training}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="Timeframe"
                value={config.timeframe}
                onChange={(e) => setConfig({...config, timeframe: e.target.value})}
                fullWidth
                disabled={training}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="Number of Bars"
                type="number"
                value={config.n_bars}
                onChange={(e) => setConfig({...config, n_bars: parseInt(e.target.value)})}
                fullWidth
                disabled={training}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={startTraining}
                disabled={training}
                fullWidth
                size="large"
              >
                {training ? <CircularProgress size={24} /> : 'Start Training'}
              </Button>
            </Grid>
          </Grid>

          {message && (
            <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="body2">{message}</Typography>
            </Box>
          )}

          <Box sx={{ mt: 3 }}>
            <Typography variant="caption" color="text.secondary">
              <strong>Note:</strong> Training typically takes 2-5 minutes depending on the amount of data.
              The model will learn to identify candlestick patterns and predict price movements.
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Container>
  );
}

export default Training;
