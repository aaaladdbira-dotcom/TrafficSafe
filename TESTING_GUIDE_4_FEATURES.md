# Quick Testing Guide - 4 New Features

## Pre-Flight Checklist

### 1. Install Dependencies
```bash
cd "c:\Users\ELITE\OneDrive\Bureau\traffic accident"
pip install -r requirements.txt
```

Expected output should show:
```
Successfully installed flask-socketio python-socketio python-engineio
```

### 2. Start the Application
```bash
python app.py
```

You should see in the console:
```
(socketio) INFO:  * Running on http://127.0.0.1:5001
(socketio) INFO: Socket.IO server started
```

If you see errors, check:
- ✅ Python 3.7+ installed
- ✅ All packages installed (pip install -r requirements.txt)
- ✅ Port 5001 is available
- ✅ Database file exists (instance/app.db)

### 3. Open Browser
Navigate to: `http://localhost:5001`

---

## Feature 1: Weather API Integration

### Test Location
Dashboard → Predictions tab

### What to Look For
1. **Forecast Cards:**
   - Shows 7-day accident risk forecast
   - Each day displays weather icon and risk level

2. **Risk Multipliers:**
   - Temperature impact (high heat = more risk)
   - Precipitation (rain = increased risk)
   - Wind speed effects

3. **Risk Factors Panel:**
   - Weather conditions breakdown
   - Temperature, humidity, wind metrics

### Test Steps
1. Click "Predictions" tab in dashboard
2. Scroll down to see "Risk Factors"
3. Look for weather icons and temperature readings
4. Should update based on current location weather

**Expected:** Weather data displays correctly, risk scores reflect weather conditions

---

## Feature 2: WebSocket Real-Time Updates

### Test Setup (Requires 2 Browser Windows)

#### Window 1: Dashboard
```
1. Open http://localhost:5001
2. Login with credentials
3. Go to Dashboard tab
4. Keep this window open and watch KPI cards
```

#### Window 2: Report Accident
```
1. Open http://localhost:5001 in new window
2. Go to "Report Accident" form
3. Keep this window ready
```

### Test Steps

**Step 1: Watch for Connection**
1. In Browser Console (F12):
   ```javascript
   console.log(window.realtimeClient.isConnected);
   // Should show: true (after 1-2 seconds)
   ```

**Step 2: Report High-Severity Accident**
1. Window 2: Fill accident form
   - Location: "Avenue Bourguiba"
   - Zone: "Tunis"
   - Cause: "Speeding"
   - Severity: **HIGH** (important!)
   - Description: "Test accident for WebSocket"
2. Click Submit

**Step 3: Observe Real-Time Update**
1. Window 1: Dashboard should show:
   - Toast notification: "New Accident: Avenue Bourguiba - high"
   - KPI cards update within 1-2 seconds
   - Total accidents count increases
   - High severity count increases

**Step 4: Low-Severity Test (Optional)**
1. Report another accident with severity "Low"
2. Window 1: Should NOT show toast (filter is high severity only)
3. But KPI cards should still update (if you're subscribed to all)

### Browser Console Debug
```javascript
// View real-time client status
window.realtimeClient.isConnected

// View active subscriptions
window.realtimeClient.subscriptions

// View raw socket events (enable debug)
window.realtimeClient = new RealtimeClient({ debug: true });
```

**Expected:** 
- Toast notifications appear within 1-2 seconds
- KPI cards update automatically
- No page refresh needed

---

## Feature 3: Voice Commands

### Test Location
Report Accident Form

### Browser Requirements
- ✅ Chrome (best support)
- ✅ Edge (good support)
- ✅ Safari (good support)
- ❌ Firefox (not supported)

### Test Steps

1. **Navigate to Form**
   - Go to "Report Accident" page
   - Scroll to "Description" field
   - Look for "🎤 Speak" button

2. **Click Voice Button**
   - Button should highlight with pulse animation
   - Status box should show "Listening..."

3. **Speak Clearly**
   - Say: "Car collision on Avenue Bourguiba, three vehicles involved"
   - Speak naturally at normal volume
   - Wait for interim results to appear

4. **Watch Results**
   - Status shows interim transcription in real-time
   - Confidence score displays (e.g., "95%")
   - Text is appended to textarea

5. **Submit**
   - Edit text if needed
   - Click "Submit Report"
   - Accident created with voice-transcribed description

### Troubleshooting Voice

**"No microphone found" error:**
- Check browser microphone permissions
- Settings → Privacy & Security → Microphone
- Ensure microphone works (test in Windows Sound settings)

**Text not appearing:**
- Check browser supports Web Speech API
- Try refreshing page and retry
- Check browser console for errors (F12)

**Wrong language:**
- Currently English (US) only
- Speak in English for best results

**No confidence score:**
- Score may not always display
- Try speaking more clearly
- Some browsers don't report confidence

**Test Cases:**
```
1. "Car accident Avenue Bourguiba"
   Expected: Simple text appended

2. "Multiple vehicle collision with high severity"
   Expected: Complete sentence appears

3. Mumble or unclear speech
   Expected: May show partial or incorrect text
   (User can manually edit)

4. Speak in French/Arabic
   Expected: English-only, may show wrong text
   (Feature constraint, by design)
```

**Expected:** Text appears in textarea, can be edited and submitted

---

## Feature 4: Enhanced Heatmap

### Test Location
Statistics Page → "Heatmap" Tab

### Test Steps

#### Step 1: View Default Heatmap
1. Go to Statistics
2. Click "Heatmap" tab (new tab with 🔥 icon)
3. You should see:
   - Map with accident density overlay
   - Color gradient from blue (low) to red (high)
   - List of top hotspots below
   - Filter controls at top

#### Step 2: Apply Filters
1. **Date Range:**
   - From: Leave empty (all data)
   - To: Leave empty (all data)
   - Or select specific date range

2. **Severity:**
   - Select "High" to see only critical accidents
   - Click "Apply Filters"
   - Heatmap should update immediately

3. **Governorate:**
   - Select "Tunis"
   - Click "Apply Filters"
   - Hotspot list updates with Tunis-only data

#### Step 3: Interact with Heatmap
1. **Zoom In/Out:**
   - Use mouse wheel
   - Heatmap becomes more detailed
   - Hotspots become more visible

2. **Pan:**
   - Click and drag map
   - Explore different regions

3. **Hotspot List:**
   - Shows top 10 accident locations
   - Each item displays:
     - Rank number
     - Location name
     - Accident count
     - Intensity bar (visual)
   - Click to see details

#### Step 4: Toggle Controls
1. **"Show" Button:**
   - Toggles heatmap visibility
   - Changes to "Hide" when hidden
   - Useful for comparing with raw map view

2. **"Legend" Button:**
   - Shows intensity scale (blue → red)
   - Shows max intensity number
   - Shows hotspot count

#### Step 5: Reset Filters
1. Click "Reset" button
2. All filters clear
3. Heatmap returns to full dataset

### Performance Testing

**With Sample Data:**
- Load time: Should be < 2 seconds
- Smooth transitions when filtering
- Map responsive on zoom/pan

**Expected:** 
- Heatmap renders with color gradient
- Hotspots list shows top locations
- Filters work correctly
- No performance lag

---

## Integration Testing

### Test Full Workflow
1. **Dashboard:** Monitor KPIs and predictions
2. **Report Form:** Use voice to describe accident
3. **WebSocket:** See real-time update in dashboard
4. **Heatmap:** View new accident in density visualization

### Test Steps
```
1. Go to Dashboard
2. Note current "Total Accidents" count
3. Go to Report Accident
4. Click voice button
5. Say: "Test accident in Sfax"
6. Submit (voice text auto-filled)
7. Return to Dashboard
8. Verify:
   - Toast notification appeared
   - Total count increased by 1
   - Map shows new pin (if map visible)
9. Go to Heatmap tab
10. Select "Sfax" governorate
11. Verify new accident appears in hotspots
```

---

## Browser Console Commands

### Check WebSocket Status
```javascript
// Check connection
window.realtimeClient.isConnected

// Check subscriptions
window.realtimeClient.subscriptions

// Manually subscribe to high-severity accidents
window.realtimeClient.subscribe('accidents', { severity: 'high' })

// Listen to events manually
window.realtimeClient.on('accident', (data) => {
  console.log('New accident:', data);
});

// Send ping to server
window.realtimeClient.ping()
```

### Check Voice Recognition
```javascript
// If VoiceCommandsHandler is loaded
console.log(window.VoiceCommandsHandler !== undefined)

// Check browser support
console.log(window.SpeechRecognition !== undefined)
```

### Check Heatmap
```javascript
// If AccidentHeatmap is loaded
console.log(window.AccidentHeatmap !== undefined)

// Check if Leaflet.heat is available
console.log(window.L.heatLayer !== undefined)
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| WebSocket not connecting | Check console for errors, ensure app restarted, check CORS settings |
| Voice button not working | Try Chrome, check microphone permission, refresh page |
| Heatmap not showing | Check `/api/v1/heatmap/data` endpoint returns data, check map container size |
| Real-time not updating | Check subscription filters match accident severity, check browser console |
| Toast notifications not showing | Check `/static/js/toast.js` is loaded, check browser console |
| Filters not applying | Check `/api/v1/heatmap/*` endpoints, check browser network tab |

---

## Success Criteria

### ✅ WebSocket Real-Time
- [ ] Toast notification appears within 2 seconds of accident submission
- [ ] Dashboard KPI cards update automatically
- [ ] No page refresh required

### ✅ Voice Commands
- [ ] Microphone permission requested on first use
- [ ] Text appears in textarea as spoken
- [ ] Status shows interim and final results
- [ ] Works in Chrome, Edge, Safari

### ✅ Heatmap Visualization
- [ ] Map renders with color gradient
- [ ] Hotspot list shows top 10 locations
- [ ] Filters (date, severity, governorate) work correctly
- [ ] Zoom/pan are smooth
- [ ] Performance is acceptable (< 2s load)

### ✅ Weather Integration
- [ ] Predictions tab shows weather icons
- [ ] Risk factors panel displays weather data
- [ ] 7-day forecast is visible

---

## Performance Baseline

| Feature | Expected Time | Notes |
|---------|---|---|
| WebSocket Update | < 2 seconds | Real-time push from server |
| Voice Recognition | < 5 seconds | Depends on speech duration |
| Heatmap Load | < 3 seconds | With < 1000 data points |
| Filter Apply | < 1 second | Client-side re-render |
| Map Zoom/Pan | < 100ms | Leaflet default performance |

---

## Next Test Phases

### Phase 2: Multi-User Testing
- Test WebSocket with 5+ simultaneous users
- Monitor server load
- Check memory usage

### Phase 3: Load Testing
- Test heatmap with 5000+ data points
- Test WebSocket with 100+ connected users
- Benchmark performance

### Phase 4: Mobile Testing
- Test voice on mobile (iOS Safari, Chrome Android)
- Test heatmap on small screens
- Test touch interactions

---

## Feedback & Debug Info to Collect

**If Something Breaks:**
1. Browser console (F12 → Console tab)
2. Network tab (F12 → Network tab)
3. Server logs (terminal running `python app.py`)
4. Steps to reproduce

**Useful Debug Info:**
```
- Browser type and version
- Operating system
- WebSocket connection status (from console)
- API response status (from Network tab)
- Error messages (from console)
- Time taken for operations
```

---

**Testing Date:** [Your Date]  
**Tester:** [Your Name]  
**Status:** Not Yet Tested

Once you complete testing, update this file with results and feedback!
