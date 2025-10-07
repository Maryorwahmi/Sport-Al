/**
 * Settings Page
 * Configure trading system parameters and preferences
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Divider,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import RestoreIcon from '@mui/icons-material/Restore';
import { settingsAPI } from '../services/api';

const Settings = () => {
  const [settings, setSettings] = useState({
    trading: {
      risk_per_trade: 0.01,
      min_rr_ratio: 2.0,
      max_spread: 3.0,
      max_daily_trades: 5,
      max_open_trades: 3,
    },
    analysis: {
      swing_length: 15,
      fvg_min_size: 8.0,
      order_block_lookback: 25,
      liquidity_threshold: 0.15,
      min_confluence_score: 7,
    },
    backtest: {
      initial_balance: 10000.0,
      commission: 0.00007,
    },
    ui: {
      refresh_interval: 30,
      theme: 'light',
      notifications_enabled: true,
    }
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await settingsAPI.getSettings();
      if (data.settings) {
        setSettings(data.settings);
      }
    } catch (err) {
      console.error('Error loading settings:', err);
      // Use default settings if backend is not available
    }
  };

  const handleSaveSettings = async () => {
    try {
      setLoading(true);
      setSuccess(false);
      setError(null);
      
      await settingsAPI.updateSettings(settings);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('Error saving settings:', err);
      setError('Failed to save settings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetSettings = async () => {
    try {
      setLoading(true);
      setSuccess(false);
      setError(null);
      
      const data = await settingsAPI.resetSettings();
      if (data.settings) {
        setSettings(data.settings);
      }
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('Error resetting settings:', err);
      setError('Failed to reset settings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const updateSetting = (category, field, value) => {
    setSettings({
      ...settings,
      [category]: {
        ...settings[category],
        [field]: value,
      }
    });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        System Settings
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure trading system parameters and preferences
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Settings saved successfully!
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Trading Settings */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Trading Settings
        </Typography>
        <Divider sx={{ mb: 3 }} />
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Risk Per Trade (%)"
              type="number"
              inputProps={{ min: 0, max: 5, step: 0.1 }}
              value={settings.trading.risk_per_trade * 100}
              onChange={(e) => updateSetting('trading', 'risk_per_trade', parseFloat(e.target.value) / 100)}
              helperText="Percentage of account to risk per trade (0.1% - 5%)"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Minimum Risk:Reward Ratio"
              type="number"
              inputProps={{ min: 1, max: 10, step: 0.1 }}
              value={settings.trading.min_rr_ratio}
              onChange={(e) => updateSetting('trading', 'min_rr_ratio', parseFloat(e.target.value))}
              helperText="Minimum R:R ratio for trade entry (1.0 - 10.0)"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Maximum Spread (pips)"
              type="number"
              inputProps={{ min: 0, max: 10, step: 0.1 }}
              value={settings.trading.max_spread}
              onChange={(e) => updateSetting('trading', 'max_spread', parseFloat(e.target.value))}
              helperText="Maximum allowed spread for trade entry"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Max Daily Trades"
              type="number"
              inputProps={{ min: 1, max: 50 }}
              value={settings.trading.max_daily_trades}
              onChange={(e) => updateSetting('trading', 'max_daily_trades', parseInt(e.target.value))}
              helperText="Maximum number of trades per day"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Max Open Trades"
              type="number"
              inputProps={{ min: 1, max: 20 }}
              value={settings.trading.max_open_trades}
              onChange={(e) => updateSetting('trading', 'max_open_trades', parseInt(e.target.value))}
              helperText="Maximum concurrent open positions"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Analysis Settings */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Analysis Settings
        </Typography>
        <Divider sx={{ mb: 3 }} />
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Swing Length"
              type="number"
              inputProps={{ min: 5, max: 50 }}
              value={settings.analysis.swing_length}
              onChange={(e) => updateSetting('analysis', 'swing_length', parseInt(e.target.value))}
              helperText="Period for swing point detection (5-50)"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="FVG Minimum Size (pips)"
              type="number"
              inputProps={{ min: 1, max: 20, step: 0.5 }}
              value={settings.analysis.fvg_min_size}
              onChange={(e) => updateSetting('analysis', 'fvg_min_size', parseFloat(e.target.value))}
              helperText="Minimum Fair Value Gap size in pips"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Order Block Lookback"
              type="number"
              inputProps={{ min: 10, max: 100 }}
              value={settings.analysis.order_block_lookback}
              onChange={(e) => updateSetting('analysis', 'order_block_lookback', parseInt(e.target.value))}
              helperText="Number of candles to look back for order blocks"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Liquidity Threshold"
              type="number"
              inputProps={{ min: 0.05, max: 0.5, step: 0.05 }}
              value={settings.analysis.liquidity_threshold}
              onChange={(e) => updateSetting('analysis', 'liquidity_threshold', parseFloat(e.target.value))}
              helperText="Threshold for liquidity zone detection (0.05-0.5)"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Minimum Confluence Score"
              type="number"
              inputProps={{ min: 3, max: 15 }}
              value={settings.analysis.min_confluence_score}
              onChange={(e) => updateSetting('analysis', 'min_confluence_score', parseInt(e.target.value))}
              helperText="Minimum confluence score for signal generation"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Backtest Settings */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Backtest Settings
        </Typography>
        <Divider sx={{ mb: 3 }} />
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Initial Balance ($)"
              type="number"
              inputProps={{ min: 1000, max: 1000000, step: 1000 }}
              value={settings.backtest.initial_balance}
              onChange={(e) => updateSetting('backtest', 'initial_balance', parseFloat(e.target.value))}
              helperText="Starting balance for backtests"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Commission (per trade)"
              type="number"
              inputProps={{ min: 0, max: 0.001, step: 0.00001 }}
              value={settings.backtest.commission}
              onChange={(e) => updateSetting('backtest', 'commission', parseFloat(e.target.value))}
              helperText="Trading commission in decimal (e.g., 0.00007 = 0.7 pips)"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* UI Settings */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          UI Settings
        </Typography>
        <Divider sx={{ mb: 3 }} />
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Refresh Interval (seconds)"
              type="number"
              inputProps={{ min: 10, max: 300, step: 10 }}
              value={settings.ui.refresh_interval}
              onChange={(e) => updateSetting('ui', 'refresh_interval', parseInt(e.target.value))}
              helperText="Dashboard auto-refresh interval"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Theme</InputLabel>
              <Select
                value={settings.ui.theme}
                label="Theme"
                onChange={(e) => updateSetting('ui', 'theme', e.target.value)}
              >
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="dark">Dark</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.ui.notifications_enabled}
                  onChange={(e) => updateSetting('ui', 'notifications_enabled', e.target.checked)}
                />
              }
              label="Enable Notifications"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Action Buttons */}
      <Box display="flex" gap={2}>
        <Button
          variant="contained"
          size="large"
          startIcon={<SaveIcon />}
          onClick={handleSaveSettings}
          disabled={loading}
        >
          Save Settings
        </Button>
        
        <Button
          variant="outlined"
          size="large"
          startIcon={<RestoreIcon />}
          onClick={handleResetSettings}
          disabled={loading}
        >
          Reset to Defaults
        </Button>
      </Box>
    </Box>
  );
};

export default Settings;
