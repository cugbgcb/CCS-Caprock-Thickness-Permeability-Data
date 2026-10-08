"""Audit archived mesh invariance and reference pore volumes for 51 paper cases."""
from pathlib import Path
import hashlib,json,math,csv
ROOT=Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'models/manifest.json').read_text())['files'];cases={}
for item in entries:
    if not item['case'].endswith('/continue'):
        cases.setdefault(item['case'],{})[item['filename']]=item
nominal={r['case']:float(r['thickness_m']) for r in csv.DictReader((ROOT/'results/historical/case_summary.csv').open())}
records=[]
widths=None
for case,files in sorted(cases.items()):
    if not all(name in files for name in ['MESH','INFILE']):continue
    data={}
    for name in ['MESH','INFILE']:
        entry=files[name];raw=(ROOT/entry['object']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==entry['sha256']
        data[name]=raw.decode().splitlines()
    rocks={line[:5]:float(line[20:30]) for line in data['INFILE'] if line[:5] in ['MAQUO','OVERB','EAUCL','MTSIM']}
    j=next(i for i,line in enumerate(data['MESH']) if line.startswith('CONNE'))
    elements=[l for l in data['MESH'][1:j] if len(l)>=80 and l[15:20] in rocks]
    assert len(elements)==26100
    geometric='\n'.join(l[:15]+l[20:] for l in elements)+'\n'+'\n'.join(data['MESH'][j:])
    bulk={rock:math.fsum(float(l[20:30]) for l in elements if l[15:20]==rock) for rock in rocks}
    layers=sorted({float(l[70:80]) for l in elements if l[15:20]=='EAUCL'})
    if widths is None:
        by_id={l[:5]:float(l[70:80]) for l in elements};widths={}
        for line in data['MESH'][j+1:]:
            if line[:5] not in by_id or line[5:10] not in by_id or int(line[25:30])!=3:continue
            for ident,field in ((line[:5],line[30:40]),(line[5:10],line[40:50])):
                z=by_id[ident];dz=2*float(field)
                if z in widths:assert math.isclose(widths[z],dz,abs_tol=1e-8)
                widths[z]=dz
    actual=math.fsum(widths[z] for z in layers)
    assert math.isclose(actual,nominal[case],rel_tol=0,abs_tol=1e-8),(case,actual,nominal[case])
    faces=[(z-widths[z]/2,z+widths[z]/2) for z in layers]
    assert all(math.isclose(a[1],b[0],abs_tol=1e-8) for a,b in zip(faces,faces[1:])),case
    base=min(a[0] for a in faces);top=max(a[1] for a in faces)
    assert math.isclose(base,-1684,abs_tol=1e-8),case
    records.append(dict(case=case,source_sha256={n:files[n]['sha256'] for n in data},geometry_without_rock_assignment_sha256=hashlib.sha256(geometric.encode()).hexdigest(),elements=len(elements),caprock_vertical_cells=len(layers),nominal_caprock_thickness_m=nominal[case],connection_defined_caprock_thickness_m=actual,caprock_base_z_m=base,caprock_top_z_m=top,porosity=rocks,bulk_volume_m3=bulk,reference_pore_volume_m3={r:v*rocks[r] for r,v in bulk.items()},total_reference_pore_volume_m3=math.fsum(v*rocks[r] for r,v in bulk.items())))
assert len(records)==51
assert len({r['geometry_without_rock_assignment_sha256'] for r in records})==1
assert all(r['porosity']==records[0]['porosity'] for r in records)
a=next(r for r in records if r['case']=='Stage01_Scn01-05_H1.57m/k1e-16');b=next(r for r in records if r['case']=='Stage01_Scn01-05_H157m/k1e-16')
reduction=a['total_reference_pore_volume_m3']-b['total_reference_pore_volume_m3']
out=dict(scope='Input reference pore volume (sum of element bulk volume times ROCKS porosity); excludes pressure-dependent pore-volume changes. 50 parameter cases plus S0; continuation folders excluded.',geometry_invariant=True,cases=records,thickness_endmember_comparison=dict(thin_case=a['case'],thick_case=b['case'],thin_reference_pore_volume_m3=a['total_reference_pore_volume_m3'],thick_reference_pore_volume_m3=b['total_reference_pore_volume_m3'],reduction_m3=reduction,reduction_percent_of_thin=100*reduction/a['total_reference_pore_volume_m3']))
(ROOT/'provenance/geometry_pore_volume_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out['thickness_endmember_comparison'],indent=2))
print('51 case meshes identical apart from rock assignments.')
