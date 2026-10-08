"""Sampling sensitivity to omitting three relaxed-tolerance continuation cases.
This diagnostic is not a tolerance rerun or validation of omitted/retained cases.
"""
import csv,json,hashlib,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.tri as tri
from scipy.optimize import brentq
import scipy
ROOT=Path(__file__).resolve().parents[1]

def intersections(ip,k,criterion):
    y=np.linspace(np.log10(1.57),np.log10(157),1001)
    z=ip(np.full_like(y,np.log10(k)),y)-np.log10(criterion)
    roots=[]
    for i in range(len(y)-1):
        if np.ma.is_masked(z[i]) or np.ma.is_masked(z[i+1]):continue
        if z[i]==0:roots.append(10**y[i])
        elif z[i]*z[i+1]<0:
            roots.append(10**brentq(lambda a:float(ip(np.log10(k),a))-np.log10(criterion),y[i],y[i+1]))
    return roots

def main():
    source=ROOT/'results/historical/case_summary.csv'
    rows=[r for r in csv.DictReader(source.open()) if r['stage']!='S0']
    control=ROOT/'provenance/historical_numerical_controls.json'
    omitted={r['case'] for r in json.loads(control.read_text())['continuations']}
    assert len(omitted)==3 and len(rows)==50
    results=[]
    for label,rr in [('all_50',rows),('omit_3_continuations',[r for r in rows if r['case'] not in omitted])]:
        x=np.log10([float(r['permeability_m2']) for r in rr]);y=np.log10([float(r['thickness_m']) for r in rr]);z=np.log10([max(float(r['R_mig_pct']),1e-10) for r in rr]);t=tri.Triangulation(x,y)
        for method in ('linear','cubic'):
            ip=tri.LinearTriInterpolator(t,z) if method=='linear' else tri.CubicTriInterpolator(t,z,kind='geom')
            for k in (5e-17,1e-16,5e-16,1e-15):
                for criterion in (.1,1.,5.):
                    results.append(dict(dataset=label,samples=len(rr),method=method,k_m2=k,criterion_pct=criterion,intersections_m=intersections(ip,k,criterion)))
    output=dict(scope='Sensitivity of estimated intersections to sample exclusion only; not numerical tolerance convergence, corrected results or uncertainty bounds',input_sha256={'case_summary.csv':hashlib.sha256(source.read_bytes()).hexdigest(),'controls.json':hashlib.sha256(control.read_bytes()).hexdigest()},libraries=dict(python=sys.version.split()[0],numpy=np.__version__,matplotlib=matplotlib.__version__,scipy=scipy.__version__),omitted_cases=sorted(omitted),floor_pct=1e-10,reporting_domain=dict(k_m2=[1e-19,1e-15],L_m=[1.57,157]),results=results)
    path=ROOT/'results/interpolation_audit/continuation_exclusion.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(output,indent=2)+'\n')
    for r in results:
        if r['criterion_pct']==1:print(r)

if __name__=='__main__':main()
