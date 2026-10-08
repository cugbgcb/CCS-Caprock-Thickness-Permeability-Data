"""Restore exact case directories from the deduplicated archive. No solver required."""
from pathlib import Path
import argparse,json,hashlib,shutil
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);p.add_argument('--case',help='Exact case path; omitted restores all');p.add_argument('--inputs-only',action='store_true');args=p.parse_args()
files=json.loads((root/'models/manifest.json').read_text())['files'];files=[f for f in files if (not args.case or f['case']==args.case) and (not args.inputs_only or f['kind']=='input')]
if not files:raise SystemExit('No matching case')
for f in files:
 src=root/f['object'];dst=args.destination/f['case']/f['filename']
 if hashlib.sha256(src.read_bytes()).hexdigest()!=f['sha256']:raise ValueError(f'Corrupt object {src}')
 if dst.exists():
  if hashlib.sha256(dst.read_bytes()).hexdigest()!=f['sha256']:raise FileExistsError(f'Refusing to replace changed file {dst}')
 else:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
print(f'Restored/verified {len(files)} files in {args.destination}')
