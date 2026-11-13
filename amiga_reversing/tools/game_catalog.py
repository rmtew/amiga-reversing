"""Inspect linked releases, bind private media, or materialize verified artifacts."""
import argparse
import json
from pathlib import Path
from amiga_reversing.disasm.game_catalog import bind_source,load_family,materialize,verify_correspondence
from amiga_reversing.disasm.project_paths import PROJECT_ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,default=PROJECT_ROOT)
    parser.add_argument('--family',required=True)
    parser.add_argument('operation',choices=['inspect','bind','materialize','verify-links'])
    parser.add_argument('--artifact')
    parser.add_argument('--path',type=Path)
    parser.add_argument('--member')
    args=parser.parse_args()
    root=args.project_root.resolve()
    family=load_family(root,args.family)
    if args.operation=='inspect':
        result=dict(game=family['name'],releases=family['releases'],targets=family['targets'],correspondences=family['correspondences'])
    elif args.operation=='bind':
        if not args.artifact or args.path is None: parser.error('bind requires --artifact and --path')
        result=dict(bound=bind_source(root,args.family,args.artifact,args.path,args.member),private=True)
    elif args.operation=='materialize':
        if not args.artifact: parser.error('materialize requires --artifact')
        result=dict(path=str(materialize(root,args.family,args.artifact)))
    else:
        result=dict(verified=[verify_correspondence(root,args.family,link['id'])['id'] for link in family['correspondences']])
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
