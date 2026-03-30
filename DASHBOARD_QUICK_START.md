# CKD-CI Dashboard: Quick Start Guide

## 🚀 Getting Started

### 1. Start the API
```bash
cd "c:\Users\hp\OneDrive\Documents\Downloads\CKD-CI (2)\CKD-CI"
.venv312\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start the Dashboard
```bash
# New terminal
cd "c:\Users\hp\OneDrive\Documents\Downloads\CKD-CI (2)\CKD-CI"
.venv312\Scripts\Activate.ps1
streamlit run dashboard.py --server.port 8501
```

### 3. Open in Browser
```
http://127.0.0.1:8501
```

---

## 🔐 Login

**Default Credentials:**
- **Email:** admin@example.com
- **Password:** password

**Available Roles:**
- Admin
- Doctor
- Nurse (lab_technician treated as nurse)
- ML Engineer

---

## 💡 Feature Highlights

### Professional Medical UI
✅ Clinical color scheme (blue, green, yellow, orange, red)
✅ Medical status badges
✅ Risk class indicators with icons
✅ Professional card shadows and spacing
✅ Accessibility-friendly high-contrast colors

### Model Version Management
✅ Automatic version resolution from registry
✅ Fallback handling for "unknown" versions
✅ Version displayed in all prediction views
✅ Version normalization consistent across dashboard

### Risk Progression Detection
✅ Tracks patient risk over time
✅ Detects escalation (risk increase)
✅ Generates clinical alerts
✅ Displays risk trend graphs
✅ Recommends actions based on escalation

### Production ML Features
✅ Prediction confidence tracking
✅ Model performance snapshots
✅ Feature drift detection
✅ Prediction audit trail
✅ System health monitoring

---

## 📱 Using Each Dashboard Mode

### Single Patient
1. Select "Single Patient" from top radio buttons
2. Enter patient demographics in left sidebar
3. OR: Select preset (Normal/Moderate/High)
4. Click "Run Prediction"
5. View:
   - Large risk badge with clinical color
   - Confidence percentage
   - Model version (resolved automatically)
   - Clinical Decision Support interpretation
   - Risk drivers (feature importance)
   - Professional prediction card
   - Download PDF report

**Model Version Fix:**
- Runtime returns "unknown"? → AUTO resolved to active model version
- All versions normalized in display

**Risk Escalation Example:**
- If patient's risk increased (e.g., Low→Moderate)
- System detects escalation
- Shows: "⚠️ RISK ESCALATION DETECTED"
- Displays previous vs current risk
- Recommends follow-up actions

### Batch CSV
1. Select "Batch CSV" mode
2. Upload CSV with required columns
3. Watch progress bar animate
4. See statistics: total processed, high-risk count, avg confidence
5. Download enriched CSV with clinical labels

### Command Center
1. View KPI cards (volume, critical patients, version, accuracy)
2. See prediction trend (time series chart)
3. View risk distribution (pie chart)
4. Analyze confidence distribution (histogram)
5. Review performance metrics

### ML Monitoring
1. Check model health status
2. Review confidence drift detection
3. Analyze feature drift table (mean-shift per feature)
4. View prediction distribution charts

### Risk Progression (Longitudinal Tracking)
1. Select patient by ID
2. View:
   - eGFR timeline (trend chart)
   - Creatinine timeline (trend chart)
   - Risk progression (trend chart)
   - Escalation history (if any)

### Alerts
- See hospital-style alerts (INFO/WARNING/CRITICAL)
- Color-coded by severity
- Includes escalation warnings

### Model Governance
- View model registry table
- Activate/Deactivate models
- Compare model versions (bar chart showing metrics)

---

## 🎯 Key Features in Action

### Feature 1: Model Version Resolution
```
Scenario: Prediction API returns model_version = "unknown"

Result: Dashboard automatically resolves to active model version
Display: "1.2.3" (from registry, not "unknown")
```

### Feature 2: Risk Escalation Detection
```
Scenario: Patient's risk increases from Low (1) to Moderate (2)

Result: 
- Alert triggered: "⚠️ RISK ESCALATION DETECTED"
- Shows: Previous: Low Risk → Current: Moderate Risk
- Color: Orange badge (Attention level)
- Recommends: Nephrology consult, cognitive testing, follow-up labs
```

### Feature 3: Professional UI Styling
```
Before: Plain text "High Risk"
After: 
- 🚨 Red badge with clinical meaning
- "High Risk (Severe CKD/Cognitive decline likely)"
- Bordered card with gradient background
- Appropriate spacing and typography
```

### Feature 4: Batch Progress
```
Status: ▓▓▓▓▓░░░░░░ 50%
Message: "Preparing batch queue: 250/500"
Features: Real-time progress feedback with visual bar
```

---

## 🔍 Verifying Everything Works

### 1. Check UI Theme Applied
✅ Dashboard loads with medical blue color
✅ Sidebar shows hospital-style layout
✅ Cards have shadows and borders

### 2. Test Model Version
✅ Login → View prediction history
✅ Check column "Model Version"
✅ Verify no "unknown" values

### 3. Test Single Patient
1. Login
2. Select preset "High"
3. Click "Apply Preset"
4. Click "Run Prediction"
5. Verify:
   - Prediction sends with resolved version
   - Result shows large red badge (High Risk)
   - Version shows as resolved (e.g., "1.2.3")
   - Clinical label shows (not "3", but "High Risk")

### 4. Test Risk Escalation
1. Command Center mode
2. Check "Prediction Logs"
3. Filter for same patient
4. Look for consecutive predictions
5. If risk increased → Alert badge should appear

### 5. Check System Health
1. Select "System Health" mode
2. See API status, DB status, Model status
3. All should show "RUNNING" or "HEALTHY"

---

## 🎨 Medical Color Reference

| Status | Color | RGB | Meaning |
|--------|-------|-----|---------|
| **Stable** | Green | #2E7D32 | Safe (eGFR > 60) |
| **Monitor** | Yellow | #F9A825 | Caution (eGFR 45-59) |
| **Attention** | Orange | #FB8C00 | Warning (eGFR 30-44) |
| **Critical** | Red | #C62828 | Danger (eGFR < 30) |
| **Primary** | Blue | #1565C0 | Trust/Clinical |

---

## 🚨 Troubleshooting

### Dashboard shows "unknown" for model version
**Solution:**
1. Check `GET /models` returns active model
2. Restart Streamlit
3. Clear browser cache
4. Login again

### Risk escalation not triggering
**Check:**
1. Predictions have same patient_id
2. Risk class actually increased (e.g., 1→2, 2→3)
3. Predictions within 7 days

### Clinical colors not appearing
**Fix:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Restart Streamlit
3. Check internet connection for CSS loading

### Batch CSV shows error "Missing required columns"
**Check:**
1. CSV has: age, gender, bmi, egfr, creatinine, bun, uacr, hemoglobin, albumin, potassium, phosphorus, calcium, systolic_bp, diabetes, hypertension, cvd
2. Column names exact (lowercase)
3. No extra columns OK, but missing columns will error
4. Example: `batch_predictions.csv` file provided

---

## 📊 Data Entry Tips

### Patient Presets (Streamlit sidebar)
- **Normal**: 54yo, eGFR 96, all labs normal → No Risk
- **Moderate**: 67yo, eGFR 58, diabetes/HTN → Moderate Risk
- **High**: 78yo, eGFR 26, multiple comorbidities → High Risk

### Manual Entry Ranges
|Field|Min|Max|Clinical Note|
|-----|---|---|---|
|Age|20|95||
|eGFR|0|150|<30 = severe CKD|
|Creatinine|0.2|10|>2.0 = impaired function|
|Systolic BP|70|260|>150 consider hypertension|
|Albumin|1.5|6|<3.5 = malnutrition|

### Pro Tips
✅ Use presets to understand system behavior
✅ Try "High" preset first to see escalation alerts
✅ Check historical predictions for same patient
✅ Use batch CSV for volume testing

---

## 📋 Common Workflows

### Workflow 1: Single Patient Prediction
```
1. Login
2. Single Patient mode
3. Use "High" preset
4. Run Prediction
5. Review clinical card
6. Check risk drivers
7. Download PDF
```

### Workflow 2: Monitor Patient Trends
```
1. Login
2. Longitudinal Tracking mode
3. Select patient ID
4. Review eGFR/creatinine/risk charts
5. Check escalation history
6. Recommend follow-up timing
```

### Workflow 3: Model Governance
```
1. Admin login
2. Model Governance mode
3. View registry table
4. Compare versions
5. Activate new model if needed
```

### Workflow 4: System Health Check
```
1. Any login
2. System Health mode
3. Verify API, DB, Model running
4. Return to appropriate dashboard view
```

---

## 🔧 Advanced: API Testing

### Test Model Version Resolution
```bash
curl -X POST http://127.0.0.1:8000/models/resolve-version \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"runtime_version": "unknown", "patient_id": 123}'
```

### Test Risk Progression
```bash
curl http://127.0.0.1:8000/patients/123/risk-progression \
  -H "Authorization: Bearer {token}"
```

### Test Drift Detection
```bash
curl http://127.0.0.1:8000/clinical/drift \
  -H "Authorization: Bearer {token}"
```

---

## 📞 Support

**Issue**: Model version not resolving
- Check: `/models` endpoint returns active model
- Solution: Restart API server

**Issue**: Risk escalation not alerting
- Check: Two predictions for same patient
- Solution: Try "High" preset twice

**Issue**: UI colors wrong
- Check: Application of theme CSS
- Solution: Hard refresh browser + restart Streamlit

---

## ✨ What's New vs. Previous Version

| Feature | Before | After |
|---------|--------|-------|
| Model Version | Often "unknown" | Always resolved |
| UI Colors | Basic colors | Medical palette |
| Risk Tracking | None | Full progression detection |
| Professional Badges | None | Clinical status bage with icons |
| Escalation Alerts | None | Real-time escalation detection |
| Error Handling | Crashes | Graceful with notifications |
| Loading States | None | Spinners + progress bars |
| Report Generation | Basic | Professional PDF |
| Theme | Default | Healthcare-specific |

---

**Dashboard Version**: 2.0 (Production-Grade)  
**Last Updated**: March 30, 2026  
**Status**: Ready for Testing
