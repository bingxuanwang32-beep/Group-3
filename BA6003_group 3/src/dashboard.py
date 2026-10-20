"""HDB Atlas — customer-first Streamlit dashboard for existing BA6003 SQLite pipeline.

Place at src/dashboard.py. Run pipeline first, then:
    python -m streamlit run src/dashboard.py
Requires streamlit, pandas (plotly optional, with Streamlit fallbacks).
"""
from pathlib import Path
import json
import sqlite3
import os
import urllib.request
import urllib.error
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "output" / "hdb_full.sqlite"
REPORT = ROOT / "output" / "quality_report.json"
st.set_page_config(page_title="HDB Atlas · Singapore Resale Insights", page_icon="🏡", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800;900&display=swap');
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"] {background:#F2F5F8!important;color:#162D40!important;}
[data-testid="stHeader"] {background:transparent!important;}
#MainMenu,footer {visibility:hidden;}
.block-container {max-width:1350px!important;padding:1.1rem 2.3rem 4rem!important;}
html,body,p,div,span,label,input,button {font-family:'DM Sans',sans-serif;}
h1,h2,h3 {font-family:'Outfit',sans-serif!important;letter-spacing:-.035em!important;color:#122D44!important;}
[data-testid="stSidebar"] {background:#102C42!important;}
[data-testid="stSidebar"] > div {color:#E9F4F5!important;}
.headerbar {display:flex;align-items:center;justify-content:space-between;padding:12px 6px 19px;}
.brand {font-family:'Outfit',sans-serif;font-weight:900;font-size:22px;letter-spacing:-.055em;color:#17364B;}
.brand span {color:#0D988A;}
.headercaption {font-size:11px;letter-spacing:.14em;color:#798B99;font-weight:800;}
.hero {background:linear-gradient(119deg,rgba(11,35,55,.98),rgba(17,69,78,.94)),radial-gradient(circle at 85% 10%,#1ba994,transparent 40%);border-radius:26px;padding:54px 58px 50px;min-height:280px;color:white;box-shadow:0 16px 38px rgba(14,39,54,.14);position:relative;overflow:hidden;margin-bottom:22px;}
.hero:before {content:'';position:absolute;width:300px;height:300px;border:1px solid #ffffff25;border-radius:50%;right:100px;top:-110px;box-shadow:0 0 0 64px #ffffff08,0 0 0 126px #ffffff06;}
.hero:after {content:'⌂';font-size:235px;font-weight:100;line-height:1;position:absolute;right:70px;bottom:-60px;color:#ffffff0d;transform:rotate(-8deg);}
.eyebrow {display:inline-block;position:relative;z-index:1;color:#B1F0DE;letter-spacing:.18em;font-weight:800;font-size:11px;text-transform:uppercase;background:#ffffff17;padding:9px 13px;border-radius:999px;}
.hero-title {position:relative;z-index:1;font-family:'Outfit',sans-serif;font-size:clamp(36px,4.2vw,61px);font-weight:800;line-height:1.02;letter-spacing:-.055em;color:#FFFFFF;margin:19px 0 16px;max-width:740px;}
.hero-title i {font-style:normal;color:#6CE0C4;}
.hero-sub {position:relative;z-index:1;font-size:15px;color:#D5E9E9;line-height:1.75;max-width:570px;}
.tagline {margin:16px 0 4px;color:#62778B;font-size:13px;}
.sectionhead {font-family:'Outfit',sans-serif;font-size:25px;font-weight:800;color:#12334B;letter-spacing:-.035em;margin:23px 0 4px;}
.sectionnote {font-size:13px;color:#73869A;margin:0 0 17px;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:20px!important;border-color:#E4ECF0!important;}
[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stSelectbox"]) {background:#FFFFFF!important;box-shadow:0 12px 32px rgba(28,60,74,.04);}
[data-testid="stMetric"] {background:white!important;border:1px solid #E1E9ED!important;border-radius:17px!important;padding:18px 21px!important;box-shadow:0 8px 28px rgba(24,48,64,.045);border-top:4px solid #20AD99!important;}
[data-testid="stMetricLabel"] {font-weight:700;color:#6B8190;font-size:12px;}
[data-testid="stMetricValue"] {font-family:'Outfit',sans-serif!important;font-size:29px!important;font-weight:800!important;color:#14334A!important;}
[data-testid="stTabs"] [role="tablist"] {background:#FFFFFF;border:1px solid #E2EAF0;border-radius:14px;padding:7px 9px;gap:9px;box-shadow:0 4px 18px #223e5510;}
[data-testid="stTabs"] button[role="tab"] {font-weight:800;color:#657D8E!important;border-radius:10px;padding:9px 16px;}
[data-testid="stTabs"] button[aria-selected="true"] {background:#E0F5EF!important;color:#08695E!important;}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],[data-testid="stTabs"] [data-baseweb="tab-border"] {display:none!important;}
[data-testid="stDataFrame"] {border-radius:14px;overflow:hidden;border:1px solid #E1E9ED;}
[data-baseweb="select"]>div,[data-testid="stNumberInput"] input {border-radius:12px!important;background:#F7FAFB!important;border-color:#DFE8ED!important;}
.stButton button[kind="primary"],.stDownloadButton button {background:#0C877B!important;color:white!important;border:none!important;border-radius:12px!important;font-weight:700!important;}
.stButton button[kind="primary"]:hover,.stDownloadButton button:hover {background:#08695F!important;}
[data-testid="stAlert"] {border-radius:15px;}
.smallfooter {margin-top:36px;padding-top:22px;border-top:1px solid #DEE7ED;display:flex;justify-content:space-between;color:#8696A5;font-size:11px;}
@media(max-width:700px){.block-container{padding:.5rem 1rem 2rem!important}.hero{padding:35px 25px;min-height:220px}.hero-title{font-size:36px}.headercaption{display:none}.smallfooter{display:block}}

/* === ACCESSIBILITY / LEGIBILITY FIX: light page, dark labels === */
/* These rules intentionally come AFTER the original styles. */
[data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] [data-testid="stWidgetLabel"] *,
[data-testid="stMain"] label,
[data-testid="stMain"] label p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] label {
  color:#18384E !important;
  -webkit-text-fill-color:#18384E !important;
  opacity:1 !important;
}
/* Explicitly style common Streamlit widget labels (including baseweb variants). */
[data-testid="stMain"] [data-testid="stSelectbox"] label *,
[data-testid="stMain"] [data-testid="stMultiSelect"] label *,
[data-testid="stMain"] [data-testid="stNumberInput"] label *,
[data-testid="stMain"] [data-testid="stToggle"] label *,
[data-testid="stMain"] [data-testid="stSlider"] label * {
  color:#18384E !important;
  -webkit-text-fill-color:#18384E !important;
}
/* Use a WHITE field background with DARK text for every search control. */
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="input"] > div,
[data-testid="stMain"] [data-testid="stNumberInput"] input {
  background:#FFFFFF !important;
  border-color:#CBD9DF !important;
  color:#18384E !important;
  -webkit-text-fill-color:#18384E !important;
