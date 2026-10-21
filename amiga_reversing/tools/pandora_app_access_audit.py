"""Inventory Pandora app-relative operands through the resident native service.

Raw instruction DTOs stay in local evidence storage. The report contains facts,
coordinates and declarations, never original instruction bytes or media.
"""
import argparse
from hashlib import sha256
import json
import sys
from pathlib import Path
from urllib.parse import quote

from amiga_reversing.disasm.app_access_audit import AuditIncomplete, build_app_access_audit, collect_instruction_pages
from amiga_reversing.disasm.restoration_client import RestorationClient

TARGET = 'amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load_evidence(directory):
    identity = json.loads((directory / 'identity.json').read_text())
    rows = json.loads((directory / 'instructions.json').read_text())
    data = json.loads((directory / 'navigation.json').read_text())
    for value, key in ((rows, 'native_instruction_evidence_sha256'), (data, 'native_navigation_sha256')):
        if sha256(json.dumps(value, sort_keys=True).encode()).hexdigest() != identity[key]:
            raise AuditIncomplete('saved native evidence differs from its captured identity')
    return rows, data, identity


def write_report(report, output):
    """Keep the summary readable and every operand site individually diffable."""
    output.parent.mkdir(parents=True, exist_ok=True)
    detail = output.with_name(output.stem + '-sites.jsonl')
    detail.write_text(''.join(json.dumps(site, sort_keys=True, separators=(',', ':')) + '\n'
                              for site in report['sites']))
    summary = {key: value for key, value in report.items() if key != 'sites'}
    summary['site_details'] = dict(file=detail.name, sha256=digest(detail), records=len(report['sites']))
    summary['auditor_profile'] = {str(p.relative_to(ROOT)): digest(p) for p in (
        Path(__file__), ROOT / 'amiga_reversing/disasm/app_access_audit.py')}
    output.write_text(json.dumps(summary, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8123')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--evidence-dir', type=Path, default=ROOT / '.runtime-state/pandora-app-access-audit')
    parser.add_argument('--from-evidence', action='store_true', help='Project the identity-checked saved snapshot; do not contact the server')
    args = parser.parse_args()
    if args.from_evidence:
        rows, data, identity = load_evidence(args.evidence_dir)
        report = build_app_access_audit(rows, data['app_slot_analysis']['layout_fields'], app_base=0x39fc, identity=identity)
        report['native_navigation_counts'] = {k: v for k, v in data['app_slot_analysis'].items() if k.endswith('_count')}
        report['snapshot_only'] = True
        write_report(report, args.output)
        print(json.dumps(report['counts'], indent=2))
        return
    client = RestorationClient(args.base_url, timeout=900)
    state = client.call(TARGET, 'state')
    if not state.get('ready'):
        raise AuditIncomplete('native analysis is not ready; existing job retained, rerun after it finishes')
    revision = state['revision']
    # These are local source identities; service revision binds the consumed artifact.
    subjects = {str(p.relative_to(ROOT)): digest(p) for p in (
        DIRECTORY / 'binary.bin', DIRECTORY / 'pandora_3e1ee0f1_bk_00_000000e8.s',
        DIRECTORY / 'manual_actions.jsonl', ROOT / 'src/build/libamiga_backend.so')}
    rows = collect_instruction_pages(client.call, TARGET, revision,
                                     progress=lambda count, total: print(f'native instructions {count}/{total}', file=sys.stderr, flush=True))
    navigation = client._request('/api/projects/' + quote(TARGET, safe='') + '/listing/navigation')
    end = client.call(TARGET, 'state')
    if end['revision'] != revision or any(digest(ROOT / p) != d for p, d in subjects.items()):
        raise AuditIncomplete('subject changed during inventory')
    data = navigation.get('data', navigation)
    analysis = data['app_slot_analysis']
    identity = dict(target=TARGET, revision=revision, subject_revision=state['subject_revision'], files=subjects,
                    native_instruction_evidence_sha256=sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
                    native_navigation_sha256=sha256(json.dumps(data, sort_keys=True).encode()).hexdigest())
    report = build_app_access_audit(rows, analysis['layout_fields'], app_base=0x39fc, identity=identity)
    report['native_navigation_counts'] = {k: v for k, v in analysis.items() if k.endswith('_count')}
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    (args.evidence_dir / 'instructions.json').write_text(json.dumps(rows, indent=2) + '\n')
    (args.evidence_dir / 'navigation.json').write_text(json.dumps(data, indent=2) + '\n')
    (args.evidence_dir / 'identity.json').write_text(json.dumps(identity, indent=2) + '\n')
    report['snapshot_only'] = False
    write_report(report, args.output)
    print(json.dumps(report['counts'], indent=2))


if __name__ == '__main__':
    main()
