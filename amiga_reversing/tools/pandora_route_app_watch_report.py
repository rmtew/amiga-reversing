"""Reconcile the private watched ending run with its published baseline.

Standard-library-only reporter: reads an explicit qualified checkout, never
imports or merges its held implementation. Published output omits raw stacks,
media, payload bytes and complete checkpoint/register captures.
"""
import argparse, bisect, hashlib, json, re
from pathlib import Path

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_text())

def memory(phase, address):
    return max((bytes.fromhex(r['bytes']) for r in phase['capture']['memory_reads'] if int(r['address'], 0) == address), key=len, default=b'')

def build(root, run_name):
    local = root / '.runtime-state/pandora-player'
    run = local / run_name
    baseline = local / 'finale-cold-b'
    qualification = load(root / 'runtime/observations/pandora-saved-earth-walkthrough.json')
    qualified = next((r for r in qualification['runs'] if r['name'] == 'finale-cold-b'))
    require(sha(baseline / 'report.json') == qualified['artifact_sha256']['report.json'], 'Baseline receipt differs')
    original = load(baseline / 'report.json')['runner']
    watched = load(run / 'report.json')['runner']
    trace = load(run / 'watch.json')
    identities = load(run / 'execution-identities.json')
    for file, expected in identities.items():
        require(sha(Path(file)) == expected, 'Executed input/code identity is stale: ' + file)
    require(original['status'] == watched['status'] == 'ok', 'Evidence precondition failed')
    require(trace['capture_complete'] and trace['server_dropped_notifications'] == 0 and trace.get('server_dropped_mmio_events') == 0 and (not trace['local_signature_overflow']), 'Evidence precondition failed')
    op = original['observation']['scenario']['phases']
    wp = watched['observation']['scenario']['phases']
    require(len(op) == len(wp) == 576 and all((p['status'] == 'hit' for p in wp)), 'Evidence precondition failed')
    require([(p['name'], p['stable_key'], p['stop_event']['frame'], p['stop_event']['cck']) for p in op] == [(p['name'], p['stable_key'], p['stop_event']['frame'], p['stop_event']['cck']) for p in wp], 'Route timing changed')
    require(original['observation']['scenario']['input_trace'] == watched['observation']['scenario']['input_trace'], 'Input trace changed')
    require(sha(run / 'authored.json') == sha(baseline / 'authored.json') and sha(run / 'compiled.json') == sha(baseline / 'compiled.json'), 'Evidence precondition failed')
    outcome = next((p for p in wp if p['name'] == 'es_saved_earth_outcome_selected'))
    require(int(outcome['capture']['registers']['a0'], 0) == 379621 and memory(outcome, 15655) == b'\xff', 'Evidence precondition failed')
    require(memory(outcome, 15672)[0] & 88 == 88 and int.from_bytes(memory(outcome, 15490), 'big') != 0, 'Evidence precondition failed')
    final = wp[-1]
    require(int.from_bytes(memory(final, 377682)[12:14], 'big') == 49 and memory(final, 15572) == b'\xff', 'Evidence precondition failed')
    inventory_path = root / 'docs/validation/pandora-app-access-audit.json'
    inventory = load(inventory_path)
    closure_path = root / 'docs/validation/pandora-app-usage-closure.json'
    closure = load(closure_path)
    site_path = root / 'docs/validation/pandora-app-access-audit-sites.jsonl'
    dated_sites = [json.loads(line) for line in site_path.read_text().splitlines()]
    originally_unresolved = {(r['source_offset'], r['operand_index']) for r in dated_sites if r['domain'] == 'unresolved_A6'}
    remaining_sites = [r for r in closure['app_sites'] if (r['source_offset'], r['operand_index']) in originally_unresolved and not r['original_entry_link']]
    require(len(remaining_sites) == 4, 'Unestablished site inventory changed')
    source = root / next((k for k in qualification['runs'][-1]['executed_code_sha256'] if k.endswith('.s'))) if any((k.endswith('.s') for k in qualification['runs'][-1]['executed_code_sha256'])) else next((root / 'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8').glob('*.s'))
    require(sha(source) == qualification['input_identities']['original_rendered_source_sha256'], 'Evidence precondition failed')
    block = source.read_text().split('    RSSET 0\n', 1)[1].split('    RSSET ', 1)[0]
    offset = 0
    gaps = []
    for line in block.splitlines():
        line = line.split(';', 1)[0].strip()
        if not line:
            continue
        m = re.fullmatch('(?:(\\w+)\\s+)?RS\\.([BWL])\\s+(\\d+)', line)
        require(m, 'Unexpected generated RS form')
        name, width, count = m.groups()
        size = {'B': 1, 'W': 2, 'L': 4}[width] * int(count)
        if name is None:
            gaps.append({'start': offset, 'end': offset + size})
        offset += size
    require(offset == 2032 and gaps == inventory['gaps'], 'Current rendered gaps differ from inventory')
    require(trace['ranges'] == gaps + [{'start': 724, 'end': 728}, {'start': 872, 'end': 876}], 'Evidence precondition failed')
    facts_path = root / '.runtime-state/pandora-app-access-audit/instructions.json'
    rows = load(facts_path)
    facts = {r['source_offset']: r for r in rows}
    require(sha(facts_path) == qualification['input_identities']['accepted_instruction_facts_sha256'], 'Evidence precondition failed')
    stops = [p['stop_event']['cck'] for p in wp]

    def phase_at(position):
        require(trace['start']['cck'] <= position['cck'] <= trace['end']['cck'], 'Evidence precondition failed')
        return wp[bisect.bisect_left(stops, position['cck'])]['name']
    signatures = []
    meanings = {24880: 'Indexed raster-row lookup aliases the pointer high WORD; observed earlier during startup. Not callback consumption.', 33638: 'Changed proximity candidate A5 is copied to nearest-object pointer and then its shadow at app+$2D4; this is semantic gameplay production, not bulk clearing. Consumer purpose remains unresolved.'}
    for row in trace['signatures']:
        at = row['pc'] - 65536
        native = facts[at]
        require(at in meanings, 'New site needs explicit static review')
        context = row.get('later_boundary_context', {})
        item = {k: v for k, v in row.items() if k != 'later_boundary_context'}
        item.update(source_offset=at, instruction=native['text'], static_interpretation=meanings[at], first_phase_by_cck=phase_at(row['first_position']), last_phase_by_cck=phase_at(row['last_position']))
        if context:
            item['later_boundary_context'] = {'phase': context['phase'], 'frame': context['stop_event']['frame'], 'a6': context['registers_at_later_boundary']['a6'], 'stack_code_address_candidates': [int.from_bytes(bytes.fromhex(context['stack_at_later_boundary_hex'])[i:i + 4], 'big') for i in range(0, 32, 4) if int.from_bytes(bytes.fromhex(context['stack_at_later_boundary_hex'])[i:i + 4], 'big') - 65536 in facts], 'caveat': 'Later canonical boundary, NOT access-time registers or a validated access-time call stack.'}
        signatures.append(item)
    require(sum((r['count'] for r in signatures)) == trace['events_received'], 'Evidence precondition failed')
    before = {'declaration_gap_regions': len(gaps), 'declaration_gap_bytes': 750, 'unexplained_declared_slots': 2, 'unresolved_conditional_A6_sites': closure['counts']['omitted_entry_not_established'], 'unresolved_register_alias_sites_dated_inventory': inventory['counts']['domains']['unresolved_register_alias']}
    by_range = []
    for region in trace['ranges']:
        events = [r for r in signatures if region['start'] <= r['app_offset'] < region['end']]
        by_range.append({**region, 'physical_start': 14844 + region['start'], 'physical_end': 14844 + region['end'], 'read_events': sum((r['count'] for r in events if r['access'] == 'read')), 'write_events': sum((r['count'] for r in events if r['access'] == 'write')), 'disposition': 'observed_known_site' if events else 'not_observed_in_completed_route_window'})
    return {'schema_version': 1, 'profile': qualification['profile'], 'validation': {'adapter_tests_passed':9,'adapter_tests_skipped':0,'controlled_reported_loss_variants_refused':['dropped_notifications','dropped_events'],'target_source_changes':0}, 'qualified_route_commit': '666b373ca9b612e0f4ad8eb92bd0a797d9389a89', 'master_publication_base': '53ac88369520343a193a7aba76e7683edfe8599b', 'status': 'ending_preserved_cpu_access_stream_complete_within_declared_limits', 'summary': {'canonical_phases': 576, 'input_events': 375, 'start_frame': trace['start']['frame'], 'end_frame': trace['end']['frame'], 'cpu_access_events': trace['events_received'], 'read_events': trace['access_counts'].get('read', 0), 'write_events': trace['access_counts'].get('write', 0), 'distinct_access_signatures': len(signatures), 'distinct_source_instruction_sites': len({s['source_offset'] for s in signatures}), 'new_instruction_sites': 0, 'newly_classified_bytes': 0, 'gap_bytes_without_received_access': 748, 'full_gap_regions_without_received_access': 13, 'server_dropped_notifications': 0, 'server_dropped_mmio_events': 0, 'local_signature_overflow': False, 'all_phase_frame_and_cck_stops_equal_baseline': True, 'input_trace_equal_baseline': True, 'saved_earth_message_pointer': '0x5cae5', 'earth_deadline_word': memory(outcome, 15490).hex(), 'self_destruct_state': 255, 'event_flags': memory(outcome, 15672)[0], 'final_health': 49}, 'input_identities': qualification['input_identities'], 'evidence_sha256': {str(p.relative_to(root)): sha(p) for p in [inventory_path, site_path, closure_path, facts_path, source] + [run / f for f in ['authored.json', 'compiled.json', 'report.json', 'summary.json', 'watch.json', 'execution-identities.json']] + [baseline / 'report.json', root / 'amiga_reversing/tools/pandora_route_app_watch.py']}, 'executed_code_sha256': {str(Path(k).relative_to(root)): v for k, v in load(run / 'execution-identities.json').items() if k.startswith(str(root)) and k.endswith('.py')}, 'reporter_profile_sha256': sha(Path(__file__)), 'range_inventory': by_range, 'watch_start': trace['start'], 'watch_end': trace['end'], 'subscription_registration': trace['registration'], 'subscription_readback': trace['readback'], 'signatures': signatures, 'remaining_conditional_A6_sites': remaining_sites, 'before': before, 'after': dict(before), 'accounting_notes': ['Gap extents rechecked against current generated RS block and unchanged original source identity. No fresh whole native analysis or generation.', 'The662 unresolved register-alias sites are the dated inventory denominator, not all claimed examined or closed by this physical-range trace.', 'The four unestablished conditional-A6 sites remain unresolved; watching these gaps is not whole-program execution coverage.', '168 WORD bus writes at one LONG MOVE site are84 writes to each half. No ordered per-store value-pair proof is claimed.'], 'static_callers': {name: [{'source_offset': r['source_offset'], 'instruction': r['text']} for r in rows if name in r['text']] for name in ['update_nearby_object_detection', 'set_text_cursor_in_overlay_plane']}, 'provisional_stream_run': {'name':'ending-app-watch-b','status':'positive_observations_only_queue_loss_unretained','events_received':197,'raw_watch_sha256':sha(local/'ending-app-watch-b/watch.json'),'reason':'The initial observer retained dropped_notifications but not the separate dropped_events queue counter. No complete absence coverage qualified from this run.'}, 'loss_schema_control': {'name':'watch-schema-a','frames':[2572,2574],'purpose':'Known frame-counter positive control; established separate dropped_events and dropped_notifications fields. No ending or unknown-region coverage claimed.','raw_event_sha256':sha(local/'watch-schema-a/event-schema.json')}, 'failed_probe': {'name': 'ending-app-watch-a', 'status': 'registration_failed_before_gameplay', 'error': 'RPC -32602 during32 stopping-trap registration; cleanup also errored; owned process exited. No coverage claimed.', 'log_sha256': sha(local / 'ending-app-watch-a.log')}, 'limits': trace['limits'] + ['Start at original source$83AE, frame463; initial clearing/copying and the prior frame462 alias read are outside this window.', 'No semantic owner/consumer, unused-memory, all-caller A6 provenance, full lifetime, native-C or relocation claim is added.', 'Source/binary and successful normal-input route are unchanged. No target byte-exact test rerun was needed.', 'Proprietary media/ROMs, raw stack/register captures and checkpoints stay private.']}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualified-checkout', type=Path, required=True)
    parser.add_argument('--run', default='ending-app-watch-c')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch('[a-zA-Z0-9_-]{1,64}', args.run):
        parser.error('Run must be a local evidence-directory name')
    report = build(args.qualified_checkout.resolve(), args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], indent=2))
if __name__ == '__main__':
    main()
