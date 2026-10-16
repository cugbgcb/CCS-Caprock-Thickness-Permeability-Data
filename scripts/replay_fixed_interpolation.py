"""Replay explicit log-space triangles without automatic Delaunay selection.

Numerical parameter-space diagnostics only; no simulation or uncertainty bound.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.tri as mt


def intersections(ip, permeability, criterion):
    x = math.log10(permeability)
    y = np.linspace(math.log10(1.57), math.log10(157), 1001)
    values = ip(np.full_like(y,x),y)-math.log10(criterion)
    roots = []
    for i in range(len(y)-1):
        if np.ma.is_masked(values[i]) or np.ma.is_masked(values[i+1]):
            continue
        if values[i] == 0:
            roots.append(10**float(y[i])); continue
        if values[i]*values[i+1] >= 0:
            continue
        lo,hi,flo = float(y[i]),float(y[i+1]),float(values[i])
        for _ in range(70):
            mid = (lo+hi)/2
            value = float(ip(x,mid))-math.log10(criterion)
            if value == 0 or mid == lo or mid == hi:
                lo = hi = mid; break
            if (value > 0) == (flo > 0):
                lo,flo = mid,value
            else:
                hi = mid
        roots.append(10**((lo+hi)/2))
    return roots


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--case-summary',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--reverse-order',action='store_true',help='Test order invariance with mapped explicit triangles')
    ap.add_argument('--floor-pct',type=float,choices=(1e-10,1e-6,1e-3),default=1e-10)
    a = ap.parse_args()
    assert not a.output.exists()
    sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    reference = json.loads(a.reference.read_text())
    assert reference['schema'] == 'fixed-log-triangulation-v1'
    assert sha(a.case_summary) == reference['source_case_summary_sha256']
    cases = {r['case']:r for r in csv.DictReader(a.case_summary.open())}
    rows,fields,mesh_counts = [],{},{}
    xx,yy = np.meshgrid(np.linspace(-19,-15,501),
                       np.linspace(math.log10(1.57),math.log10(157),501))
    for label,record in reference['datasets'].items():
        points = record['points']; count = len(points)
        assert count == record['samples'] and len({p['case'] for p in points}) == count
        x = np.array([float.fromhex(p['log_k_hex']) for p in points])
        y = np.array([float.fromhex(p['log_L_hex']) for p in points])
        default_z = np.array([float.fromhex(p['log_response_hex']) for p in points])
        values = []
        for i,p in enumerate(points):
            source = cases[p['case']]
            assert source['stage'] != 'S0'
            assert abs(x[i]-math.log10(float(source['permeability_m2']))) < 1e-12
            assert abs(y[i]-math.log10(float(source['thickness_m']))) < 1e-12
            native = float(source['R_mig_pct']); assert math.isfinite(native) and 0 <= native <= 100
            assert abs(default_z[i]-math.log10(max(native,reference['floor_pct']))) < 1e-12
            values.append(math.log10(max(native,a.floor_pct)))
        z = default_z if a.floor_pct == reference['floor_pct'] else np.array(values)
        triangles = np.array(record['triangles'],dtype=int)
        assert triangles.ndim == 2 and triangles.shape[1] == 3
        assert triangles.min() >= 0 and triangles.max() < count
        assert all(len(set(t)) == 3 for t in triangles.tolist())
        order = np.arange(count)[::-1] if a.reverse_order else np.arange(count)
        inverse = np.empty(count,dtype=int); inverse[order] = np.arange(count)
        triangulation = mt.Triangulation(x[order],y[order],triangles=inverse[triangles])
        assert not triangulation.is_delaunay, 'Automatic triangulation must not execute'
        mesh_counts[label] = dict(samples=count,triangles=len(triangles))
        for method in ('linear','cubic'):
            ip = mt.LinearTriInterpolator(triangulation,z[order]) if method == 'linear' else mt.CubicTriInterpolator(triangulation,z[order],kind='geom')
            for permeability in (5e-17,1e-16,5e-16,1e-15):
                for criterion in (.1,1.,5.):
                    rows.append(dict(dataset=label,samples=count,method=method,k_m2=permeability,
                                     criterion_pct=criterion,intersections_m=intersections(ip,permeability,criterion)))
            if method == 'linear':
                fields[label] = ip(xx,yy)
    comparisons = {}
    for label in ('omit_2_altered_restarts','omit_3_continuations'):
        full,reduced = fields['all_50'],fields[label]
        valid = ~(np.ma.getmaskarray(full)|np.ma.getmaskarray(reduced))
        indices = np.argwhere(valid)
        differences = np.abs(full.filled(np.nan)-reduced.filled(np.nan))
        index = indices[int(np.argmax(differences[valid]))]
        i,j = map(int,index)
        comparisons[label] = dict(masked_grid_points=int(np.ma.count_masked(reduced)),
            masked_percent=100*int(np.ma.count_masked(reduced))/reduced.size,
            common_grid_points=int(valid.sum()),maximum_absolute_log10_difference=float(differences[i,j]),
            location=dict(k_m2=10**float(xx[i,j]),L_m=10**float(yy[i,j])),
            full_response_pct=10**float(full[i,j]),reduced_response_pct=10**float(reduced[i,j]),
            support_mask_sha256=hashlib.sha256(np.ma.getmaskarray(reduced).tobytes()).hexdigest())
    result = dict(reference_sha256=sha(a.reference),case_summary_sha256=sha(a.case_summary),
        libraries=dict(python=sys.version.split()[0],numpy=np.__version__,matplotlib=matplotlib.__version__),
        point_order='reversed_with_mapped_fixed_triangles' if a.reverse_order else 'stored',
        floor_pct=a.floor_pct,automatic_triangulation_used=False,mesh_counts=mesh_counts,
        results=rows,diagnostic_grid_shape=[501,501],linear_surface_comparisons=comparisons,
        scientific_results_admitted=False,
        scope='Explicit archived binary log-coordinates/response and triangle indices, with optional new logarithmic floor. Root sets and common-support linear diagnostics only; no model rerun, continuum threshold, confidence interval or numerical-flow convergence.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(root_sets=len(rows),floor_pct=a.floor_pct,
                         point_order=result['point_order'],linear_surface_comparisons=comparisons),indent=2))


if __name__ == '__main__':
    main()
