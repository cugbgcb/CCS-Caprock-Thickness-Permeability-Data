"""Verify selected historical rows and criterion flags, not the full field scan."""
import csv
from collections import Counter
from decimal import Decimal as D
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((ROOT/'results/diagnostics/historical_aqueous_pressure_flags.json').read_text())
objects=json.loads((ROOT/'models/manifest.json').read_text())['files']
cases={c['case']:c for c in record['cases']};assert len(cases)==48
hashed={}
for name,c in cases.items():
    for filename,expected in c['input_sha256'].items():
        if filename=='CO2TAB':continue # Licensed table is intentionally absent.
        item=next(v for v in objects if v['case']==name and v['filename']==filename)
        assert item['sha256']==expected
        path=ROOT/item['object']
        if item['object'] not in hashed:hashed[item['object']]=sha(path)
        assert hashed[item['object']]==expected
    assert c['saved_times_s']==sorted(set(c['saved_times_s']))
coverage=record['reported_audit_coverage']
assert coverage==dict(noncontinuation_cases=48,saved_fields=1516,cell_states=39567600)
assert sum(len(c['saved_times_s']) for c in cases.values())==1516
seen=set();counts=Counter()
for s in record['selected_flagged_states']:
    assert s['case'] in cases and s['time_s'] in cases[s['case']]['saved_times_s']
    key=s['case'],s['time_s'],s['cell'];assert key not in seen;seen.add(key)
    raw=next(csv.reader([s['raw_csv_row']]));assert len(raw)==len(record['columns']) and raw[0].strip()==s['cell']
    v={k:float(x.replace('D','E')) for k,x in zip(record['columns'][1:],raw[1:])}
    assert all(math.isfinite(x) for x in v.values())
    pressure=v['PRES']+v['PCAP_GL']
    assert v['PRES']>0 and v['SAT_L']>0 and v['DEN_L']>0 and v['REL_L']==0 and pressure<0
    assert math.isclose(pressure,s['reconstructed_aqueous_transport_pressure_Pa'],rel_tol=1e-13,abs_tol=1e-7)
    assert all(0<=v[k]<=1 for k in ('SAT_G','SAT_L','SAT_S'))
    assert abs(v['SAT_G']+v['SAT_L']+v['SAT_S']-1)<2e-10
    counts[s['case']]+=1
assert len(seen)==56 and len(counts)==5
assert all(counts[name]==c['reported_negative_occupied_water_states'] for name,c in cases.items())
for name,expected in record['primary_tables_sha256'].items():assert sha(ROOT/'results/primary_response'/name)==expected
cohort=list(csv.DictReader((ROOT/'results/primary_response/case_summary.csv').open()))
qualified=[]
for row in csv.DictReader((ROOT/'results/primary_response/threshold_brackets.csv').open()):
    endpoints=[]
    for side in ('lower','upper'):
        members=[c for c in cohort if D(c['permeability_m2'])==D(row['permeability_m2']) and D(c['thickness_m'])==D(row['L_'+side+'_m'])]
        assert len(members)==1;case=members[0]['case']
        if counts[case]:endpoints.append(dict(side=side,case=case,negative_saved_states=counts[case]))
    if endpoints:qualified.append(dict(threshold_pct=row['threshold_pct'],permeability_m2=row['permeability_m2'],
        L_lower_m=row['L_lower_m'],L_upper_m=row['L_upper_m'],flagged_endpoints=endpoints,
        status='conditional_on_capillary_and_thermophysical_validation'))
assert qualified==record['qualified_primary_brackets']
print('Verified56 selected historical rows, input identities and affected1%/5% bracket flags; full spatial scan and scientific validity are not independently certified.')
