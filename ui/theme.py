"""
Professional medical UI theme for CKD-CI healthcare dashboard.

Follows healthcare design standards:
- Clinical blue/green for primary actions (trust, medical)
- Alert colors: Green (safe) → Yellow (caution) → Orange (warning) → Red (critical)
- Accessibility: High contrast ratios, colorblind-friendly palettes
"""

from dataclasses import dataclass
from typing import Dict

# Medical Color Palette (based on healthcare standards)
COLORS = {
    # Primary (Clinical Trust)
    "primary_dark": "#1565C0",        # Deep medical blue
    "primary": "#1976D2",              # Clinical blue
    "primary_light": "#42A5F5",        # Lighter blue
    
    # Status Colors (Clinical Risk)
    "stable": "#2E7D32",               # Safe green (eGFR > 60)
    "monitor": "#F9A825",              # Caution yellow (eGFR 45-59)
    "attention": "#FB8C00",            # Warning orange (eGFR 30-44)
    "critical": "#C62828",             # Critical red (eGFR < 30)
    
    # Feedback
    "success": "#388E3C",              # Success green
    "warning": "#FFA000",              # Warning amber
    "error": "#D32F2F",                # Error red
    "info": "#0288D1",                 # Info blue
    
    # Neutrals
    "background": "#F5F7FA",           # Light neutral
    "surface": "#FFFFFF",              # Card/surface white
    "border": "#D0D7E1",               # Subtle border
    "text_primary": "#1A1A1A",         # High contrast text
    "text_secondary": "#666666",       # Secondary text
    "text_tertiary": "#999999",        # Tertiary text
}

# Risk Badges with clinical meaning
RISK_BADGES = {
    0: {"label": "No Risk", "color": COLORS["stable"], "icon": "✅", "clinical": "Normal kidney function"},
    1: {"label": "Low Risk", "color": COLORS["monitor"], "icon": "⚠️", "clinical": "Mild CKD"},
    2: {"label": "Moderate Risk", "color": COLORS["attention"], "icon": "⚠️", "clinical": "Moderate CKD"},
    3: {"label": "High Risk", "color": COLORS["critical"], "icon": "🚨", "clinical": "Severe CKD/Cognitive decline likely"},
}

# Status Badges
STATUS_BADGES = {
    "stable": {"label": "Stable", "color": COLORS["stable"], "icon": "✓"},
    "monitor": {"label": "Monitor", "color": COLORS["monitor"], "icon": "◆"},
    "attention": {"label": "Attention", "color": COLORS["attention"], "icon": "⚠"},
    "critical": {"label": "Critical", "color": COLORS["critical"], "icon": "⛔"},
}

# Alert Severity
ALERT_COLORS = {
    "INFO": COLORS["info"],
    "WARNING": COLORS["warning"],
    "CRITICAL": COLORS["error"],
}

# Typography (Streamlit CSS)
TYPOGRAPHY = {
    "font_family": "system-ui, -apple-system, sans-serif",
    "heading_font": "system-ui, -apple-system, sans-serif",
    "code_font": "monospace",
}

# Spacing scale
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "xxl": "3rem",
}

# Shadow depths for cards
SHADOWS = {
    "sm": "0 1px 2px rgba(0,0,0,0.05)",
    "md": "0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.05)",
    "lg": "0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)",
    "xl": "0 20px 25px rgba(0,0,0,0.1), 0 10px 10px rgba(0,0,0,0.04)",
}

# eGFR categories (clinical standard)
EGFR_STAGES = {
    "stage_1": {"range": (90, 150), "label": "Normal", "color": COLORS["stable"]},
    "stage_2": {"range": (60, 89), "label": "Mild decrease", "color": COLORS["stable"]},
    "stage_3a": {"range": (45, 59), "label": "Mild-moderate decrease", "color": COLORS["monitor"]},
    "stage_3b": {"range": (30, 44), "label": "Moderate-severe decrease", "color": COLORS["attention"]},
    "stage_4": {"range": (15, 29), "label": "Severe decrease", "color": COLORS["critical"]},
    "stage_5": {"range": (0, 14), "label": "Kidney failure", "color": COLORS["critical"]},
}


def get_risk_badge(risk_class: int) -> Dict[str, str]:
    """Get badge info for risk class (0-3)."""
    return RISK_BADGES.get(risk_class, RISK_BADGES[0])


def get_status_badge(status: str) -> Dict[str, str]:
    """Get badge info for status."""
    normalized = str(status or "").strip().lower()
    for key, badge in STATUS_BADGES.items():
        if key in normalized:
            return badge
    return STATUS_BADGES["stable"]


def get_alert_color(severity: str) -> str:
    """Get color for alert severity."""
    return ALERT_COLORS.get(str(severity).upper(), COLORS["info"])


def get_egfr_stage(egfr: float) -> Dict[str, any]:
    """Get eGFR clinical stage."""
    for stage, info in EGFR_STAGES.items():
        range_min, range_max = info["range"]
        if range_min <= egfr <= range_max:
            return info
    return EGFR_STAGES["stage_1"]  # Default


def apply_custom_theme() -> str:
    """Return custom Streamlit CSS for medical theme."""
    css = f"""
    <style>
    :root {{
        --primary-color: {COLORS['primary']};
        --primary-dark: {COLORS['primary_dark']};
        --primary-light: {COLORS['primary_light']};
        --success-color: {COLORS['success']};
        --error-color: {COLORS['error']};
        --warning-color: {COLORS['warning']};
        --info-color: {COLORS['info']};
        --background-color: {COLORS['background']};
        --text-primary: {COLORS['text_primary']};
        --text-secondary: {COLORS['text_secondary']};
    }}
    
    * {{
        font-family: {TYPOGRAPHY['font_family']};
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        font-family: {TYPOGRAPHY['heading_font']};
        font-weight: 600;
        letter-spacing: -0.5px;
    }}
    
    body {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
    }}
    
    /* Card styling for Streamlit containers */
    [data-testid="stMetric"] {{
        background-color: {COLORS['surface']};
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: {SHADOWS['md']};
        border: 1px solid {COLORS['border']};
    }}
    
    /* Success/Error message styling */
    .stAlert {{
        border-radius: 6px;
        padding: 1rem 1.5rem;
    }}
    
    .stAlert.success {{
        background-color: rgba(46, 125, 50, 0.1);
        border-left: 4px solid {COLORS['stable']};
    }}
    
    .stAlert.error {{
        background-color: rgba(198, 40, 40, 0.1);
        border-left: 4px solid {COLORS['critical']};
    }}
    
    .stAlert.warning {{
        background-color: rgba(255, 160, 0, 0.1);
        border-left: 4px solid {COLORS['warning']};
    }}
    
    .stAlert.info {{
        background-color: rgba(2, 136, 209, 0.1);
        border-left: 4px solid {COLORS['info']};
    }}
    
    /* Button styling */
    .stButton > button {{
        background-color: {COLORS['primary']};
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {COLORS['primary_dark']};
        box-shadow: {SHADOWS['md']};
    }}
    
    .stButton > button:active {{
        transform: scale(0.98);
    }}
    
    /* SelectBox and other inputs */
    .stSelectbox, .stNumberInput, .stTextInput {{
        border-radius: 6px;
    }}
    
    /* Tabs styling */
    .streamlit-tabs {{
        border-bottom: 2px solid {COLORS['border']};
    }}
    
    /* Expander styling */
    .stExpander {{
        border-radius: 6px;
        border: 1px solid {COLORS['border']};
    }}
    
    </style>
    """
    return css
