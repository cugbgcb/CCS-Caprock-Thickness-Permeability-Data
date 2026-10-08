"""Audit retained INFILE controls and optional raw continuation overlaps, read-only."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
YEAR=31536000.
MFINAL=12500003160.

def value(text):
    return float(text.replace('D','E')) if text.strip() else None

def controls(path):
    lines=path.read_text().splitlines()
    i=next(i for i,line in enumerate(lines) if line.startswith('PARAM'))
    a,b,c=[s.ljust(80) for s in lines[i+1:i+4]]
    return dict(max_newton_iterations=int(a[:2]),initial_step_s=value(b[20:30]),max_step_s=value(b[30:40]),
                relative_tolerance=value(c[:10]),absolute_tolerance=value(c[10:20]),
                mobility_upstream_weight=value(c[30:40]),newton_increment_weight=value(c[40:50]),
                derivative_increment=value(c[50:60]),
                mop={str(n):int(a[15+n].strip() or '0') for n in (11,12,16,17,18,21)})

def balances(path):
    records={};t=None;domain=None;frame={}
    def finish():
        if frame:
            assert set(frame)=={'MAQUO','OVERB','EAUCL','MTSIM','SYSTEM'},(path,t,frame)
            assert t not in records,(path,t)
            records[t]=frame.copy()
    with path.open(errors='replace') as stream:
        for line in stream:
            m=re.search(r'THE TIME IS\s+([\d.Ee+-]+)\s+SECONDS',line)
            if m:finish();frame={};t=float(m[1]);domain=None
            m=re.search(r'Balances for domain #\s*\d+,\s*\*(\w+)\*',line,re.I)
            if m:domain=m[1]
            if 'balances for entire system' in line.lower():domain='SYSTEM'
            if domain and re.search(r'\bTOTAL\s+\*',line):
                fields=line.split('*')[-1].split();assert len(fields)==4 and t is not None
                s=fields[2].replace('D','E')
                if 'E' not in s.upper():s=re.sub(r'(?<=\d)([+-]\d+)$',r'E\1',s)
                frame[domain]=float(s);domain=None
    finish();assert records
    return records

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw-root',type=Path);ap.add_argument('--output',type=Path,default=ROOT/'provenance/historical_numerical_controls_inputs.json');args=ap.parse_args()
    manifest=json.loads((ROOT/'models/manifest.json').read_text())
    provenance=json.loads((ROOT/'results/historical/provenance.json').read_text())
    files={f['case']:f for f in manifest['files'] if f['filename']=='INFILE'}
    output={'parameter_authority':'https://tough.lbl.gov/assets/files/Tough3/TOUGH3_Users_Guide_v2.pdf','cases':[],'continuations':[]}
    for case in provenance['cases']:
        name=case['case'];f=files[name];path=args.raw_root/name/'INFILE' if args.raw_root else ROOT/f['object']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']==case['input_sha256']
        output['cases'].append(dict(case=name,input_sha256=f['sha256'],controls=controls(path)))
        if not any('/continue/' in s for s in case['sources']):continue
        f=files[name+'/continue'];path=args.raw_root/name/'continue/INFILE' if args.raw_root else ROOT/f['object']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256']
        item=dict(case=name,input_sha256=f['sha256'],controls=controls(path),merge_policy='Continuation overwrites original balance at identical printed time; distinct times retained in sorted order')
        if args.raw_root:
            original=balances(args.raw_root/name/'OUTPUT');continued=balances(args.raw_root/name/'continue/OUTPUT')
            shared=sorted(original.keys() & continued.keys())
            overlaps=[]
            for t in shared:
                a,b=original[t],continued[t]
                overlaps.append(dict(time_s=t,time_years=t/YEAR,system_difference_kg=b['SYSTEM']-a['SYSTEM'],above_difference_kg=(b['OVERB']+b['MAQUO'])-(a['OVERB']+a['MAQUO']),R_final_difference_percentage_points=100*((b['OVERB']+b['MAQUO'])-(a['OVERB']+a['MAQUO']))/MFINAL))
            item.update(original_time_range_s=[min(original),max(original)],continuation_time_range_s=[min(continued),max(continued)],overlap=overlaps)
            retained=list(csv.DictReader((ROOT/'results/historical/mass_timeseries.csv').open()))
            merged={**original,**continued}
            for r in retained:
                if r['case']==name:
                    raw=merged[float(r['time_s'])]
                    assert all(float(r[k])==raw[k] for k in raw),name
            item['retained_merged_inventories_verified']=True
        output['continuations'].append(item)
    assert len(output['cases'])==51 and len(output['continuations'])==3
    assert all(x['controls']==output['cases'][0]['controls'] for x in output['cases'])
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'original_cases':len(output['cases']),'continuations':output['continuations']},indent=2))

if __name__=='__main__':main()
