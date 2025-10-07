/**
 * Main App Component for SMC Forez Trading System
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  Button,
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ShowChartIcon from '@mui/icons-material/ShowChart';

import Dashboard from './pages/Dashboard';
import BacktestResults from './pages/BacktestResults';
import './App.css';

// Create custom theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    success: {
      main: '#4caf50',
    },
    error: {
      main: '#f44336',
    },
    background: {
      default: '#0a1929',
      paper: '#132f4c',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          {/* App Bar */}
          <AppBar position="static">
            <Toolbar>
              <ShowChartIcon sx={{ mr: 2 }} />
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                SMC Forez Trading System
              </Typography>
              <Button
                color="inherit"
                component={Link}
                to="/"
                startIcon={<DashboardIcon />}
              >
                Dashboard
              </Button>
              <Button
                color="inherit"
                component={Link}
                to="/backtest"
                startIcon={<AssessmentIcon />}
              >
                Backtest Results
              </Button>
            </Toolbar>
          </AppBar>

          {/* Main Content */}
          <Container maxWidth="xl" sx={{ flexGrow: 1, mt: 2 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/backtest" element={<BacktestResults />} />
            </Routes>
          </Container>

          {/* Footer */}
          <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', bgcolor: 'background.paper' }}>
            <Container maxWidth="xl">
              <Typography variant="body2" color="text.secondary" align="center">
                SMC Forez - Multi-Timeframe Smart Money Concepts Trading System
              </Typography>
              <Typography variant="caption" color="text.secondary" align="center" display="block">
                H4, H1, M15 Synchronous Analysis | Professional Confluence Model
              </Typography>
            </Container>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
