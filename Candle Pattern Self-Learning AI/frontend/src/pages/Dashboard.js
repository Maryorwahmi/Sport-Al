import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Card, CardContent, Grid, Button, CircularProgress } from '@mui/material';
import { TrendingUp, Analytics, Assessment } from '@mui/icons-material';
import apiService from '../services/api';

function Dashboard() {
  const [health, setHealth] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadHealth();
    loadModelInfo();
  }, []);

  const loadHealth = async () => {
    try {
      const response = await apiService.healthCheck();
      setHealth(response.data);
    } catch (error) {
      console.error('Error loading health:', error);
    }
  };

  const loadModelInfo = async () => {
    try {
      const response = await apiService.getModelInfo();
      setModelInfo(response.data);
    } catch (error) {
      console.error('Error loading model info:', error);
    }
  };

  const scanMarkets = async () => {
    setLoading(true);
    try {
      const response = await apiService.scanOpportunities({
        symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
      });
      setOpportunities(response.data.opportunities);
    } catch (error) {
      console.error('Error scanning:', error);
    }
    setLoading(false);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        <TrendingUp sx={{ fontSize: 40, mr: 2, verticalAlign: 'middle' }} />
        Trading Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">System Status</Typography>
              <Typography variant="body2">
                Status: {health?.status || 'Unknown'}
              </Typography>
              <Typography variant="body2">
                Model Trained: {health?.pattern_engine_trained ? '✓ Yes' : '✗ No'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Model Info</Typography>
              <Typography variant="body2">
                Trained: {modelInfo?.model_info?.pattern_engine_trained ? 'Yes' : 'No'}
              </Typography>
              <Typography variant="body2">
                Patterns: {modelInfo?.model_info?.pattern_stats?.n_patterns || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Quick Actions</Typography>
              <Button 
                variant="contained" 
                onClick={scanMarkets} 
                disabled={loading}
                fullWidth
                sx={{ mt: 1 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Scan Markets'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <Analytics sx={{ mr: 1 }} />
                Trading Opportunities ({opportunities.length})
              </Typography>
              {opportunities.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No opportunities found. Click "Scan Markets" to search.
                </Typography>
              ) : (
                opportunities.map((opp, idx) => (
                  <Box key={idx} sx={{ p: 2, mb: 2, border: '1px solid #ddd', borderRadius: 1 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={3}>
                        <Typography variant="subtitle2">{opp.symbol}</Typography>
                        <Typography variant="body2" color={opp.action === 'BUY' ? 'success.main' : 'error.main'}>
                          {opp.action}
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="caption">Entry</Typography>
                        <Typography variant="body2">{opp.entry_price?.toFixed(5)}</Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="caption">SL / TP</Typography>
                        <Typography variant="body2">
                          {opp.stop_loss?.toFixed(5)} / {opp.take_profit?.toFixed(5)}
                        </Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="caption">Confluence</Typography>
                        <Typography variant="body2">{(opp.confluence_score * 100).toFixed(0)}%</Typography>
                      </Grid>
                    </Grid>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Dashboard;
