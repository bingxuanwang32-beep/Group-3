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
}
[data-testid="stMain"] [data-baseweb="select"] input,
[data-testid="stMain"] [data-baseweb="select"] [role="combobox"],
[data-testid="stMain"] [data-baseweb="select"] [role="combobox"] *,
[data-testid="stMain"] [data-baseweb="input"] input {
  color:#18384E !important;
  -webkit-text-fill-color:#18384E !important;
  opacity:1 !important;
}
[data-testid="stMain"] [data-baseweb="select"] svg,
[data-testid="stMain"] [data-baseweb="input"] svg {fill:#24495F !important;color:#24495F !important;}
/* Selected multiselect tags remain distinctly teal and legible. */
[data-testid="stMain"] [data-baseweb="tag"] {
  background:#D8F4EE !important;
  border-radius:7px !important;
}
[data-testid="stMain"] [data-baseweb="tag"] *,
[data-testid="stMain"] [data-baseweb="tag"] span {
  color:#0C6259 !important;
  -webkit-text-fill-color:#0C6259 !important;
}
/* Fix invisible unselected tab labels. Streamlit nests text in a paragraph. */
[data-testid="stTabs"] button[role="tab"],
[data-testid="stTabs"] button[role="tab"] *,
[data-testid="stTabs"] button[role="tab"] p {
  color:#355268 !important;
  -webkit-text-fill-color:#355268 !important;
  opacity:1 !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] *,
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
  color:#08786C !important;
  -webkit-text-fill-color:#08786C !important;
}
/* Text below charts and other body captions stays readable. */
[data-testid="stMain"] [data-testid="stCaptionContainer"] *,
[data-testid="stMain"] [data-testid="stMetricLabel"] * {
  color:#526E82 !important;
  -webkit-text-fill-color:#526E82 !important;
}
/* Keep hero colors intentionally white, unaffected by label overrides. */
.hero .hero-title {color:#FFFFFF!important;}
.hero .hero-title i {color:#6CE0C4!important;}
.hero .hero-sub {color:#D5E9E9!important;}

</style>""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Loading HDB resale transactions…")
def get_data(dbpath: str, modified: int):
    with sqlite3.connect(dbpath) as conn:
        d = pd.read_sql_query("SELECT * FROM resale_transactions", conn)
    needed = {'month','town','flat_type','floor_area_sqm','resale_price'}
    if not needed.issubset(d.columns):
        raise ValueError(f"Database missing columns: {sorted(needed - set(d.columns))}")
    d['month'] = pd.to_datetime(d['month'], errors='coerce')
    for x in ['floor_area_sqm','resale_price']:
        d[x] = pd.to_numeric(d[x], errors='coerce')
    for x in ['town','flat_type']:
        d[x] = d[x].astype('string').str.strip().str.upper()
    d = d.dropna(subset=['month','town','flat_type','floor_area_sqm','resale_price'])
    d = d.loc[(d.floor_area_sqm>0)&(d.resale_price>0)].copy()
    d['price_per_sqm'] = d.resale_price / d.floor_area_sqm
    d['month_start'] = d.month.dt.to_period('M').dt.to_timestamp()
    return d

# OpenRouter settings are loaded from Streamlit Cloud Secrets first, then local env.
def ai_setting(name):
    try:
        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except (FileNotFoundError, KeyError, AttributeError):
        pass
    value = os.environ.get(name)
    if value:
        return value.strip()
    env_path = ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip("\"").strip("'")
    return None


def ask_hdb_ai(messages, context):
    api_key = ai_setting("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY. Configure Streamlit Secrets.")

    model = ai_setting("OPENROUTER_MODEL") or "openai/gpt-4o-mini"
    system_text = (
        "You are HDB Atlas AI, an assistant for Singapore historical HDB resale data. "
        "Use only the supplied dashboard statistics for numerical statements. "
        "Never invent listings, prices, forecasts or HDB eligibility rules. "
        "Historical sales are not current listings or official valuations. "
        "For town recommendations, rank only the supplied town and flat-type summaries, "
        "and explain budget-fit share and transaction sample size. Do not claim a town "
        "is universally best. For price guidance, give the supplied historical median "
        "and 25th–75th percentile range for the matching town and flat type. If no "
        "matching summary is supplied, ask the user to adjust the dashboard filters. "
        "Do not infer mortgage payments, commute times, amenities or current availability. "
        "When the data is insufficient, state the limitation. "
        "Answer in the language of the user's question, concisely."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "system", "content": "Dashboard context: " + json.dumps(context, ensure_ascii=False)},
            *messages[-10:],
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.load(response)

        choice = data["choices"][0]
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            pieces = [part.get("text", "") for part in content
                      if isinstance(part, dict) and part.get("type") == "text"]
            combined = "\n".join(piece for piece in pieces if piece)
            if combined.strip():
                return combined.strip()

        finish_reason = choice.get("finish_reason", "unknown")
        if finish_reason == "length":
            raise RuntimeError("AI ran out of output tokens. Try a shorter question or a different model.")
        if finish_reason == "content_filter":
            raise RuntimeError("The model declined to generate a response.")
        raise RuntimeError(
            f"The model returned no visible text (finish_reason={finish_reason}). "
            "Check OPENROUTER_MODEL in Streamlit Secrets."
        )
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise RuntimeError("OpenRouter authentication failed (401). Check your API key.") from None
        if exc.code == 402:
            raise RuntimeError("OpenRouter credits are insufficient (402).") from None
        if exc.code == 429:
            raise RuntimeError("OpenRouter rate limit reached (429). Please try later.") from None
        if exc.code in (400, 404):
            raise RuntimeError(f"OpenRouter rejected the request ({exc.code}). Check the model ID.") from None
        raise RuntimeError(f"OpenRouter request failed (HTTP {exc.code}).") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("Cannot connect to OpenRouter. Please try again.") from None
    except (KeyError, IndexError, TypeError, ValueError):
        raise RuntimeError("OpenRouter returned an unexpected response format.") from None


def build_ai_context(view, affordable, recommendation_data, selected_town,
                     selected_types, budget, period, data_through):
    def value(x):
        return round(float(x), 2) if pd.notna(x) else None

    total = len(view)
    market_summary = []
    recommendation_candidates = []
    if not recommendation_data.empty:
        priced = recommendation_data.assign(
            within_budget=recommendation_data.resale_price.le(budget)
        )
        grouped = (priced.groupby(["town", "flat_type"], observed=True)
                   .agg(transaction_count=("resale_price", "size"),
                        within_budget_count=("within_budget", "sum"),
                        median_price_sgd=("resale_price", "median"),
                        p25_price_sgd=("resale_price", lambda s: s.quantile(.25)),
                        p75_price_sgd=("resale_price", lambda s: s.quantile(.75)))
                   .reset_index())
        grouped["within_budget_share_pct"] = (
            grouped.within_budget_count / grouped.transaction_count * 100
        )
        grouped["sufficient_sample"] = grouped.transaction_count.ge(10)

        market_summary = [{
            "town": str(row.town),
            "flat_type": str(row.flat_type),
            "transactions": int(row.transaction_count),
            "within_budget_sales": int(row.within_budget_count),
            "within_budget_share_pct": value(row.within_budget_share_pct),
            "median_price_sgd": value(row.median_price_sgd),
            "historical_price_p25_sgd": value(row.p25_price_sgd),
            "historical_price_p75_sgd": value(row.p75_price_sgd),
            "sufficient_sample": bool(row.sufficient_sample),
        } for row in grouped.itertuples(index=False)]

        candidates = (grouped.loc[grouped.sufficient_sample]
                      .sort_values(
                          ["within_budget_share_pct", "within_budget_count", "median_price_sgd"],
                          ascending=[False, False, True]
                      ).head(8))
        recommendation_candidates = [{
            "town": str(row.town),
            "flat_type": str(row.flat_type),
            "transactions": int(row.transaction_count),
            "within_budget_sales": int(row.within_budget_count),
            "within_budget_share_pct": value(row.within_budget_share_pct),
            "median_price_sgd": value(row.median_price_sgd),
        } for row in candidates.itertuples(index=False)]

    return {
        "scope": "Completed historical HDB resale transactions; not active listings",
        "data_through": str(data_through.date()),
        "selected_town": selected_town,
        "flat_types": [str(x) for x in selected_types],
        "transaction_period": period,
        "budget_sgd": int(budget),
        "total_historical_transactions": total,
        "historical_transactions_within_budget": len(affordable),
        "historical_affordability_share_percent": round(100 * len(affordable) / total, 2) if total else None,
        "median_historical_price_sgd": value(view.resale_price.median()),
        "median_within_budget_price_sgd": value(affordable.resale_price.median()),
        "median_within_budget_floor_area_sqm": value(affordable.floor_area_sqm.median()),
        "towns_with_matching_historical_transactions": int(affordable.town.nunique()),
        "recommendation_method": (
            "Candidates require at least 10 historical transactions and are ranked by "
            "within-budget share, within-budget sales count, then lower median price."
        ),
        "recommended_town_flat_type_candidates": recommendation_candidates,
        "historical_price_by_town_and_flat_type": market_summary,
    }

def cash(n):
    return f"S${n:,.0f}" if pd.notna(n) else '—'

def base_chart(fig, height=345):
    fig.update_layout(height=height, margin=dict(l=5,r=8,t=18,b=7),
                      paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                      font=dict(family='DM Sans', color='#465A6C',size=12),
                      legend=dict(orientation='h',yanchor='bottom',y=1.02,x=0),
                      hovermode='x unified')
    fig.update_xaxes(showgrid=False,zeroline=False)
    fig.update_yaxes(gridcolor='#E6ECF1',zeroline=False)
    return fig

if not DB.exists():
    st.error('Processed SQLite database not found. Run the existing data pipeline first: `python src/full_pipeline.py`.')
    st.stop()
try:
    df = get_data(str(DB), DB.stat().st_mtime_ns)
except Exception as exc:
    st.error(f"Cannot load transaction database: {exc}")
    st.stop()
if df.empty:
    st.error('No usable HDB transactions are available in the database.')
    st.stop()

st.markdown('''<div class="headerbar"><div class="brand">HDB<span>·</span>ATLAS</div><div class="headercaption">SINGAPORE RESALE MARKET INTELLIGENCE &nbsp; / &nbsp; BA6003</div></div>''', unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="eyebrow">THE SMARTER WAY TO FIND HOME</div><div class="hero-title">Your next home.<br><i>A clearer decision.</i></div><div class="hero-sub">Know what your budget can buy. Explore Singapore's HDB neighbourhoods, compare real resale prices, and discover more possibilities.</div></div>''',unsafe_allow_html=True)

towns = sorted(df.town.unique().tolist())
flat_types = sorted(df.flat_type.unique().tolist())
max_month = df.month_start.max()
st.markdown('<div class="sectionhead">Start exploring</div><div class="sectionnote">Choose a location you love, or explore every town within your budget.</div>',unsafe_allow_html=True)

search_panel = st.container(border=True)
with search_panel:
    st.markdown('**FIND YOUR FIT** &nbsp; <span style="color:#8B9CA6;font-size:12px">Personalise your property search</span>', unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns([1.55,1.1,1.15,1.15],gap='medium')
with c1:
    mode=st.selectbox('Location', ['All towns']+towns, index=0, help='Type a town name to search for it.')
with c2:
    selected_types=st.multiselect('Flat type', flat_types, default=[t for t in ['3 ROOM','4 ROOM','5 ROOM'] if t in flat_types] or flat_types)
with c3:
    budget=st.number_input('Your maximum budget (S$)', min_value=100000, max_value=3000000, value=600000,step=25000)
with c4:
    period=st.selectbox('Transaction period', ['Last 12 months','Last 3 years','Last 5 years','All years'])

n_months={'Last 12 months':12,'Last 3 years':36,'Last 5 years':60,'All years':None}[period]
start=max_month-pd.DateOffset(months=n_months-1) if n_months else df.month_start.min()
recent=df.loc[(df.month_start>=start)&df.flat_type.isin(selected_types)].copy()
view=recent if mode=='All towns' else recent.loc[recent.town==mode].copy()
aff=view.loc[view.resale_price<=budget].copy()

st.markdown(f'<div class="tagline">● HISTORICAL DATA THROUGH {df.month.max():%B %Y} &nbsp;·&nbsp; Not live property listings or official valuations.</div>', unsafe_allow_html=True)

tabs=st.tabs(['01 · Find affordable homes','02 · Market trends','03 · Sold transactions','04 · Our data','05 · Ask HDB AI'])
with tabs[0]:
    st.markdown('<div class="sectionhead">A better view of your budget</div><div class="sectionnote">Compare completed HDB sales at or below your budget, by town and flat type.</div>',unsafe_allow_html=True)
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Within budget', f'{len(aff):,} sales')
    k2.metric('Towns with matches', f'{aff.town.nunique():,}')
    k3.metric('Median affordable price', cash(aff.resale_price.median()))
    k4.metric('Median affordable area', f'{aff.floor_area_sqm.median():,.0f} sqm' if not aff.empty else '—')
    if view.empty:
        st.warning('No historical transactions match this town, flat type and period. Widen your search.')
    else:
        temp=view.assign(affordable=view.resale_price.le(budget))
        result=(temp.groupby(['town','flat_type']).agg(
            total_sales=('resale_price','size'), within_budget=('affordable','sum'),
            median_all_price=('resale_price','median')).reset_index())
        result['affordable_pct']=(result.within_budget/result.total_sales*100).round(1)
        st.markdown('<div class="sectionhead">Explore affordability by neighbourhood</div><div class="sectionnote">Each cell shows the share of recorded transactions at or below your selected budget.</div>',unsafe_allow_html=True)
        matrix=result.pivot(index='town',columns='flat_type',values='affordable_pct').fillna(0)
        if HAS_PLOTLY and not matrix.empty:
            chart=px.imshow(matrix, color_continuous_scale=['#F2E2DE','#F0C8A8','#C3E5DC','#187E76'],range_color=[0,100],
                            labels={'color':'Within budget (%)','x':'Flat type','y':'Town'},text_auto='.0f',aspect='auto')
            chart.update_traces(texttemplate='%{z:.0f}%', hovertemplate='%{y} · %{x}<br>Within budget: %{z:.1f}%<extra></extra>')
            chart.update_layout(height=max(280, min(850, len(matrix)*30+130)), margin=dict(l=8,r=6,t=10,b=0),
                paper_bgcolor='rgba(0,0,0,0)',font=dict(family='DM Sans',color='#44576A'),coloraxis_colorbar=dict(title='%'))
            st.plotly_chart(chart,use_container_width=True)
        else:
            st.dataframe(matrix.style.format('{:.0f}%').background_gradient(cmap='GnBu',axis=None),use_container_width=True)
        st.markdown('<div class="sectionhead">Find your next neighbourhood</div><div class="sectionnote">Rank towns and flat types using actual historical sales.</div>',unsafe_allow_html=True)
        display=result.sort_values(['within_budget','affordable_pct'],ascending=False).rename(columns={
            'town':'Town','flat_type':'Flat type','total_sales':'All sales','within_budget':'Within budget',
            'median_all_price':'Overall median (S$)','affordable_pct':'Within budget (%)'})
        st.dataframe(display,hide_index=True,use_container_width=True,column_config={
            'Overall median (S$)':st.column_config.NumberColumn(format='S$%.0f'),
            'Within budget (%)':st.column_config.ProgressColumn(min_value=0,max_value=100,format='%.1f%%')})
        st.caption('Affordability describes the share of *past registered sales* under a budget—not active listings. The median is for all transactions in that town and flat type.')

with tabs[1]:
    st.markdown('<div class="sectionhead">The market, in perspective</div><div class="sectionnote">Historical monthly median resale prices, without applying the budget cap (to avoid distorted trends).</div>',unsafe_allow_html=True)
    defaults=[mode] if mode!='All towns' else [x for x in ['TAMPINES','WOODLANDS','PUNGGOL'] if x in towns]
    compare=st.multiselect('Compare towns (up to 4)',towns,default=defaults,max_selections=4,key='trend_towns')
    trend_type=st.selectbox('Flat type for trend comparison',selected_types or flat_types,index=0,key='trend_flat') if (selected_types or flat_types) else None
    trend=recent.loc[recent.town.isin(compare)&recent.flat_type.eq(trend_type)] if trend_type else recent.iloc[0:0]
    if trend.empty:
        st.info('Choose at least one town and one flat type to see historical trends.')
    else:
        monthly=(trend.groupby(['month_start','town']).agg(median_price=('resale_price','median'),transactions=('resale_price','size')).reset_index())
        if HAS_PLOTLY:
            fig=px.line(monthly,x='month_start',y='median_price',color='town',markers=True,
                        labels={'month_start':'Transaction month','median_price':'Median resale price (S$)','town':'Town'},
                        color_discrete_sequence=['#087F7A','#244C69','#E3A65F','#7D6BC1'])
            fig.update_yaxes(tickprefix='S$',tickformat=',.0f')
            st.plotly_chart(base_chart(fig,395),use_container_width=True)
        else:
            st.line_chart(monthly.pivot(index='month_start',columns='town',values='median_price'))
        st.markdown('**Transactions per month**')
        if HAS_PLOTLY:
            volumes=px.bar(monthly,x='month_start',y='transactions',color='town',barmode='group',
                color_discrete_sequence=['#087F7A','#244C69','#E3A65F','#7D6BC1'],labels={'month_start':'Month','transactions':'Sales','town':'Town'})
            st.plotly_chart(base_chart(volumes,250),use_container_width=True)
        else:
            st.bar_chart(monthly.pivot(index='month_start',columns='town',values='transactions'))
        st.caption('Comparisons reflect observed transactions; shifts in the mix of flats sold can affect medians.')

with tabs[2]:
    st.markdown('<div class="sectionhead">Explore real transactions</div><div class="sectionnote">Inspect actual sold prices and floor areas for your selected location and flat type.</div>',unsafe_allow_html=True)
    t1,t2=st.columns([2,1])
    with t1:
        show_budget=st.toggle('Show only transactions within my budget',value=False)
    with t2:
        min_area=st.number_input('Minimum floor area (sqm)',min_value=0,max_value=500,value=0,step=5)
    hist=view.loc[view.floor_area_sqm>=min_area]
    if show_budget:
        hist=hist.loc[hist.resale_price<=budget]
    h1,h2,h3=st.columns(3)
    h1.metric('Historical transactions',f'{len(hist):,}')
    h2.metric('Median sold price',cash(hist.resale_price.median()))
    h3.metric('Median floor area',f'{hist.floor_area_sqm.median():.0f} sqm' if not hist.empty else '—')
    if hist.empty:
        st.warning('No transactions found for these filters. Try widening the period or removing the budget limit.')
    else:
        st.markdown('<div class="sectionhead">Median sold price by home size · BAR CHART</div>', unsafe_allow_html=True)
        st.markdown('<div class="sectionnote">Each bar shows the typical (median) sold price for a 10-sqm size range in your selected town and flat type. Compare bar heights to see which home sizes have higher typical resale prices.</div>', unsafe_allow_html=True)
        size_data = hist.copy()
        size_data['size_start'] = ((size_data['floor_area_sqm'] // 10) * 10).astype(int)
        size_summary = (size_data.groupby(['size_start', 'flat_type'], observed=True)
                        .agg(median_price=('resale_price', 'median'),
                             transactions=('resale_price', 'size'))
                        .reset_index())
        size_summary = size_summary.loc[size_summary['transactions'] >= 3].copy()
        size_summary['size_label'] = size_summary['size_start'].apply(
            lambda x: f'{x}–{x + 9} sqm')
        if size_summary.empty:
            st.info('There are not enough historical transactions per size range to make a reliable comparison. Try selecting more months or towns.')
        else:
            # Sort size bands numerically and keep their order in the chart.
            size_order = (size_summary[['size_start', 'size_label']]
                          .drop_duplicates().sort_values('size_start')['size_label'].tolist())
            if HAS_PLOTLY:
                bar = px.bar(
                    size_summary,
                    x='size_label', y='median_price', color='flat_type',
                    barmode='group', category_orders={'size_label': size_order},
                    custom_data=['transactions'],
                    labels={'size_label': 'Home size (sqm)',
                            'median_price': 'Typical sold price (S$)',
                            'flat_type': 'Flat type'},
                    color_discrete_sequence=['#0C877B', '#2D6DA3', '#E5A252', '#7565A4', '#CF8077']
                )
                bar.update_traces(
                    hovertemplate='<b>%{x}</b><br>Median sold price: S$%{y:,.0f}<br>Historical transactions: %{customdata[0]:,}<extra>%{fullData.name}</extra>'
                )
                bar.update_yaxes(tickprefix='S$', tickformat=',.0f')
                bar.update_layout(hovermode='closest', bargap=.22)
                st.plotly_chart(base_chart(bar, 385), use_container_width=True)
            else:
                chart_table = (size_summary.pivot_table(
                    index='size_label', columns='flat_type', values='median_price', observed=True)
                    .reindex(size_order))
                st.bar_chart(chart_table, x_label='Home size (sqm)', y_label='Median resale price (S$)',
                             use_container_width=True)
            most_common = (size_summary.sort_values('transactions', ascending=False).iloc[0])
            st.info(
                f"**How to read this chart:** Compare the heights of the bars to see the typical resale price "
                f"for each home-size range. For example, {most_common['flat_type']} flats measuring "
                f"{most_common['size_label']} had a median sold price of "
                f"{cash(most_common['median_price'])} across "
                f"{int(most_common['transactions']):,} recorded transactions in this search. "
                "The chart uses completed historical sales, not current asking prices."
            )
            st.caption('Groups with fewer than 3 recorded transactions are excluded; each median is calculated from all matching transactions in the group. Prices may also reflect town, lease and storey differences.')
            with st.expander('Show sample sizes by home size'):
                st.dataframe(size_summary[['size_label','flat_type','transactions','median_price']].rename(
                    columns={'size_label':'Home size','flat_type':'Flat type','transactions':'Historical sales','median_price':'Median sold price (S$)'}),
                    hide_index=True, use_container_width=True)
        st.markdown('**Actual recorded transactions**')
        wanted=['month','town','flat_type','block','street_name','storey_range','floor_area_sqm','remaining_lease','resale_price','price_per_sqm']
        cols=[c for c in wanted if c in hist.columns]
        listing=hist[cols].sort_values('month',ascending=False).copy()
        listing['month']=listing['month'].dt.strftime('%Y-%m')
        st.dataframe(listing,hide_index=True,use_container_width=True,height=385)
        st.download_button('↓  Download these transactions (CSV)',data=listing.to_csv(index=False).encode('utf-8'),
            file_name='hdb_historical_transactions.csv',mime='text/csv')

with tabs[3]:
    st.markdown('<div class="sectionhead">Where the numbers come from</div><div class="sectionnote">Transparent methodology and pipeline diagnostics.</div>',unsafe_allow_html=True)
    st.markdown('Data source: Singapore Government HDB resale transactions, processed by your BA6003 group pipeline. Monthly medians describe transactions registered during the relevant month, not asking prices.')
    st.markdown('**Interpretation:** A percentage within budget means historical sales at or below that amount; it does not mean that percentage of current listings is available. These analyses are indicative, not an official property valuation.')
    if REPORT.exists():
        try:
            report=json.loads(REPORT.read_text(encoding='utf-8'))
            q1,q2,q3,q4=st.columns(4)
            q1.metric('Raw rows',f"{report.get('raw_rows',0):,}")
            q2.metric('Processed rows',f"{report.get('clean_rows',0):,}")
            q3.metric('Property matched',f"{report.get('property_match_rate',0)*100:.2f}%")
            q4.metric('Flagged records',f"{report.get('quality_issues',0):,}")
            st.caption(f"Date range: {report.get('date_min','—')} to {report.get('date_max','—')} · Duplicate rows flagged: {report.get('duplicates','—')}")
        except (OSError,ValueError,TypeError) as exc:
            st.warning(f'Unable to read quality report: {exc}')
    else:
        st.info('quality_report.json is not available. Run the full pipeline to generate it.')

with tabs[4]:
    st.markdown('<div class="sectionhead">Ask HDB Atlas AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sectionnote">Ask which towns have more past sales in your budget, or request historical price ranges by town and flat type.</div>', unsafe_allow_html=True)
    ai_context = build_ai_context(
        view, aff, recent, mode, selected_types, budget, period, max_month
    )
    current_filter_key = json.dumps(ai_context, sort_keys=True)
    if st.session_state.get("hdb_chat_filter_key") != current_filter_key:
        st.session_state["hdb_chat_filter_key"] = current_filter_key
        st.session_state["hdb_chat_messages"] = []
    if "hdb_chat_messages" not in st.session_state:
        st.session_state["hdb_chat_messages"] = []

    st.info("This assistant uses historical HDB transaction summaries, not live property listings. Change filters above to change its data context.")
    if st.button("Clear conversation", key="clear_hdb_ai_chat"):
        st.session_state["hdb_chat_messages"] = []

    for message in st.session_state["hdb_chat_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("E.g. Which towns have more 4-room sales within my budget?", key="hdb_ai_input")
    if question:
        st.session_state["hdb_chat_messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Analysing the selected HDB data..."):
                try:
                    answer = ask_hdb_ai(st.session_state["hdb_chat_messages"], ai_context)
                    st.markdown(answer)
                    st.session_state["hdb_chat_messages"].append({"role": "assistant", "content": answer})
                except RuntimeError as exc:
                    st.error(str(exc))
                    # A failed call should not contaminate the next conversation turn.
                    st.session_state["hdb_chat_messages"].pop()
    st.caption("AI text may contain errors. Verify important decisions against official HDB sources.")

st.markdown('<div class="smallfooter"><span>© HDB ATLAS &nbsp;·&nbsp; BA6003 GROUP PROJECT</span><span>Built for better decisions &nbsp;·&nbsp; Historical analytics, not an official valuation</span></div>',unsafe_allow_html=True)
