import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container, Button, Box, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { TrendingUp, Assessment, School } from '@mui/icons-material';
import Dashboard from './pages/Dashboard';
import Backtest from './pages/Backtest';
import Training from './pages/Training';
import './App.css';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <TrendingUp sx={{ mr: 2 }} />
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Candle Pattern Self-Learning AI
              </Typography>
              <Button color="inherit" component={Link} to="/">
                Dashboard
              </Button>
              <Button color="inherit" component={Link} to="/training">
                <School sx={{ mr: 1 }} />
                Training
              </Button>
              <Button color="inherit" component={Link} to="/backtest">
                <Assessment sx={{ mr: 1 }} />
                Backtest
              </Button>
            </Toolbar>
          </AppBar>

          <Container>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/training" element={<Training />} />
              <Route path="/backtest" element={<Backtest />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
