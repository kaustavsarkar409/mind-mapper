"""MindMarker — early cognitive risk screening from a 30-second speech sample."""

from __future__ import annotations

import textwrap
import streamlit as st

from analyzer import AnalysisResult, analyze_uploaded_bytes, get_demo_analysis

st.set_page_config(
    page_title="MindMarker",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = textwrap.dedent("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    /* Hide default Streamlit elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }

    /* Global theme resets */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif !important;
        color: #E2E8F0;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background:
            radial-gradient(circle at 80% 20%, rgba(20, 184, 166, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 20% 80%, rgba(16, 185, 129, 0.12) 0%, transparent 50%),
            linear-gradient(160deg, #090D16 0%, #0F172A 60%, #090B11 100%);
        background-size: 200% 200%;
        animation: gradientBG 15s ease infinite;
        background-attachment: fixed;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1100px !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0B0F19 !important;
        border-right: 1px solid rgba(20, 184, 166, 0.15) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.4) !important;
        color: #E2E8F0 !important;
    }
    
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] li, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] strong, 
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] a {
        color: #E2E8F0 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(20, 184, 166, 0.15) !important;
    }

    .sidebar-brand {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 8px;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #14B8A6, #34D399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .sidebar-tagline {
        font-size: 1rem;
        color: #64748B;
        margin-top: 2px;
    }

    .science-heading {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #14B8A6;
        margin-bottom: 0.75rem;
    }

    .science-block {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #94A3B8;
    }

    .science-block strong {
        color: #E2E8F0;
    }

    .sidebar-tip {
        background: rgba(20, 184, 166, 0.08);
        border: 1px solid rgba(20, 184, 166, 0.2);
        border-radius: 12px;
        padding: 0.85rem;
        font-size: 0.8rem;
        color: #94A3B8;
        line-height: 1.5;
    }

    .sidebar-tip code {
        color: #34D399;
        background: rgba(52, 211, 153, 0.08);
        padding: 0.1rem 0.3rem;
        border-radius: 4px;
    }

    /* Custom Clinical Glass Cards */
    .clinical-card {
        background: rgba(17, 24, 39, 0.65);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 2px solid rgba(20, 184, 166, 0.35);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease;
    }

    .clinical-card:hover {
        transform: translateY(-2px);
        border-color: rgba(20, 184, 166, 0.4);
        box-shadow: 0 12px 35px rgba(20, 184, 166, 0.12);
    }

    .clinical-card--risk-low {
        border-top: 3px solid #10B981;
        box-shadow: 0 8px 30px rgba(16, 185, 129, 0.05);
    }
    .clinical-card--risk-low:hover {
        border-color: rgba(16, 185, 129, 0.5);
        box-shadow: 0 12px 35px rgba(16, 185, 129, 0.12);
    }

    .clinical-card--risk-elevated {
        border-top: 3px solid #F59E0B;
        box-shadow: 0 8px 30px rgba(245, 158, 11, 0.05);
    }
    .clinical-card--risk-elevated:hover {
        border-color: rgba(245, 158, 11, 0.5);
        box-shadow: 0 12px 35px rgba(245, 158, 11, 0.12);
    }

    .clinical-card--risk-high {
        border-top: 3px solid #EF4444;
        box-shadow: 0 8px 30px rgba(239, 68, 68, 0.06);
    }
    .clinical-card--risk-high:hover {
        border-color: rgba(239, 68, 68, 0.5);
        box-shadow: 0 12px 35px rgba(239, 68, 68, 0.15);
    }

    /* Hero Badge */
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        background: rgba(20, 184, 166, 0.08);
        color: #14B8A6;
        border: 1px solid rgba(20, 184, 166, 0.25);
        border-radius: 99px;
        padding: 0.35rem 0.85rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 10px rgba(20, 184, 166, 0.05);
    }

    .hero-pulse-dot {
        width: 6px;
        height: 6px;
        background-color: #34D399;
        border-radius: 50%;
        animation: heart-beat 1.6s ease-in-out infinite;
    }

    @keyframes heart-beat {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.4); opacity: 0.5; }
        100% { transform: scale(1); opacity: 1; }
    }

    .main-header {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: clamp(3.8rem, 8vw, 5.5rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        line-height: 1.05 !important;
        margin: 0 0 0.75rem 0 !important;
        background: linear-gradient(135deg, #F8FAFC 30%, #94A3B8 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }

    .main-header span {
        background: linear-gradient(90deg, #14B8A6, #34D399) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }

    .sub-header {
        color: #94A3B8;
        font-size: 1.15rem;
        line-height: 1.5;
        margin: 0;
        max-width: 680px;
    }

    /* File Uploader styling */
    [data-testid="stFileUploader"] section {
        background: rgba(15, 23, 42, 0.4) !important;
        border: 1px dashed rgba(20, 184, 166, 0.25) !important;
        border-radius: 14px !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stFileUploader"] section:hover {
        border-color: rgba(20, 184, 166, 0.5) !important;
        background: rgba(20, 184, 166, 0.03) !important;
        box-shadow: 0 0 15px rgba(20, 184, 166, 0.05) !important;
    }

    /* Section elements */
    .section-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #14B8A6;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .panel-heading {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #F1F5F9;
        margin: 0 0 1rem 0;
        letter-spacing: -0.01em;
    }

    /* Transcript Box */
    .transcript-box {
        color: #CBD5E1;
        font-size: 1.05rem;
        line-height: 1.7;
        background: rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 1.1rem;
    }

    .highlighted-filler {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #F87171;
        border-radius: 6px;
        padding: 1px 6px;
        font-weight: 600;
        font-size: 0.9em;
        margin: 0 2px;
        display: inline-block;
    }

    /* Waveform Animation */
    .waveform-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        height: 40px;
        margin: 0.5rem 0;
    }
    .waveform-bar {
        width: 3px;
        background: linear-gradient(180deg, #14b8a6, #10b981);
        border-radius: 3px;
        animation: wave-breath 1.2s ease-in-out infinite alternate;
    }
    .bar-1 { height: 8px; animation-delay: 0.1s; }
    .bar-2 { height: 25px; animation-delay: 0.3s; }
    .bar-3 { height: 35px; animation-delay: 0.5s; }
    .bar-4 { height: 18px; animation-delay: 0.2s; }
    .bar-5 { height: 30px; animation-delay: 0.4s; }
    .bar-6 { height: 12px; animation-delay: 0.6s; }
    .bar-7 { height: 22px; animation-delay: 0.15s; }
    .bar-8 { height: 8px; animation-delay: 0.35s; }

    @keyframes wave-breath {
        0% { transform: scaleY(0.4); }
        100% { transform: scaleY(1.2); }
    }

    /* Risk gauge styling */
    .risk-widget-shell {
        text-align: center;
        padding: 0.25rem 0;
    }

    .risk-widget-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #94A3B8;
        margin-bottom: 1rem;
    }

    .risk-gauge-wrap {
        position: relative;
        width: 200px;
        height: 200px;
        margin: 0 auto 1.25rem;
    }

    .risk-gauge-svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
    }

    .risk-gauge-track {
        fill: none;
        stroke: rgba(255, 255, 255, 0.05);
        stroke-width: 12;
    }

    .risk-gauge-fill {
        fill: none;
        stroke-width: 12;
        stroke-linecap: round;
        transition: stroke-dashoffset 0.8s ease-in-out;
    }

    .risk-gauge-center {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .risk-score-huge {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1;
    }

    .risk-score-huge--low {
        color: #10B981;
    }

    .risk-score-huge--elevated {
        color: #F59E0B;
    }

    .risk-score-huge--high {
        color: #EF4444;
    }

    .risk-score-unit {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #64748B;
        margin-top: 0.25rem;
    }

    .risk-category-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 130px;
        padding: 0.5rem 1.25rem;
        border-radius: 99px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: #0F172A;
    }

    .risk-category-badge--low {
        background: linear-gradient(135deg, #10B981, #059669);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }

    .risk-category-badge--elevated {
        background: linear-gradient(135deg, #F59E0B, #D97706);
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
    }

    .risk-category-badge--high {
        background: linear-gradient(135deg, #EF4444, #DC2626);
        color: #FFFFFF;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.35);
    }

    .risk-demo-tag {
        display: inline-block;
        margin-top: 0.9rem;
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748B;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 99px;
        padding: 0.25rem 0.75rem;
    }

    /* Metric Tiles */
    .metric-tile {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        transition: all 0.25s ease;
    }

    .metric-tile:hover {
        border-color: rgba(20, 184, 166, 0.3);
        background: rgba(20, 184, 166, 0.03);
    }

    .metric-title {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #F1F5F9;
    }

    /* Contributing factors */
    .factors-wrap {
        margin-top: 0.25rem;
    }

    .factor-pill {
        display: inline-flex;
        align-items: center;
        background: rgba(20, 184, 166, 0.06);
        color: #CCFBF1;
        border: 1px solid rgba(20, 184, 166, 0.2);
        border-radius: 99px;
        padding: 0.35rem 0.8rem;
        margin: 0.2rem 0.3rem 0.2rem 0;
        font-size: 0.78rem;
        font-weight: 500;
    }

    /* Biomarker Range Visualizers */
    .biomarker-range-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.75rem;
        transition: all 0.25s ease;
    }

    .biomarker-range-card:hover {
        border-color: rgba(20, 184, 166, 0.25);
        background: rgba(20, 184, 166, 0.02);
    }

    .biomarker-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .biomarker-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #CBD5E1;
    }

    .biomarker-val {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.95rem;
        font-weight: 700;
        color: #F1F5F9;
    }

    .biomarker-bar-container {
        position: relative;
        height: 8px;
        margin: 0.5rem 0;
    }

    .biomarker-track {
        position: absolute;
        inset: 0;
        background-color: rgba(255, 255, 255, 0.06);
        border-radius: 99px;
        overflow: visible;
    }

    .biomarker-healthy-zone {
        position: absolute;
        top: 0;
        bottom: 0;
        background-color: rgba(16, 185, 129, 0.22);
        border-radius: 99px;
    }

    .biomarker-marker {
        position: absolute;
        top: 50%;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        transform: translate(-50%, -50%);
        border: 2px solid #090D16;
        box-shadow: 0 0 8px rgba(0, 0, 0, 0.5);
        transition: left 0.5s ease-in-out;
    }

    .biomarker-footer {
        display: flex;
        justify-content: space-between;
        font-size: 0.68rem;
        color: #64748B;
        margin-top: 0.25rem;
    }

    .biomarker-healthy-text {
        font-weight: 500;
        color: #94A3B8;
    }

    /* Patient Insights */
    .patient-insight-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.35rem 0.8rem;
        border-radius: 99px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .patient-insight-badge--good {
        background-color: rgba(16, 185, 129, 0.1);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .patient-insight-badge--elevated {
        background-color: rgba(245, 158, 11, 0.1);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .patient-insight-badge--high {
        background-color: rgba(239, 68, 68, 0.1);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }

    .patient-exercise-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-left: 3px solid #14B8A6;
        border-radius: 8px;
        padding: 0.85rem;
        margin-bottom: 0.6rem;
    }

    .patient-exercise-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #E2E8F0;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .patient-exercise-desc {
        font-size: 0.78rem;
        color: #94A3B8;
        line-height: 1.4;
    }

    /* Custom Streamlit Radio to Segmented Control override styling */
    div[data-testid="stRadio"] > div {
        background-color: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(20, 184, 166, 0.25) !important;
        border-radius: 30px !important;
        padding: 3px 6px !important;
        display: flex !important;
        flex-direction: row !important;
        width: fit-content !important;
        gap: 4px !important;
    }

    div[data-testid="stRadio"] label {
        border-radius: 20px !important;
        padding: 6px 18px !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        transition: all 0.25s ease !important;
        cursor: pointer !important;
        margin: 0 !important;
        background: transparent !important;
        border: none !important;
    }

    div[data-testid="stRadio"] label:hover {
        color: #F1F5F9 !important;
        background: rgba(255, 255, 255, 0.03) !important;
    }

    div[data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(20, 184, 166, 0.3) !important;
    }

    div[data-testid="stRadio"] input[type="radio"] {
        display: none !important;
    }

    div[data-testid="stRadio"] label div[dir="ltr"] {
        display: none !important;
    }

    /* Button overrides */
    div.stButton > button {
        border-radius: 12px !important;
        padding: 0.55rem 1.25rem !important;
        font-weight: 600 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #14B8A6 0%, #0D9488 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(20, 184, 166, 0.25) !important;
    }

    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(20, 184, 166, 0.35) !important;
    }

    div.stButton > button:not([kind="primary"]) {
        background-color: rgba(17, 24, 39, 0.7) !important;
        color: #14B8A6 !important;
        border: 1px solid rgba(20, 184, 166, 0.3) !important;
    }

    div.stButton > button:not([kind="primary"]):hover {
        background-color: rgba(20, 184, 166, 0.05) !important;
        border-color: rgba(20, 184, 166, 0.5) !important;
    }

    /* Warnings and Alerts */
    [data-testid="stAlert"] {
        border-radius: 12px !important;
        border: 1px solid rgba(20, 184, 166, 0.15) !important;
        background-color: rgba(17, 24, 39, 0.7) !important;
    }

    .disclaimer {
        text-align: center;
        font-size: 0.78rem;
        color: #64748B;
        line-height: 1.5;
    }



    /* Floating background glows for clinical animation */
    .bg-glow-1 {
        position: fixed;
        width: 600px;
        height: 600px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(20, 184, 166, 0.18) 0%, transparent 70%);
        top: -15%;
        left: -15%;
        z-index: -2;
        filter: blur(80px);
        animation: floatGlow1 20s ease-in-out infinite alternate;
        pointer-events: none;
    }

    .bg-glow-2 {
        position: fixed;
        width: 700px;
        height: 700px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.14) 0%, transparent 70%);
        bottom: -20%;
        right: -20%;
        z-index: -2;
        filter: blur(90px);
        animation: floatGlow2 25s ease-in-out infinite alternate;
        pointer-events: none;
    }

    @keyframes floatGlow1 {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(120px, 80px) scale(1.15); }
        100% { transform: translate(60px, 160px) scale(0.9); }
    }

    @keyframes floatGlow2 {
        0% { transform: translate(0, 0) scale(1); }
        50% { transform: translate(-140px, -60px) scale(1.1); }
        100% { transform: translate(-80px, -120px) scale(0.85); }
    }
</style>
""")

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def clean_html(html: str) -> str:
    """Helper to remove leading whitespace on each line to prevent Streamlit from showing it as raw markdown code block."""
    return "\n".join(line.strip() for line in html.splitlines())


_RISK_UI = {
    "Low": {
        "wrap": "clinical-card--risk-low",
        "score": "risk-score-huge--low",
        "badge": "risk-category-badge--low",
        "stroke": "#10B981",
        "glow": "drop-shadow(0 0 8px rgba(16, 185, 129, 0.4))",
    },
    "Elevated": {
        "wrap": "clinical-card--risk-elevated",
        "score": "risk-score-huge--elevated",
        "badge": "risk-category-badge--elevated",
        "stroke": "#F59E0B",
        "glow": "drop-shadow(0 0 8px rgba(245, 158, 11, 0.4))",
    },
    "High Risk": {
        "wrap": "clinical-card--risk-high",
        "score": "risk-score-huge--high",
        "badge": "risk-category-badge--high",
        "stroke": "#EF4444",
        "glow": "drop-shadow(0 0 10px rgba(239, 68, 68, 0.45))",
    },
}


def _risk_theme(category: str) -> dict:
    return _RISK_UI.get(category, _RISK_UI["Elevated"])


def _risk_gauge_svg(score: float, stroke: str, glow_filter: str) -> str:
    """Build SVG arc gauge; circumference ≈ 565 for r=90."""
    circumference = 565.48
    offset = circumference - (score / 100.0) * circumference
    return f"""
    <svg class="risk-gauge-svg" viewBox="0 0 200 200" style="filter: {glow_filter};">
        <circle class="risk-gauge-track" cx="100" cy="100" r="90"/>
        <circle class="risk-gauge-fill" cx="100" cy="100" r="90"
            stroke="{stroke}"
            stroke-dasharray="{circumference}"
            stroke-dashoffset="{offset}"/>
    </svg>
    """


def render_sidebar() -> None:
    with st.sidebar:
        sidebar_brand_html = clean_html("""
        <div class="sidebar-brand">🩺 MindMarker</div>
        <div class="sidebar-tagline">Clinical Speech Biomarker System</div>
        """)
        st.markdown(sidebar_brand_html, unsafe_allow_html=True)

        st.markdown("---")
        
        science_html = clean_html("""
        <p class="science-heading">Diagnostic Basis</p>
        <div class="science-block">
        <p><strong>Linguistic tracking</strong> monitors syntactic organization and word retrieval patterns during spontaneous speech:</p>
        <ul>
        <li><strong>Type-Token Ratio (TTR)</strong> — vocabulary diversity; reductions often reflect lexical retrieval difficulties.</li>
        <li><strong>Sentence length</strong> — simplification of grammatical structures can indicate cognitive load adaptation.</li>
        <li><strong>Filler words</strong> (<em>um, uh, like</em>) — high frequency represents searching or pauses during planning.</li>
        </ul>
        <p><strong>Acoustic tracking</strong> measures timing anomalies in the verbal audio stream:</p>
        <ul>
        <li><strong>Pause detection</strong> — measures silent intervals. Frequent pausing suggests processing latency.</li>
        <li><strong>Speech rate (WPM)</strong> — slowing of tempo correlates with overall cognitive speed fluctuations.</li>
        </ul>
        <p>This system acts as a non-invasive screening biomarker and is not a stand-alone diagnostic tool.</p>
        </div>
        """)
        st.markdown(science_html, unsafe_allow_html=True)

        st.markdown("---")
        
        tip_html = clean_html("""
        <div class="sidebar-tip">
        Provide a ~30s vocal recording, or select <strong>Load Demo Sample</strong> for standard reference dashboard visualizations.
        </div>
        """)
        st.markdown(tip_html, unsafe_allow_html=True)


def render_risk_card(result: AnalysisResult) -> None:
    risk = result.risk
    theme = _risk_theme(risk.category)
    demo_tag = (
        '<div class="risk-demo-tag">Demo Mode — Illustrative Metrics Only</div>'
        if result.is_demo
        else ""
    )
    risk_html = clean_html(f"""
    <div class="clinical-card {theme['wrap']}">
        <div class="risk-widget-shell">
            <div class="risk-widget-label">Cognitive Risk Index</div>
            <div class="risk-gauge-wrap">
                {_risk_gauge_svg(risk.score, theme['stroke'], theme['glow'])}
                <div class="risk-gauge-center">
                    <span class="risk-score-huge {theme['score']}">{risk.score:.0f}</span>
                    <span class="risk-score-unit">percent</span>
                </div>
            </div>
            <div class="risk-category-badge {theme['badge']}">{risk.category}</div>
            {demo_tag}
        </div>
    </div>
    """)
    st.markdown(risk_html, unsafe_allow_html=True)


def render_metric(title: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-tile">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def highlight_fillers(transcript: str) -> str:
    from analyzer import FILLER_WORDS
    words = transcript.split()
    highlighted = []
    for word in words:
        clean_word = word.strip(".,!?;:()\"'").lower()
        if clean_word in FILLER_WORDS:
            highlighted.append(f'<span class="highlighted-filler">{word}</span>')
        else:
            highlighted.append(word)
    return " ".join(highlighted)


def render_biomarker_range(label: str, value: float, min_val: float, max_val: float, healthy_min: float, healthy_max: float, unit: str = "") -> str:
    # Scale value to percentage of range [min_val, max_val]
    total_range = max_val - min_val if max_val > min_val else 1.0
    patient_pct = ((value - min_val) / total_range) * 100
    patient_pct = max(0.0, min(100.0, patient_pct))
    
    healthy_min_pct = ((healthy_min - min_val) / total_range) * 100
    healthy_max_pct = ((healthy_max - min_val) / total_range) * 100
    healthy_width = healthy_max_pct - healthy_min_pct
    
    # Check if patient value is healthy
    if "Filler" in label or "Pause" in label:
        is_healthy = value <= healthy_max
    else:
        is_healthy = healthy_min <= value <= healthy_max
        
    marker_color = "#10B981" if is_healthy else ("#F59E0B" if is_healthy or value >= healthy_min - 0.1 * total_range else "#EF4444")
    
    # Format value, min_val, max_val to strings
    val_str = f"{value:.2f}" if isinstance(value, float) else str(value)
    min_str = f"{min_val:.1f}" if isinstance(min_val, float) else str(min_val)
    max_str = f"{max_val:.1f}" if isinstance(max_val, float) else str(max_val)
    h_min_str = f"{healthy_min:.1f}" if isinstance(healthy_min, float) else str(healthy_min)
    h_max_str = f"{healthy_max:.1f}" if isinstance(healthy_max, float) else str(healthy_max)
    
    html = clean_html(f"""
    <div class="biomarker-range-card">
        <div class="biomarker-header">
            <span class="biomarker-label">{label}</span>
            <span class="biomarker-val">{val_str}{unit}</span>
        </div>
        <div class="biomarker-bar-container">
            <div class="biomarker-track">
                <div class="biomarker-healthy-zone" style="left: {healthy_min_pct}%; width: {healthy_width}%;"></div>
                <div class="biomarker-marker" style="left: {patient_pct}%; background-color: {marker_color};"></div>
            </div>
        </div>
        <div class="biomarker-footer">
            <span>{min_str}</span>
            <span class="biomarker-healthy-text">Healthy: {h_min_str}-{h_max_str}{unit}</span>
            <span>{max_str}</span>
        </div>
    </div>
    """)
    return html


def render_results(result: AnalysisResult, view_mode: str) -> None:
    # 1. Transcript card
    highlighted_text = highlight_fillers(result.transcript)
    
    transcript_html = clean_html(f"""
    <div class="clinical-card">
        <div class="section-title">✍️ Speech Transcript</div>
        <div class="transcript-box">{highlighted_text}</div>
    </div>
    """)
    st.markdown(transcript_html, unsafe_allow_html=True)
    
    # Section title
    st.markdown('<div class="section-title">📊 Diagnostics Report</div>', unsafe_allow_html=True)
    
    if view_mode == "Patient Dashboard":
        # Render Patient View
        col_risk, col_insights = st.columns([1, 1.2], gap="large")
        with col_risk:
            render_risk_card(result)
            
        with col_insights:
            # Reassuring assessment text
            cat = result.risk.category
            if cat == "Low":
                vitality_title = "Healthy Cognitive Fluency"
                vitality_badge = "patient-insight-badge--good"
                vitality_desc = "Your vocal flow, pacing, and word diversity reflect strong cognitive vitality and linguistic control."
                tips = [
                    ("🧩 Solve puzzle-based games", "Word-search, crossword puzzles, or Sudoku reinforce neural patterns and verbal memory."),
                    ("🗣️ Maintain social connections", "Regular, active conversations are fantastic physical and mental training for speech pacing."),
                    ("🚶 Keep physically active", "Brisk walking or light cardio boosts blood flow to brain regions responsible for language control.")
                ]
            elif cat == "Elevated":
                vitality_title = "Mild Fluency Fluctuations"
                vitality_badge = "patient-insight-badge--elevated"
                vitality_desc = "We detected moderate pauses or slight word repetitions. These patterns are common during fatigue, stress, or normal cognitive load, but worth monitoring."
                tips = [
                    ("📚 Read aloud daily", "Spend 10 minutes reading a book or newspaper out loud. This exercises speech pacing and reduces pause frequency."),
                    ("🧘 Focus on speech breath", "Taking a conscious, gentle breath before starting a sentence helps reduce filler word usage like 'um' or 'uh'."),
                    ("💤 Prioritize cognitive rest", "Ensure 7-8 hours of quality sleep, as fatigue is a major contributor to momentary word-finding difficulties.")
                ]
            else: # High Risk
                vitality_title = "Fluency Patterns Need Attention"
                vitality_badge = "patient-insight-badge--high"
                vitality_desc = "We noted more frequent pausing and simplified sentence patterns. This could indicate normal cognitive aging or fatigue, but sharing these findings with your doctor is recommended."
                tips = [
                    ("🩺 Schedule a routine clinical check", "Share this report summary with your primary care provider or neurologist for a standard cognitive review."),
                    ("🧠 Vocabulary exercise", "Practice daily word-retrieval exercises, such as naming as many animals or countries as possible in 60 seconds."),
                    ("🗣️ Speak at a comfortable pace", "Give yourself permission to slow down and organize your thoughts without rushing. Pacing helps reduce syntactic simplification.")
                ]
                
            insight_html = clean_html(f"""
            <div class="clinical-card">
                <div class="panel-heading">Cognitive Wellness Profile</div>
                <div style="margin-bottom: 1.25rem;">
                    <span class="patient-insight-badge {vitality_badge}">✦ {vitality_title}</span>
                </div>
                <p style="color: #94A3B8; font-size: 0.92rem; line-height: 1.6; margin-bottom: 1.5rem;">{vitality_desc}</p>
                
                <div class="panel-heading" style="font-size: 0.95rem; margin-top: 1rem;">Recommended Cognitive Exercises</div>
            """)
            
            for title, desc in tips:
                insight_html += clean_html(f"""
                <div class="patient-exercise-card">
                    <div class="patient-exercise-title">{title}</div>
                    <div class="patient-exercise-desc">{desc}</div>
                </div>
                """)
            insight_html += "</div>"
            st.markdown(insight_html, unsafe_allow_html=True)
            
    else:
        # Render Clinician View
        col_risk, col_factors = st.columns([1, 1.2], gap="large")
        with col_risk:
            render_risk_card(result)
            
        with col_factors:
            factors_html = "".join(
                f'<span class="factor-pill">✦ {factor}</span>' for factor in result.risk.factors
            )
            factors_card = clean_html(f"""
            <div class="clinical-card" style="height: 100%;">
                <div class="panel-heading">Contributing Biomarker Factors</div>
                <p style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 1rem;">
                    The following features crossed established screening cutoffs and contributed to the elevated risk index:
                </p>
                <div class="factors-wrap">{factors_html}</div>
            </div>
            """)
            st.markdown(factors_card, unsafe_allow_html=True)
            
        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
        
        col_ling, col_acoustic = st.columns(2, gap="large")
        ling = result.linguistic
        ac = result.acoustic
        
        with col_ling:
            st.markdown(clean_html("""
            <div class="clinical-card">
                <div class="panel-heading" style="color: #14B8A6;">🧬 Linguistic Biomarkers</div>
            """), unsafe_allow_html=True)
            
            # TTR: healthy is 0.45 - 0.65
            st.markdown(render_biomarker_range("Type-Token Ratio (TTR)", ling.type_token_ratio, 0.20, 0.70, 0.45, 0.65), unsafe_allow_html=True)
            # Sentence length: healthy is 7.0 - 15.0
            st.markdown(render_biomarker_range("Avg Sentence Length", ling.avg_sentence_length, 2.0, 20.0, 7.0, 15.0, " words"), unsafe_allow_html=True)
            # Filler word rate: healthy is < 0.05
            filler_rate = ling.filler_total / max(ling.total_words, 1)
            st.markdown(render_biomarker_range("Filler Word Rate", filler_rate, 0.0, 0.25, 0.0, 0.05), unsafe_allow_html=True)
            # Pronoun-Noun ratio: healthy is 0.10 - 0.45
            st.markdown(render_biomarker_range("Pronoun-Noun Ratio", ling.pronoun_noun_ratio, 0.0, 1.2, 0.10, 0.45), unsafe_allow_html=True)
            # Adjective/Adverb density: healthy is 0.12 - 0.28
            st.markdown(render_biomarker_range("Adjective/Adverb Density", ling.adj_adv_density, 0.0, 0.40, 0.12, 0.28), unsafe_allow_html=True)
            
            ling_extra_html = clean_html(f"""
                <div style="height: 0.75rem;"></div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div class="metric-tile">
                        <div class="metric-title">Total Words</div>
                        <div class="metric-value">{ling.total_words}</div>
                    </div>
                    <div class="metric-tile">
                        <div class="metric-title">Unique Words</div>
                        <div class="metric-value">{ling.unique_words}</div>
                    </div>
                </div>
                <div class="metric-tile" style="margin-top: 10px;">
                    <div class="metric-title">Filler Words Breakdown</div>
                    <div class="metric-value">{ling.filler_total} total</div>
                    <p class="disclaimer" style="text-align: left; margin-top: 4px; font-size: 0.72rem;">
                        {", ".join(f"{k}: {v}" for k, v in ling.filler_counts.items() if v) or "No fillers detected"}
                    </p>
                </div>
            </div>
            """)
            st.markdown(ling_extra_html, unsafe_allow_html=True)
            
        with col_acoustic:
            st.markdown(clean_html("""
            <div class="clinical-card">
                <div class="panel-heading" style="color: #38BDF8;">🩺 Acoustic Biomarkers</div>
            """), unsafe_allow_html=True)
            
            # Speech rate: healthy is 110 - 160
            st.markdown(render_biomarker_range("Speech Rate (WPM)", ac.words_per_minute, 50.0, 200.0, 110.0, 160.0, " WPM"), unsafe_allow_html=True)
            # Articulation rate: healthy is 125 - 175
            st.markdown(render_biomarker_range("Articulation Rate", ac.articulation_rate, 50.0, 250.0, 125.0, 175.0, " WPM"), unsafe_allow_html=True)
            # Avg pause duration: healthy is < 0.5s
            st.markdown(render_biomarker_range("Avg Pause Duration", ac.avg_pause_duration, 0.0, 1.5, 0.0, 0.50, "s"), unsafe_allow_html=True)
            # Pause count: healthy is <= 3 per 30s
            st.markdown(render_biomarker_range("Pause Count", ac.pause_count, 0, 12, 0, 3), unsafe_allow_html=True)
            # Pitch Variation: healthy is 15.0 - 45.0
            st.markdown(render_biomarker_range("Pitch Variation", ac.pitch_variation, 0.0, 60.0, 15.0, 45.0, " Hz"), unsafe_allow_html=True)
            
            acoustic_extra_html = clean_html(f"""
                <div style="height: 0.75rem;"></div>
                <div class="metric-tile">
                    <div class="metric-title">Recording Duration</div>
                    <div class="metric-value">{ac.speech_duration_sec:.1f} seconds</div>
                </div>
            </div>
            """)
            st.markdown(acoustic_extra_html, unsafe_allow_html=True)
            
    # FDA Disclaimer card
    disclaimer_html = clean_html("""
    <div class="clinical-card" style="margin-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.05);">
        <div class="disclaimer">
            ⚠️ <strong>Clinical Notice:</strong> MindMarker provides a research-inspired digital speech biomarker screening signal only. 
            It does not constitute a medical diagnosis, clinical evaluation, or FDA-approved diagnostic statement. 
            Vocal changes can be influenced by multiple factors including situational stress, speech impediments, baseline accent, and temporary fatigue. 
            Consult a certified healthcare professional for a comprehensive cognitive assessment.
        </div>
    </div>
    """)
    st.markdown(disclaimer_html, unsafe_allow_html=True)


def run_analysis_from_upload(uploaded_file) -> AnalysisResult | None:
    suffix = "." + uploaded_file.name.rsplit(".", 1)[-1].lower()
    if suffix not in {".wav", ".mp3"}:
        st.error("Unsupported format. Please upload a .wav or .mp3 file.")
        return None

    with st.spinner("Analyzing speech (Whisper + spaCy + librosa)…"):
        try:
            return analyze_uploaded_bytes(uploaded_file.getvalue(), suffix=suffix)
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
            st.info("Use **Load Demo Sample** to continue your presentation.")
    return None


def main() -> None:
    # Inject animated background glow circles
    st.markdown(
        '<div class="bg-glow-1"></div><div class="bg-glow-2"></div>',
        unsafe_allow_html=True
    )
    render_sidebar()

    hero_html = clean_html("""
    <div class="clinical-card">
        <div class="hero-badge">
            <span class="hero-pulse-dot"></span>
            AI Cognitive Biomarker Engine
        </div>
        <p class="main-header">Mind<span>Marker</span></p>
        <p class="sub-header">
            Non-invasive screening of cognitive risk through acoustic and linguistic speech biomarkers. 
            Analyze a spontaneous speech sample in seconds.
        </p>
    </div>
    """)
    st.markdown(hero_html, unsafe_allow_html=True)

    # File uploader and actions
    uploader_html_start = clean_html("""
    <div class="clinical-card">
        <div class="section-title">🎙️ Audio Sample Upload</div>
    """)
    st.markdown(uploader_html_start, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Upload a speech sample (.wav or .mp3, ~30 seconds)",
        type=["wav", "mp3"],
        help="Record spontaneous speech — e.g., describe your day or a familiar picture.",
        label_visibility="collapsed"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
    with btn_col1:
        analyze_clicked = st.button("Analyze Speech", type="primary", use_container_width=True)
    with btn_col2:
        demo_clicked = st.button("Load Demo Sample", use_container_width=True)

    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    if demo_clicked:
        st.session_state.last_result = get_demo_analysis()
        st.success("Demo sample loaded.")

    if analyze_clicked:
        if uploaded is None:
            st.warning("Upload an audio file first, or click **Load Demo Sample**.")
        else:
            soundwave_placeholder = st.empty()
            soundwave_placeholder.markdown(
                clean_html("""
                <div class="clinical-card" style="text-align: center;">
                    <p style="color: #14B8A6; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.25rem;">Processing Speech Biomarkers...</p>
                    <div class="waveform-container">
                        <div class="waveform-bar bar-1"></div>
                        <div class="waveform-bar bar-2"></div>
                        <div class="waveform-bar bar-3"></div>
                        <div class="waveform-bar bar-4"></div>
                        <div class="waveform-bar bar-5"></div>
                        <div class="waveform-bar bar-6"></div>
                        <div class="waveform-bar bar-7"></div>
                        <div class="waveform-bar bar-8"></div>
                    </div>
                </div>
                """),
                unsafe_allow_html=True
            )
            result = run_analysis_from_upload(uploaded)
            soundwave_placeholder.empty()
            if result is not None:
                st.session_state.last_result = result
                st.success("Analysis complete.")

    if st.session_state.last_result is not None:
        st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
        view_mode = st.radio(
            "Select Dashboard View Mode",
            options=["Patient Dashboard", "Clinician Dashboard"],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
        render_results(st.session_state.last_result, view_mode)
    else:
        onboard_html = clean_html("""
        <div class="clinical-card">
            <p class="panel-heading" style="color: #14B8A6;">Getting Started</p>
            <ol class="onboard-steps" style="line-height: 2; color: #94A3B8; padding-left: 1.2rem;">
                <li>Upload an audio recording (~30 seconds of speech in English).</li>
                <li>Click <strong>Analyze Speech</strong>, or click <strong>Load Demo Sample</strong> for instant visualization.</li>
            </ol>
            <p style="color: #64748B; font-size: 0.82rem; margin-top: 1rem; line-height: 1.5;">
                The diagnostic engine will perform local audio segmentation (energy detection), 
                transcribe using neural network architectures, and map acoustic/linguistic ratios against standard baselines.
            </p>
        </div>
        """)
        st.markdown(onboard_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
