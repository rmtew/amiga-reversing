"""Recover STX payloads from a reviewed, source-bound native execution recipe."""
import argparse
import json
from pathlib import Path
from amiga_reversing.disasm.stx_recovery import read_stx, recover


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--member')
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists() and (not args.output_dir.is_dir() or any(args.output_dir.iterdir())):
        parser.error('output directory must be new or empty')
    data,origin=read_stx(args.image,args.member)
    report,outputs=recover(data,json.loads(args.plan.read_text()))
    report['origin']=origin
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for name,value in outputs.items(): (args.output_dir/name).write_bytes(value)
    (args.output_dir/'recovery.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(output_dir=str(args.output_dir),artifacts=report['captures'],runs=report['runs']),indent=2))


if __name__=='__main__': main()
