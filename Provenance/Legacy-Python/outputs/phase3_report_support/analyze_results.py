import sys,json,math
from pathlib import Path
import numpy as np,pandas as pd
from docx import Document
from collections import Counter
root=Path(__file__).resolve().parents[2]; out=Path(__file__).resolve().parent;out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'scripts'))
import formal_analysis as f
panel=pd.read_csv(root/'data/clean/clean_daily_panel.csv',parse_dates=['date_utc'])
def analyze(cutoff,recompute):
 p=panel[panel.date_utc<=cutoff].copy()
 rows=[];episodes=[];brows=[];changes=[];bays=[];errors=[]
 for aid,g in p.groupby('asset_id',sort=False):
  g=g.sort_values('date_utc').reset_index(drop=True); n=len(g); y=g.log_price.to_numpy(); dates=g.date_utc
  a=dict(asset_id=aid,symbol=g.symbol.iloc[0],asset_type=g.asset_type.iloc[0])
  if recompute:
   r0,m=f.psy_window_size(n);sa,bs,start=f.recursive_adf_statistics(y,m)
   cv=np.array([f.critical_value('SADF',.95,i+1) if np.isfinite(bs[i]) else np.nan for i in range(n)])
   above=bs>cv; runs=np.split(np.flatnonzero(above),np.flatnonzero(np.diff(np.flatnonzero(above))>1)+1)
   row={**a,'observations':n,'minimum_window_days':m,'sadf_statistic':float(np.nanmax(sa)),'gsadf_statistic':float(np.nanmax(bs))}
   for q in [.90,.95,.99]:
    row[f'sadf_cv_{int(q*100)}']=f.critical_value('SADF',q,n)
    row[f'gsadf_cv_{int(q*100)}']=f.critical_value('GSADF',q,n)
    row[f'sadf_reject_{int(q*100)}']=bool(row['sadf_statistic']>row[f'sadf_cv_{int(q*100)}'])
    row[f'gsadf_reject_{int(q*100)}']=bool(row['gsadf_statistic']>row[f'gsadf_cv_{int(q*100)}'])
   row['above95_days']=int(above.sum());row['longest95_run']=int(max(map(len,runs),default=0))
   episodes+=f.stamp_episodes(dates,bs,cv,30,.95,a,1)
   cc,ss=f.change_point_outputs(g,a,30,2);changes+=cc
   bb=pd.DataFrame(f.bayesian_online_adf(y,dates,365,.5));bb['symbol']=a['symbol'];bb['asset_type']=a['asset_type'];bays.append(bb)
   bsrows=pd.DataFrame({'date_utc':dates,'bsadf_statistic':bs,'cv95':cv,'above95':above});bsrows['symbol']=a['symbol'];brows.append(bsrows)
   e=int(np.nanargmax(bs));s=int(start[e]);x=y[s:e];dy=np.diff(y[s:e+1]);X=np.column_stack([np.ones(len(x)),x])
   beta=np.linalg.lstsq(X,dy,rcond=None)[0];res=dy-X@beta
   t=beta[1]/math.sqrt((res@res/(len(x)-2))*np.linalg.inv(X.T@X)[1,1]);errors.append(abs(t-bs[e]))
  rows.append(row if recompute else a)
 return p,pd.DataFrame(rows),pd.DataFrame(episodes),pd.DataFrame(changes),pd.concat(bays,ignore_index=True),pd.concat(brows,ignore_index=True),max(errors,default=0)
p,june,je,jc,jb,jbs,err=analyze(pd.Timestamp('2026-06-30'),True)
june.to_csv(out/'june_test_summary.csv',index=False);je.to_csv(out/'june_episodes.csv',index=False);jc.to_csv(out/'june_change_points.csv',index=False);jb.to_csv(out/'june_bayesian.csv',index=False);jbs.to_csv(out/'june_bsadf.csv',index=False)
full=pd.read_csv(root/'data/analysis/psy_test_summary.csv')
ep=pd.read_csv(root/'data/analysis/psy_bubble_episodes.csv')
cp=pd.read_csv(root/'data/analysis/change_points.csv')
bay=pd.read_csv(root/'data/analysis/bayesian_online_diagnostics.csv',parse_dates=['date_utc'])
bs=pd.read_csv(root/'data/analysis/psy_bsadf_series.csv',parse_dates=['date_utc'])
def sums(t,e,c,b,price):
 fan=t[t.asset_type.eq('fan_token')];ef=e[e.asset_type.eq('fan_token')&e.confidence_level.eq(.95)] if len(e) else e
 return dict(fan_prices=int(price[price.asset_type.eq('fan_token')].close_usd.notna().sum()),series=len(t),sadf5=int(fan.sadf_reject_95.sum()),gsadf10=int(fan.gsadf_reject_90.sum()),gsadf5=int(fan.gsadf_reject_95.sum()),gsadf1=int(fan.gsadf_reject_99.sum()),fan_episodes5=len(ef),mean_cp=int((c.asset_type.eq('fan_token')&c.dimension.eq('return_mean')).sum()),vol_cp=int((c.asset_type.eq('fan_token')&c.dimension.eq('log_squared_return')).sum()),benchmark_cp=int(c.asset_type.eq('benchmark').sum()),bay_rows=len(b))
summary={'june':sums(june,je,jc,jb,p),'september':sums(full,ep,cp,bay,panel),'max_ols_t_error':err}
tables={}
for label,t,e,c,b,bs0 in [('june',june,je,jc,jb,jbs),('september',full,ep,cp,bay,bs)]:
 agg=c[c.asset_type.eq('fan_token')].groupby(['symbol','dimension']).size().unstack(fill_value=0).reindex(columns=['return_mean','log_squared_return'],fill_value=0)
 stats=[]
 for sym,g in b[b.asset_type.eq('fan_token')].groupby('symbol'):
  v=g.bayesian_explosive_slope_probability
  stats.append(dict(symbol=sym,mean_probability=float(v.mean()),maximum_probability=float(v.max()),days_ge95=int((v>=.95).sum()),share_ge95=float((v>=.95).mean()),last_probability=float(v.iloc[-1]),maximum_cp_probability=float(g.bayesian_change_point_probability.max())))
 bstats=pd.DataFrame(stats)
 merged=t[t.asset_type.eq('fan_token')].merge(agg,left_on='symbol',right_index=True,how='left').merge(bstats,on='symbol',how='left')
 if label=='september':
  dd=[]
  for sym,g in bs0.groupby('symbol'):
   pos=g[g.bsadf_above_95pct_critical_value].date_utc
   runs=np.split(pos.to_numpy(),np.flatnonzero(np.diff(pos.to_numpy()).astype('timedelta64[D]').astype(int)>1)+1)
   dd.append(dict(symbol=sym,above95_days=len(pos),longest95_run=max(map(len,runs),default=0)))
  merged=merged.merge(pd.DataFrame(dd),on='symbol',how='left')
 merged.to_csv(out/(label+'_combined.csv'),index=False)
 tables[label]=merged.to_dict('records')
summary['tables']=tables
summary['june_episodes']=je.to_dict('records')
summary['september_episodes']=[]
for row in ep[(ep.asset_type.eq('fan_token'))&(ep.confidence_level.eq(.95))].to_dict('records'):
 sym=row['symbol'];start=pd.Timestamp(row['start_date']);end=pd.Timestamp(row['end_date'])
 bg=bay[bay.symbol.eq(sym)&bay.date_utc.between(start,end)]
 cg=cp[cp.symbol.eq(sym)].copy();cg['change_date']=pd.to_datetime(cg.change_date);cg=cg[cg.change_date.between(start-pd.Timedelta(days=15),end+pd.Timedelta(days=15))]
 raw=panel[panel.symbol.eq(sym)&panel.date_utc.between(start,end)]
 row.update(bayes_mean=float(bg.bayesian_explosive_slope_probability.mean()),bayes_share95=float(bg.bayesian_explosive_slope_probability.ge(.95).mean()),price_change_pct=float((raw.close_usd.iloc[-1]/raw.close_usd.iloc[0]-1)*100),cp_nearby=cg[['change_date','dimension']].astype(str).to_dict('records'))
 summary['september_episodes'].append(row)
summary['date_range']={a:[str(g.date_utc.min().date()),str(g.date_utc.max().date()),len(g)] for a,g in p.groupby('symbol')}
summary['cp_totals_sep']=cp.groupby(['asset_type','dimension']).size().to_dict().__str__()
d=Document(root/'references/FRAM_PHASE_1_REPORT.docx')
summary['ref_fonts']={str(k):v for k,v in Counter((run.font.name,run.font.size.pt if run.font.size else None) for par in d.paragraphs for run in par.runs).most_common()}
(out/'analysis.json').write_text(json.dumps(summary,indent=2,default=str))
print(json.dumps({k:v for k,v in summary.items() if k not in ['tables','date_range','ref_fonts']},indent=2,default=str))
print('JUNE TABLE',june[['symbol','sadf_statistic','gsadf_statistic','gsadf_reject_95','longest95_run']].to_string(index=False))
print('FONTS',summary['ref_fonts'])
