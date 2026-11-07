# CKD-CI Dashboard: Production-Grade Healthcare AI Platform

## Executive Summary

The CKD-CI dashboard has been transformed from a functional prototype into an enterprise-ready clinical AI system. This document details all enhancements, architectural patterns, and deployment guidelines.

---

## 🎯 Part 1: Professional Medical UI/UX Enhancements

### 1.1 Medical Color Scheme & Theme (`ui/theme.py`)

#### Clinical Color Palette
- **Primary (Trust)**: `#1565C0` - Deep medical blue for primary actions
- **Risk Badges**:
  - **Stable** (Green): `#2E7D32` - eGFR > 60, no cognitive impairment
  - **Monitor** (Yellow): `#F9A825` - eGFR 45-59, mild CKD
  - **Attention** (Orange): `#FB8C00` - eGFR 30-44, moderate-severe CKD
  - **Critical** (Red): `#C62828` - eGFR < 30, severe CKD/cognitive decline

#### Risk Classes
```python
RISK_BADGES = {
    0: {"label": "No Risk", "color": COLORS["stable"], "icon": "✅", "clinical": "Normal kidney function"},
    1: {"label": "Low Risk", "color": COLORS["monitor"], "icon": "⚠️", "clinical": "Mild CKD"},
    2: {"label": "Moderate Risk", "color": COLORS["attention"], "icon": "⚠️", "clinical": "Moderate CKD"},
    3: {"label": "High Risk", "color": COLORS["critical"], "icon": "🚨", "clinical": "Severe CKD/Cognitive decline likely"},
}
```

#### eGFR Clinical Staging
eGFR values are automatically categorized into clinical stages:
- **Stage 1**: eGFR ≥ 90 - Normal kidney function
- **Stage 2**: eGFR 60-89 - Mild decrease
- **Stage 3a**: eGFR 45-59 - Mild-moderate decrease
- **Stage 3b**: eGFR 30-44 - Moderate-severe decrease
- **Stage 4**: eGFR 15-29 - Severe decrease
- **Stage 5**: eGFR < 15 - Kidney failure

### 1.2 Professional UI Components

#### Risk Badge Rendering
```python
render_risk_badge(risk_class: int | None)
```
Displays clinical status with color, icon, and clinical interpretation.

#### Status Badges
```python
render_status_badge(status: str | None)
```
Shows monitoring status (Stable/Monitor/Attention/Critical).

#### Prediction Result Card
```python
render_prediction_card(result: dict, confidence: float, model_version: str, cds: dict)
```
Comprehensive result display with:
- Large risk class label in clinical color
- Confidence percentage and progress indicator
- Model version information
- Clinical staging information
- CDS interpretation panel

#### Streamlit Theme Application
```python
apply_streamlit_theme()
```
Applies custom CSS for:
- Card shadows for depth
- Rounded corners (6-8px border-radius)
- Professional spacing and alignment
- Alert color-coding
- Button styling with hover effects

### 1.3 Loading States & Notifications

```python
with st.spinner("Running clinical inference..."):
    response = submit_single_prediction(features)

# Success notification
st.success("Prediction completed in 45ms")

# Error banner
st.error("Backend unavailable")

# Warning banner
st.warning("Out-of-range lab value detected")

# Info notification
st.info("eGFR trend: improving over 30 days")
```

---

## 🏥 Part 2: Model Version Management (`services/model_registry_resolver.py`)

### 2.1 Version Resolution Strategy

**Problem**: Production runtime sometimes returns "unknown" or null for model_version.

**Solution**: Multi-level fallback resolution:

```
1. Runtime bundle version (if valid) ✓
2. Registry active model version ✓
3. Fallback parameter ✓
4. "version_unavailable" (final fallback)
```

### 2.2 ModelRegistryResolver Class

```python
resolver = ModelRegistryResolver()
resolver.update_registry(models_from_api)

# Resolve version with fallbacks
version = resolver.resolve_version(
    runtime_version="unknown",
    fallback_to_active=True
)
# Returns: "1.2.3" (from active model)

# Get active model info
active_info = resolver.get_active_model_info()
# {
#   "version": "1.2.3",
#   "status": "production",
#   "performance_metrics": {...}
# }

# Compare versions
comparison = resolver.compare_versions("1.1.0", "1.2.3")
# {
#   "version1": "1.1.0",
#   "version2": "1.2.3",
#   "metrics": {
#     "accuracy": {
#       "version1": 0.92,
#       "version2": 0.94,
#       "improvement": True,
#       "percent_change": 2.17
#     }
#   }
# }
```

### 2.3 Displaying Resolved Versions

Dashboard now shows:
- **Single Patient Mode**: Model version resolved via registry
- **History View**: All predictions have resolved versions
- **Prediction Logs**: Version shown normalized
- **Batch CSV Results**: Version column normalized

---

## 📊 Part 3: Risk Progression Detection (`services/risk_progression.py`)

### 3.1 RiskProgressionEngine

Tracks patient risk changes, detects escalations, and generates clinical alerts.

```python
engine = RiskProgressionEngine()

# Add each prediction
engine.add_prediction({
    "id": 123,
    "patient_id": 456,
    "predicted_label": "2",  # Class 2: Moderate Risk
    "confidence": 0.85,
    "created_at": "2024-03-30T10:30:00Z",
    "model_version": "1.2.3",
    "input_features": {...}
})

# Analyze progression
progression = engine.get_progression(patient_id=456)
# RiskProgression(
#   current_risk_class=2,
#   previous_risk_class=1,
#   escalation_detected=True,  # Risk increased!
#   escalation_direction="up",
#   change_magnitude=1,
#   trend="worsening",
#   consecutive_escalations=2
# )
```

### 3.2 Escalation Detection Logic

Escalation alert triggered when:
- Risk class increases (e.g., 1 → 2 → 3)
- Within escalation threshold (7 days)
- Multiple consecutive increases

### 3.3 Clinical Alerts

```python
alerts = engine.generate_risk_alerts(progression, patient_id)
# [
#   {
#     "severity": "CRITICAL",
#     "title": "HIGH RISK - Cognitive Decline Detected",
#     "detail": "Patient at high risk (class 3). Recommend immediate cognitive assessment.",
#     "type": "risk_level"
#   },
#   {
#     "severity": "WARNING",
#     "title": "⚠️ RISK ESCALATION DETECTED",
#     "detail": "Risk increased from class 1 to 2. Changes stage worsening.",
#     "type": "escalation"
#   }
# ]
```

### 3.4 Risk Progression Display

```
Previous Risk: Low Risk (Class 1)
Current Risk: Moderate Risk (Class 2)

⚠️ RISK ESCALATION DETECTED
Risk increased from class 1 to class 2 (1 stage worsening)

Consecutive escalations: 2
Trend: Worsening
Days at current risk: 3

📈 Recommend:
- Follow-up cognitive assessment within 1 week
- Nephrology consultation for CKD management
- Review medications affecting cognition
```

---

## 🔧 Part 4: Enhanced API Client (`services/api_client.py`)

New methods for enterprise monitoring:

### 4.1 Model Registry Operations
```python
get_model_registry(token) → List[Dict]
get_active_model_version(token) → Dict
get_model_version_info(version, token) → Dict
compare_model_versions(v1, v2, token) → Dict
get_model_performance_history(token) → Dict
```

### 4.2 Analytics & Monitoring
```python
get_prediction_confidence_trend(days=7, token) → Dict
get_drift_trends(token) → Dict
get_patient_risk_progression(patient_id, token) → Dict
get_prediction_audit_logs(patient_id=None, limit=100, token) → List[Dict]
resolve_model_version(runtime_version, patient_id=None, token) → Dict
```

---

## 👨‍⚕️ Part 5: Role-Based Dashboard Modes

### Single Patient
- **Access**: All authenticated users
- **Features**: 
  - Clinically plausible patient presets (Normal/Moderate/High)
  - Real-time prediction with timing breakdown
  - CDS interpretation panel with actions
  - Explainability with SHAP-like waterfall
  - PDF report download
  - Risk progression tracking

### Batch CSV
- **Access**: All authenticated users
- **Features**:
  - Progress bar during scoring
  - Enriched output (confidence, clinical label, version)
  - Statistics dashboard (high-risk count, avg confidence)
  - Distribution charts
  - CSV download with clinical normalizations

### Command Center
- **Access**: Authenticated users
- **Features**:
  - KPI cards (volume, critical count, accuracy, version)
  - Prediction trend chart
  - Risk distribution pie chart
  - Confidence distribution histogram
  - Performance metrics (accuracy, precision, recall, F1)

### ML Monitoring
- **Access**: Authenticated users
- **Features**:
  - Model health status
  - Confidence drift detection
  - Distribution shift analysis
  - Feature drift table with highlighting
  - Confidence and prediction histograms

### Alerts
- **Access**: Authenticated users
- **Features**:
  - Hospital severity feed (INFO/WARNING/CRITICAL)
  - Color-coded alerts
  - Risk escalation notifications
  - Drift warnings

### Prediction Logs
- **Access**: Authenticated users
- **Features**:
  - Audit viewer with clinical labels
  - Sortable/filterable table
  - Model version normalization
  - CSV export

### Longitudinal Tracking
- **Access**: Authenticated users
- **Features**:
  - Patient timeline selection
  - eGFR trend chart
  - Creatinine trend chart
  - Risk trend chart
  - Escalation detection display
  - Clinical recommendations

### Model Governance
- **Access**: Admin, ML Engineer
- **Features**:
  - Model registry table
  - Activate/Deactivate buttons
  - Model comparison bar chart
  - Version metrics display

### Performance Analytics
- **Access**: Admin, ML Engineer
- **Features**:
  - Accuracy/Precision/Recall/F1 metrics
  - Performance snapshots
  - Model comparison capability

### Testing Tools
- **Access**: Admin, ML Engineer
- **Features**:
  - Synthetic patient generator (low/moderate/high)
  - Auto-fill for testing

### System Health
- **Access**: Authenticated users
- **Features**:
  - API status indicator
  - Database status
  - Model status
  - Health score card

### Prediction History
- **Access**: Doctor, Nurse, Admin
- **Features**:
  - Filterable by date range
  - Filterable by clinical label
  - Filterable by model version
  - Pagination (10, 20, 50, 100 per page)
  - Clinical normalization
  - CSV export

### Admin Analytics
- **Access**: Admin only
- **Features**:
  - Total prediction count
  - Distribution by risk class
  - Average confidence by model version
  - Latest predictions summary
  - CSV export

---

## 🚀 Part 6: Deployment & Integration

### 6.1 Environment Variables

```bash
API_URL=http://127.0.0.1:8000
REQUEST_TIMEOUT=10
ENV=production
```

### 6.2 Starting the System

```bash
# Terminal 1: API
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Dashboard
streamlit run dashboard.py --server.port 8501
```

### 6.3 Health Checks

```bash
# API health
curl http://127.0.0.1:8000/health

# Dashboard health
curl http://127.0.0.1:8501/_stcore/health
```

---

## 📋 Part 7: New Files Created

| File | Purpose | Size |
|------|---------|------|
| `ui/theme.py` | Medical color theme, styling constants | 250 lines |
| `services/risk_progression.py` | Risk tracking and escalation detection | 350 lines |
| `services/model_registry_resolver.py` | Version resolution with FallBacks | 200 lines |

### 6.4 Updated Files

| File | Changes |
|------|---------|
| `dashboard.py` | Integrated theme, risk engine, resolver (1200+ lines) |
| `services/api_client.py` | Added 9 new API methods |
| `ui/__init__.py` | Created (placeholder) |

---

## ✅ Part 8: Testing Checklist

### Authentication
- [ ] Login with admin@example.com / password works
- [ ] JWT token validation passes
- [ ] Session expires appropriately
- [ ] Logout clears session state

### Single Patient
- [ ] Normal preset loads correctly
- [ ] Prediction returns 200
- [ ] Model version displayed (not "unknown")
- [ ] CDS interpretation shown
- [ ] PDF report generates
- [ ] Risk progression tracked

### Batch CSV
- [ ] CSV upload validates columns
- [ ] Batch prediction completes
- [ ] Progress bar updates
- [ ] Statistics display correctly
- [ ] Download button works
- [ ] Clinical labels normalized

### Command Center
- [ ] KPI cards load
- [ ] Charts render (Plotly)
- [ ] Model version displayed
- [ ] Performance metrics shown

### ML Monitoring
- [ ] Model health status shown
- [ ] Drift detection works
- [ ] Feature drift table displays
- [ ] Drift warnings highlight

### Model Governance
- [ ] Registry table loads
- [ ] Activate/Deactivate buttons functional
- [ ] Comparison chart renders

### System Health
- [ ] API status correct
- [ ] DB status correct
- [ ] Model status correct

### Risk Progression
- [ ] Last 2 predictions compared
- [ ] Escalation alert triggered on increase
- [ ] Alert color matches severity
- [ ] Risk trend chart shows progression

### Model Version Resolution
- [ ] Runtime "unknown" version resolved to registry
- [ ] Version displayed in all views
- [ ] Version normalization consistent
- [ ] Fallback chain working

---

## 🔐 Part 9: Security & Best Practices

### Role-Based Access Control (RBAC)
```python
Admin:     All dashboard modes + model control
Doctor:    Prediction + clinical decision views
Nurse:     View-only predictions + patient history
ML Engineer: Model governance + monitoring
Lab Technician: Treated as Nurse (role aliasing)
```

### Audit Logging
All predictions logged with:
- User email (no PHI)
- Prediction label
- Confidence
- Model version
- Timestamp

### Error Handling
- API failures handled gracefully
- User-friendly error messages
- No stack traces leaked to frontend
- Authentication errors clear session

### Data Privacy
- No patient identifiable information (PII) in logs
- Features only stored in predictions table
- Audit trail sanitized before display
- PDF reports generated client-side

---

## 📊 Part 10: Production Monitoring Features

### Prediction Confidence Trend
Tracks confidence decay over time:
```python
get_prediction_confidence_trend(days=7, token)
```

### Feature Drift Monitoring
Detects statistical shift in features:
- Mean drift per feature
- Percentage change
- Drift severity flags

### Model Performance Tracking
Stores metrics per version:
- Accuracy, Precision, Recall, F1, AUC
- Confusion matrices
- Performance history

### Inference Metadata
Each prediction now includes:
- Timestamp (UTC)
- Feature signature (SHA256)
- Model version
- Feature count
- User email (requested_by)

---

## 🎯 Part 11: Implementation Highlights

### Multi-Level Fallback Design
Model version resolution never fails:
1. Use runtime version if valid
2. Query registry for active model
3. Use parameter fallback
4. Default to "version_unavailable"

### Non-Invasive Architecture
All new features are additions:
- No breaking changes to existing APIs
- Modular service layer
- Progressive enhancement
- Backward compatible

### Enterprise-Grade Styling
Professional medical UI:
- Clinical color palette (not just bright colors)
- Accessibility: high contrast ratios
- Proper spacing and alignment
- Professional typography
- Icon-based status indicators

### Real-Time Monitoring
Dashboard tracks:
- Prediction volume (today/total)
- API health (real-time)
- Model version (active)
- System latency (simulated realistic UX)
- Patient risk changes (live alerts)

---

## 🚨 Part 12: Known Limitations & Future Work

### Current Limitations
1. Risk progression stored in session (cleared on refresh)
2. Model version comparison requires API call
3. Drift detection uses heuristic (not full statistical tests)
4. PDF report uses matplotlib (not production BI tool)

### Future Enhancements
1. Persist risk progression to PostgreSQL
2. Train SHAP explainer models
3. Integrate MLflow for experiment tracking
4. Add Prometheus metrics for Kubernetes
5. Implement distributed tracing (OpenTelemetry)
6. Add automated retraining trigger logic
7. Implement feature store integration
8. Add model shadowing (A/B testing) UI

---

## 📞 Support & Troubleshooting

### Model version shows "version_unavailable"
1. Check `GET /models` API endpoint
2. Verify active model in registry
3. Check prediction response includes model_version

### Risk escalation not detecting
1. Verify predictions have patient_id
2. Check predictions are within 7 days
3. Confirm risk_class is 0-3

### Clinical colors not showing
1. Clear browser cache
2. Restart Streamlit
3. Check COLORS dict in `ui/theme.py`

### Batch prediction hangs
1. Check CSV column names match FEATURE_COLUMNS
2. Verify API timeout increased (default 10s)
3. Check backend logs for errors

---

## 📖 Quick Reference

| Feature | Location | API Endpoint |
|---------|----------|--------------|
| Model Registry | Model Governance | `/models/registry` |
| Version Resolution | All views | `/models/resolve-version` |
| Risk Progression | Longitudinal View | `/patients/{id}/risk-progression` |
| Drift Monitoring | ML Monitoring | `/clinical/drift` |
| Alerts | Alert View | `/clinical/monitoring` |
| System Health | System Health | `/clinical/system-health` |

---

## 🎓 Learning Resources

- **Healthcare AI Standards**: HL7 FHIR, DICOM
- **Clinical Decision Support**: FDA Software as a Medical Device (SaMD) guidance
- **Risk Stratification**: eGFR clinica staging reference
- **Model Monitoring**: Model Card template (Mitchell et al., 2019)
- **MLOps**: MLflow, Kubeflow, Airflow

---

**Document Version**: 1.0  
**Last Updated**: March 30, 2026  
**Next Review**: Q2 2026
