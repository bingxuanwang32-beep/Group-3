from pathlib import Path
import json
import sqlite3
import pandas as pd
import streamlit as st
ROOT=Path(__file__).resolve().parents[1];DB=ROOT/'output/hdb_full.sqlite'
st.set_page_config(page_title='HDB Resale Price Explorer',layout='wide')
st.title('HDB Resale Price Explorer')
st.caption('Explore historical HDB resale prices and filter transactions by location, flat type, size and budget.')
if not DB.exists():st.error('Please run python src/full_pipeline.py first.');st.stop()
with sqlite3.connect(DB) as c:
 d=pd.read_sql_query('SELECT * FROM resale_transactions',c)
d['month']=pd.to_datetime(d['month'], errors='coerce')
if d.empty:st.stop()
towns=st.sidebar.multiselect('Town',sorted(d.town.unique()),default=sorted(d.town.unique())[:5])
types=st.sidebar.multiselect('Flat type',sorted(d.flat_type.unique()),default=sorted(d.flat_type.unique()))
area=st.sidebar.slider('Floor area (sqm)',int(d.floor_area_sqm.min()),int(d.floor_area_sqm.max()),(int(d.floor_area_sqm.min()),int(d.floor_area_sqm.max())))
budget=st.sidebar.number_input('Maximum budget (SGD)',min_value=0,max_value=int(d.resale_price.max()),value=int(d.resale_price.quantile(.75)),step=10000)
st.sidebar.caption('Set budget to 0 to remove the budget filter.')

f=d[d.town.isin(towns)&d.flat_type.isin(types)&d.floor_area_sqm.between(*area)]
if budget > 0:
    f=f[f.resale_price <= budget]

a,b,c=st.columns(3)
a.metric('Matching transactions',f'{len(f):,}')
b.metric('Median price',f'S${f.resale_price.median():,.0f}' if len(f) else 'No records')
c.metric('Median S$/sqm',f'S${f.price_per_sqm.median():,.0f}' if len(f) else 'No records')

if f.empty:
    st.warning('No transactions match the current filters. Try increasing the budget or widening the filters.')
else:
    st.subheader('Monthly median price')
    st.line_chart(f.set_index('month').resale_price.resample('MS').median())
    st.subheader('Filtered transactions')
    st.dataframe(f[['month','town','flat_type','block','storey_range','floor_area_sqm','remaining_lease','resale_price','price_per_sqm']],hide_index=True)
    st.download_button('Download filtered CSV',f.to_csv(index=False),'filtered_resale.csv','text/csv')

st.divider()
st.subheader('Data quality summary')
report_path=ROOT/'output/quality_report.json'
if report_path.exists():
    report=json.loads(report_path.read_text(encoding='utf-8'))
    q1,q2,q3,q4=st.columns(4)
    q1.metric('Raw rows',f"{report['raw_rows']:,}")
    q2.metric('Usable rows',f"{report['clean_rows']:,}")
    q3.metric('Property match rate',f"{report['property_match_rate']*100:.4f}%")
    q4.metric('Flagged records',f"{report['quality_issues']:,}")
    st.caption(f"Date range: {report['date_min']} to {report['date_max']} | Duplicate rows detected: {report['duplicates']:,}")
else:
    st.info('Run the full pipeline first to display the data quality report.')

st.caption('Indicative analysis only; not an official valuation.')
