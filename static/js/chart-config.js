Chart.defaults.font.family = "Inter, system-ui, -apple-system, 'Segoe UI', Roboto";
Chart.defaults.color = "#374151";

// Centralized chart theme and palette
const ChartTheme = {
  palette: {
    primaryA: '#1d4ed8', // royal blue
    primaryB: '#0ea5e9', // azure
    accent1: '#f59e0b', // amber
    accent2: '#ef4444', // red
    success: '#10b981', // emerald
    neutral: '#475569'
  },
  // Pre-built arrays for categorical charts
  colors: {
    severity: ['#ef4444', '#f59e0b', '#10b981', '#1d4ed8'],
    cause: '#0ea5e9',
    line: ['#1d4ed8', '#0ea5e9'],
  },
  tooltip: {
    backgroundColor: "rgba(255,255,255,0.98)",
    titleColor: "#0f172a",
    bodyColor: "#475569",
    borderColor: "rgba(15,23,42,0.06)",
    borderWidth: 1,
    padding: 10,
    displayColors: false,
    titleFont: { weight: '600' },
    bodyFont: { weight: '400' }
  },
  animation: {
    duration: 600,
    easing: "cubicBezier(.2,.8,.2,1)"
  },
  // common options for responsive layouts
  defaults: {
    maintainAspectRatio: false,
  }
};
