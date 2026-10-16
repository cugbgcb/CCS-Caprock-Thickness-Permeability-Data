"""Reproduce the 47-case primary cohort and sampled brackets using standard Python."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
historical=ROOT/'results/historical/case_summary.csv'
continuations=ROOT/'results/interpolation_audit/continuation_exclusion.json'
assert sha(historical)=='db304d28a8f18538d3b589cae77a59ab41ac455da0e253aba36341b16ca72900'
assert sha(continuations)=='cbcbf652b019febc322d3599d3369578b07a79d0cabedc40d76f776156117c1d'
with historical.open() as stream:
    all_cases=list(csv.DictReader(stream))
assert len(all_cases)==51 and len({v['case'] for v in all_cases})==51
parameters=[v for v in all_cases if v['stage']!='S0']
assert len(parameters)==50
excluded=set(json.loads(continuations.read_text())['omitted_cases'])
assert excluded=={'Stage01_Scn01-05_H1.57m/k1e-15','Stage02/Stage02_H1.00m/k0.5e-17','Stage02/Stage02_H2.57m/k1e-17'}
assert excluded<={v['case'] for v in parameters}
primary=[v for v in parameters if v['case'] not in excluded]
assert len(primary)==47
inside=lambda v: 1.57<=float(v['thickness_m'])<=157 and 1e-19<=float(v['permeability_m2'])<=1e-15
assert sum(map(inside,primary))==43
brackets=[]
for criterion in (.1,1,5):
    for permeability in sorted({float(v['permeability_m2']) for v in primary}):
        members=sorted([v for v in primary if float(v['permeability_m2'])==permeability],key=lambda v:float(v['thickness_m']))
        for left,right in zip(members,members[1:]):
            a,b=float(left['R_mig_pct']),float(right['R_mig_pct'])
            assert math.isfinite(a) and math.isfinite(b)
            if (a-criterion)*(b-criterion)>=0:
                continue
            assert a>0 and b>0
            lower,upper=float(left['thickness_m']),float(right['thickness_m'])
            weight=(math.log(criterion)-math.log(a))/(math.log(b)-math.log(a))
            estimate=lower*(upper/lower)**weight
            assert lower<=estimate<=upper
            brackets.append(dict(threshold_pct=criterion,permeability_m2=permeability,
                L_lower_m=lower,L_upper_m=upper,R_lower_pct=a,R_upper_pct=b,L_loglinear_diagnostic_m=estimate))
one=[v for v in brackets if v['threshold_pct']==1]
assert [(v['permeability_m2'],v['L_lower_m'],v['L_upper_m']) for v in one]==[
    (5e-17,2.57,6.97),(1e-16,4.97,10.97),(5e-16,23.7,33.7),(1e-15,15.7,49.7)]
assert not any(v['threshold_pct']==.1 and v['permeability_m2']==5e-18 for v in brackets)
out=ROOT/'results/primary_response';out.mkdir(exist_ok=True)


def write_csv(path,rows):
    text=io.StringIO(newline='')
    writer=csv.DictWriter(text,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    path.write_bytes(text.getvalue().encode('utf-8'))


write_csv(out/'case_summary.csv',primary)
write_csv(out/'threshold_brackets.csv',brackets)
record=dict(historical_archive_commit='3e6359f74e8df1e18c2cbcdd6502b4192703d034',
    archived_parameter_cases=50,primary_parameter_cases=47,in_domain_primary_cases=43,retained_guard_points=4,
    excluded_cases=sorted(excluded),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in (historical,continuations,Path(__file__).resolve())},
    primary_case_summary_sha256=sha(out/'case_summary.csv'),primary_brackets_sha256=sha(out/'threshold_brackets.csv'),
    scientific_validation_complete=False,
    scope='Selection and adjacent-thickness log-linear bracket arithmetic from unchanged archived endpoints. '
          'All continuation cases excluded from primary cohort; S0 is a separate reference. '
          'No grid/time convergence, thermophysical validity, corrected simulation or extrapolated threshold is established. '
          'Reporting domain is 1.57–157 m and 1e-19–1e-15 m²; guard points are retained for traceability. '
          'This script does not regenerate interpolated figures or read large spatial outputs.')
(out/'selection.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(archived_parameter_cases=50,primary_parameter_cases=47,in_domain_primary_cases=43,retained_guard_points=4,one_percent_brackets=one),indent=2))
