from pathlib import Path
import csv,json,math
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'results/historical';rows=list(csv.DictReader((p/'mass_timeseries.csv').open()))
prev={};peaks={}
for r in rows:
 t=float(r['time_s']);injected=7.92745*min(t,50*31536000);above=float(r['above_kg']);r['injected_to_date_kg']=injected
 r['R_mig_current_pct']=100*above/injected if injected>0 else ''
 r['net_migration_t_per_year']='';case=r['case']
 if case in prev:
  a=prev[case];dt=(t-float(a['time_s']))/31536000
  rate=(above-float(a['above_kg']))/1000/dt;r['net_migration_t_per_year']=rate
  if case not in peaks or rate>peaks[case]['rate']:peaks[case]=dict(rate=rate,start_year=float(a['time_year']),end_year=float(r['time_year']))
 prev[case]=r
with (p/'mass_timeseries.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(p/'net_rate_peaks.json').write_text(json.dumps(peaks,indent=2))
for L in ['1.57','4.97']:print(L,peaks[f'Stage01_Scn01-05_H{L}m/k1e-16'])
