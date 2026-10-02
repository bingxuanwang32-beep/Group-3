from pathlib import Path
import argparse,json,sqlite3,hashlib,re,logging
import pandas as pd, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
ROOT=Path(__file__).resolve().parents[1]
logger=logging.getLogger("hdb_pipeline")
RESALE_REQ=['month','town','flat_type','block','street_name','storey_range','floor_area_sqm','flat_model','lease_commence_date','remaining_lease','resale_price']
PROP_REQ=['blk_no','street','year_completed','max_floor_lvl','residential','total_dwelling_units']

def norm(s): return s.astype('string').str.strip().str.upper().str.replace(r'\s+',' ',regex=True)
def parse_storey(s):
 m=s.astype('string').str.extract(r'(\d+)\s+TO\s+(\d+)');return (pd.to_numeric(m[0],errors='coerce')+pd.to_numeric(m[1],errors='coerce'))/2
def parse_lease(s):
 y=pd.to_numeric(s.astype('string').str.extract(r'(\d+)\s+YEAR')[0],errors='coerce').fillna(0);mo=pd.to_numeric(s.astype('string').str.extract(r'(\d+)\s+MONTH')[0],errors='coerce').fillna(0);return y+mo/12
def clean_resale(x):
 miss=set(RESALE_REQ)-set(x); assert not miss,f'Missing resale columns: {miss}'
 d=x.copy();d.columns=d.columns.str.strip().str.lower()
 for c in ['town','flat_type','block','street_name','storey_range','flat_model','remaining_lease']:d[c]=norm(d[c])
 d['month']=pd.to_datetime(d.month,format='%Y-%m',errors='coerce');d['floor_area_sqm']=pd.to_numeric(d.floor_area_sqm,errors='coerce');d['resale_price']=pd.to_numeric(d.resale_price,errors='coerce');d['lease_commence_date']=pd.to_numeric(d.lease_commence_date,errors='coerce')
 d['storey_mid']=parse_storey(d.storey_range);d['remaining_lease_years']=parse_lease(d.remaining_lease);d['price_per_sqm']=d.resale_price/d.floor_area_sqm;d['property_key']=norm(d.block)+'|'+norm(d.street_name)
 d['quality_issue']='';
 def flag(mask,msg):d.loc[mask.fillna(True),'quality_issue']+=msg+';'
 for c in ['month','town','flat_type','block','street_name','floor_area_sqm','resale_price']:flag(d[c].isna(),'missing_'+c)
 flag(d.floor_area_sqm.le(0),'nonpositive_area');flag(d.resale_price.le(0),'nonpositive_price');flag(d.storey_mid.isna(),'invalid_storey');flag(d.remaining_lease_years.isna(),'invalid_lease')
 d['quality_issue']=d.quality_issue.str.rstrip(';');return d

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--resale',type=Path,default=ROOT/'data/raw/HDBResalePrices.csv');ap.add_argument('--property',type=Path,default=ROOT/'data/raw/HDBPropertyInformation.csv');ap.add_argument('--output',type=Path,default=ROOT/'output');a=ap.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=True);(o/'figures').mkdir(exist_ok=True)
 formatter=logging.Formatter("%(asctime)s | %(levelname)s | %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
 logger.setLevel(logging.INFO)
 if not logger.handlers:
  console=logging.StreamHandler(); console.setFormatter(formatter); logger.addHandler(console)
  file_handler=logging.FileHandler(o/'pipeline.log',encoding='utf-8'); file_handler.setFormatter(formatter); logger.addHandler(file_handler)
 logger.info("Pipeline started")
 raw=pd.read_csv(a.resale);prop=pd.read_csv(a.property,dtype='string')
 logger.info("Loaded resale data: %s rows",len(raw)); logger.info("Loaded property data: %s rows",len(prop))
 r=clean_resale(raw); logger.info("Resale cleaning completed")
 p=prop.copy(); assert set(PROP_REQ)<=set(p.columns); logger.info("Required columns verified")
 p['property_key']=norm(p.blk_no)+'|'+norm(p.street);p['year_completed']=pd.to_numeric(p.year_completed,errors='coerce');p['max_floor_lvl']=pd.to_numeric(p.max_floor_lvl,errors='coerce');p['total_dwelling_units']=pd.to_numeric(p.total_dwelling_units,errors='coerce');p=p.drop_duplicates('property_key')
 r=r.merge(p[['property_key','year_completed','max_floor_lvl','total_dwelling_units']],on='property_key',how='left',validate='many_to_one',indicator='property_match');r['transaction_year']=r.month.dt.year;r['building_age_at_sale']=r.transaction_year-r.year_completed;r['quality_issue']=r.quality_issue.where(r.property_match.eq('both'),r.quality_issue+';unmatched_property')
 logger.info("Property matching rate: %.4f%%",r.property_match.eq('both').mean()*100)
 logger.info("Unmatched property records: %s",int(r.property_match.ne('both').sum()))
 r.to_csv(o/'resale_cleaned_all.csv',index=False);r[r.quality_issue.eq('')].to_csv(o/'resale_analysis.csv',index=False);r[r.property_match.ne('both')].to_csv(o/'unmatched_property_records.csv',index=False);r[r.quality_issue.ne('')].to_csv(o/'quality_issues.csv',index=False)
 good=r[r.quality_issue.eq('')].copy();good=good.sort_values('month'); logger.info("Rows passing quality checks: %s",len(good)); logger.info("Rows flagged: %s",int((r.quality_issue!='').sum()))
 # SQLite tables
 with sqlite3.connect(o/'hdb_full.sqlite') as c: good.to_sql('resale_transactions',c,if_exists='replace',index=False);p.to_sql('property_inventory',c,if_exists='replace',index=False)
 logger.info("SQLite database created")
 good.groupby('month',as_index=False).agg(median_price=('resale_price','median'),mean_price=('resale_price','mean'),transactions=('resale_price','size')).to_csv(o/'monthly_summary.csv',index=False)
 good.groupby(['town','flat_type'],as_index=False).agg(median_price=('resale_price','median'),median_psqm=('price_per_sqm','median'),transactions=('resale_price','size')).to_csv(o/'town_flat_summary.csv',index=False)
 # time split model, no future leakage
 cut=good.month.quantile(.8);tr=good[good.month<=cut];te=good[good.month>cut];features=['town','flat_type','flat_model','floor_area_sqm','storey_mid','remaining_lease_years','lease_commence_date','transaction_year'];cats=['town','flat_type','flat_model'];nums=list(set(features)-set(cats));prep=ColumnTransformer([('cat',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('onehot',OneHotEncoder(handle_unknown='ignore'))]),cats),('num',SimpleImputer(strategy='median'),nums)])
 model=Pipeline([('prep',prep),('model',RandomForestRegressor(n_estimators=150,max_depth=20,min_samples_leaf=2,n_jobs=-1,random_state=42))]);logger.info("Training rows: %s; testing rows: %s",len(tr),len(te)); model.fit(tr[features],tr.resale_price);pred=model.predict(te[features]);metrics={'train_rows':len(tr),'test_rows':len(te),'cutoff_month':str(cut.date()),'MAE':float(mean_absolute_error(te.resale_price,pred)),'RMSE':float(mean_squared_error(te.resale_price,pred)**0.5),'R2':float(r2_score(te.resale_price,pred))};(o/'model_metrics.json').write_text(json.dumps(metrics,indent=2)); logger.info("Model metrics: MAE=%.2f RMSE=%.2f R2=%.3f",metrics['MAE'],metrics['RMSE'],metrics['R2']); pd.DataFrame({'actual':te.resale_price,'predicted':pred,'month':te.month}).to_csv(o/'test_predictions.csv',index=False)
 # plots
 plt.rcParams.update({'figure.dpi':140,'axes.spines.top':False,'axes.spines.right':False});monthly=pd.read_csv(o/'monthly_summary.csv');plt.figure(figsize=(10,5));plt.plot(monthly.month,monthly.median_price,color='#147d92');plt.xticks(monthly.month[::12],rotation=45);plt.ylabel('Median resale price (SGD)');plt.title('Monthly median HDB resale price');plt.tight_layout();plt.savefig(o/'figures/01_monthly_price.png');plt.close()
 top=good.groupby('town').resale_price.median().sort_values().tail(15);plt.figure(figsize=(9,6));top.plot.barh(color='#e59b3d');plt.xlabel('Median resale price (SGD)');plt.title('15 towns with highest median prices');plt.tight_layout();plt.savefig(o/'figures/02_town_prices.png');plt.close()
 plt.figure(figsize=(8,5));plt.scatter(te.resale_price,pred,s=5,alpha=.2);mn,mx=te.resale_price.min(),te.resale_price.max();plt.plot([mn,mx],[mn,mx],'r--');plt.xlabel('Actual');plt.ylabel('Predicted');plt.title('Time-based test predictions');plt.tight_layout();plt.savefig(o/'figures/03_actual_predicted.png');plt.close()
 plt.figure(figsize=(8,5));plt.hist(good.price_per_sqm,bins=50,color='#147d92');plt.xlabel('Price per sqm (SGD)');plt.ylabel('Transactions');plt.title('Resale price per square metre');plt.tight_layout();plt.savefig(o/'figures/04_price_psqm.png');plt.close()
 report={'raw_rows':len(raw),'clean_rows':len(good),'quality_issues':int((r.quality_issue!='').sum()),'duplicates':int(raw.duplicated().sum()),'property_match_rate':float(r.property_match.eq('both').mean()),'date_min':str(good.month.min().date()),'date_max':str(good.month.max().date()),**metrics};(o/'quality_report.json').write_text(json.dumps(report,indent=2)); logger.info("Pipeline completed successfully"); print(json.dumps(report,indent=2))
if __name__=='__main__':main()
