"""Reproduce Pandora's bounded static app-use closure from retained native facts.

No assembly-text parsing, runtime capture or source generation. The graph is a
normal-return overapproximation with explicitly reviewed original data targets;
it is not a gameplay reachability or arbitrary callback-target proof.
"""
import argparse
from collections import Counter, defaultdict, deque
from hashlib import sha256
import json
from pathlib import Path

from amiga_reversing.disasm.app_access_audit import AuditIncomplete, decode_retained_instruction, explicit_register_writes
from amiga_reversing.tools.pandora_app_access_audit import ROOT, DIRECTORY, load_evidence


def digest(value):
    return sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def reachable(instructions, edges, roots):
    by = defaultdict(list)
    for edge in edges:
        by[edge['source_offset']].append(edge)
    seen, pending = set(), deque(roots)
    while pending:
        pc = pending.popleft()
        if pc in seen or pc not in instructions:
            continue
        seen.add(pc)
        row = instructions[pc]
        if by[pc]:
            pending.extend(e['target_offset'] for e in by[pc] if e['status'] == 'resolved' and e['kind'] != 'return')
        elif row['flow'] == 'sequential':
            pending.append(pc + row['size'])
    return seen


def reviewed_edges(metadata, binary, review, labels):
    extra = []
    for field, caller in [('interaction_callback', 0x83fe), ('interaction_completion_callback', 0x7a00),
                          ('interaction_completion_callback', 0x93f4)]:
        fields = [x for x in metadata['seeded_entities'] if x.get('struct_name') == 'world_object_shared_prefix' and x.get('field_name') == field]
        if len(fields) != 35:
            raise AuditIncomplete('original object-field population changed')
        for item in fields:
            value = int.from_bytes(binary[item['addr']:item['addr']+4], 'big')
            if value:
                extra.append(dict(source_offset=caller, target_offset=value-0x10000, kind='call', status='resolved',
                                  data_source=item['addr'], evidence=item['citation'], scope='original initialized object field; not immutable'))
    for item in review['stored_script_audit']['absolute_calls']:
        extra.append(dict(source_offset=0x11de, target_offset=item['target_source'], kind='call', status='resolved',
                          data_source=item['source'], evidence=item['citation'], scope='reviewed original stored absolute command'))
    for index in range(11):
        source = 0x4dce8 + 2*index
        value = int.from_bytes(binary[source:source+2], 'big', signed=True)
        extra.append(dict(source_offset=0x4dc2a, target_offset=0x4d7de+value, kind='jump', status='resolved',
                          data_source=source, evidence='pandora-indirect-closeout.json', scope='eleven original control entries; wider runtime domain unchecked'))
    # Native canonical labels plus manually reviewed LEA/store pairs. These two
    # stores are missed by the native callback candidate set, not new targets.
    names = {row['symbol']: row['addr'] for row in labels}
    for name, origin, store in [('handle_copper_interrupt_palette_effect',0xe0a,0xe0e),
                                ('apply_ticker_highlight_colors_and_arm_frame_end',0xa98,0xa9c)]:
        extra.append(dict(source_offset=0x902, target_offset=names[name], kind='call', status='resolved',
                          data_source=store, value_origin=origin, evidence=f's0:{store:08X}:instruction',
                          scope='reviewed original explicit Copper callback pointer store'))
    return extra


def build_report(rows, navigation, identity, edges, metadata, binary, review):
    decoded = {}
    for row in rows:
        data = bytes.fromhex(row['bytes']); pc = row['source_offset']
        if binary[pc:pc+len(data)] != data or pc in decoded:
            raise AuditIncomplete('retained instruction bytes or identity differ')
        fact = decode_retained_instruction(data, project_root=ROOT)
        if fact['size'] != row['size']:
            raise AuditIncomplete('native instruction boundary differs')
        decoded[pc] = dict(source_offset=pc, **fact, register_writes=explicit_register_writes(fact))
    writes = [d for d in decoded.values() if 'A6' in d['register_writes']]
    restores = {0x90a:0x8e4,0x922:0x8e4,0x93a:0x8e4,0x948:0x8e4,0x9d6:0x9cc,0xfe8:0xfde,
                0x1034:0x102a,0x97c8:0x97be,0x4d340:0x4d336,0x4d360:0x4d354,0x4d378:0x4d36e,
                0x552f8:0x552e6,0x55344:0x55332,0x5535e:0x55352}
    if {d['source_offset'] for d in writes} != set(restores) | {0x48c,0x8e8,0x4d978,0x4d98e}:
        raise AuditIncomplete('reviewed A6 modifier population changed')
    audio_calls = [e for e in edges if e['kind']=='call' and e['target_offset']==0x4d8fc]
    if {e['source_offset'] for e in audio_calls} != {0x9d0,0xfe2}:
        raise AuditIncomplete('audio clobber caller population changed')
    extra = reviewed_edges(metadata,binary,review,navigation['groups']['labels'])
    if any(e['target_offset'] not in decoded for e in extra):
        raise AuditIncomplete('reviewed original target is not accepted native code')
    native_reached = reachable(decoded,edges,[0x48c,0x8e8])
    reached = reachable(decoded,edges+extra,[0x48c,0x8e8])
    sites = []
    for row in rows:
        for op in row['operand_facts']:
            if op['memory'] and op['base_register']=='A6':
                hardware = any(e['operand_index']==op['operand_index'] and e['shape']=='hardware_register_family' for e in row['platform_evidence'])
                native = any(e['operand_index']==op['operand_index'] for e in row['app_slot_refs'])
                sites.append(dict(source_offset=row['source_offset'],operand_index=op['operand_index'],displacement=op['displacement'],
                                  indexed=op['indexed'],width_bytes=op['width_bytes'],hardware=hardware,native_app_attribution=native,
                                  original_entry_link=row['source_offset'] in reached))
    app = [s for s in sites if not s['hardware']]; conditional = [s for s in app if not s['native_app_attribution']]
    groups = []
    for root,meaning in [(0x248a,'Background restoration chain'),(0x2656,'Atomic Copper callback setter'),
                         (0x6dca,'Standalone tilemap offset helper'),(0x4d34c,'Standalone proximity-audio starter'),
                         (0x4d4f2,'Sequence214 feedback loop')]:
        local = reachable(decoded,edges+extra,[root])
        members = [s for s in app if not s['original_entry_link'] and s['source_offset'] in local]
        groups.append(dict(entry=root,meaning=meaning,sites=members,remaining='No external accepted/native or reviewed original-data entry established. Need an original caller, computed/stack target producer, or retained execution evidence; internal looping is not an external entry. No dead-code claim.'))
    cursor = defaultdict(list)
    for row in decoded.values():
        for op in row['operand_facts']:
            if op['base_register']=='A6' and op['access']=='address':
                cursor[op['displacement']].append(dict(source_offset=row['source_offset'],registers=[d['direct_register'] for d in row['operand_facts'] if d['direct_register'] and d['access'] in {'register_write','memory_write'}]))
    slot_checks = []
    for offset in [0x190,0x2d4,0x368]:
        physical = 0x39fc + offset
        scalar = [s for s in app if not s['indexed'] and s['displacement'] < offset+4 and s['displacement']+s['width_bytes'] > offset]
        constants = [dict(source_offset=d['source_offset'],operand_index=op['operand_index'],kind=kind,value=op[key])
                     for d in decoded.values() for op in d['operand_facts']
                     for key,kind in [('absolute_address','absolute_EA'),('immediate_value','immediate_scalar_candidate')]
                     if op[key] is not None and physical <= op[key] < physical+4]
        pointer_seeds = []
        for seed in metadata['seeded_entities']:
            if seed.get('value_kind') not in {'target_pointer','struct_pointer','string_pointer','raw_pointer'}:
                continue
            pos=seed.get('addr'); end=seed.get('end')
            if isinstance(pos,int) and end==pos+4:
                value=int.from_bytes(binary[pos:end],'big')
                if physical<=value<physical+4:
                    pointer_seeds.append(dict(source_offset=pos,value=value,citation=seed.get('citation')))
        slot_checks.append(dict(app_offset=offset,physical_address=physical,scalar_A6_overlaps=scalar,
                                static_constant_matches=constants,canonical_seeded_pointer_matches=pointer_seeds,
                                dead_storage_proved=False,limits='Exact constants and canonical initialized seeds only; computed/split pointers, dynamic state and opaque data are not excluded.'))
    cursor_contracts = [
        dict(offset=0x196,meaning='Four carried ID BYTEs',consumers=[0x2ac6,0x2acc,0x86e2],
             bound='Four-slot scans/copies; selected transfer uses D0.w=(cursorY-139)>>3 without an independent four-slot check.',
             aliases='Index318 reads/writes+2D4; index466 reads/writes+368. These require out-of-contract rows2683/3867.'),
        dict(offset=0x19a,meaning='Four pocket ID BYTEs',consumers=[0x2b3c,0x2b42,0x86f4],
             bound='Four-slot scans/copies; selected transfer shares the unchecked cursor-row index.',
             aliases='Index314 reads/writes+2D4; index462 reads/writes+368; rows2651/3835.'),
        dict(offset=0x232,meaning='Sixteen queued LONG message pointers',consumers=[0x2be6,0x2bec,0x2c12,0x9a0e,0x9a14,0x9a36],
             bound='Original tail initialization and four-byte updates; upper check before enqueue. Sentinel/pop reads reach+276, four bytes beyond nominal queue.',
             aliases='Inline queue interval does not reach the three questioned slots under valid tail protocol. Loaded message pointers are a separate mutable text domain.'),
        dict(offset=0x272,meaning='Queue end/sentinel address',consumers=[0x2be2,0x2c16,0x9a0a,0x9a3a],
             bound='Address-only end comparisons, not an unaccessed allocated field.',aliases='Same queue/sentinel qualification as+232.'),
        dict(offset=0x2ba,meaning='Four displayed inventory IDs',consumers=[0x284c,0x2856,0x2860,0x286a,0x2a80],
             bound='Four explicit name-list reads. Selected row store uses unchecked D0.w; valid rows139/147/155/163 select0..3.',
             aliases='Index26 writes+2D4; index174 writes+368, corresponding to invalid rows347/1531.'),
        dict(offset=0x2da,meaning='64-byte deposited ID prefix',consumers=[0x89da,0x89de,0x9fc4],
             bound='Reset clears16LONGs; deposit scans until zero without a64-byte end test.',
             aliases='A nonzero142-byte prefix reaches+368; no original lifetime deposit/zero-frontier bound is established.'),
        dict(offset=0x32c,meaning='Three submitted-name LONG pointers',consumers=[0x9d42,0x9e5a],
             bound='Initialized admission progresses count0..3; indexed store and display loop do not independently bound corrupted count.',
             aliases='Count15 stores at+368; display count>=16 reads it. This is not proof of a legitimate callback installer.')]
    return dict(schema='pandora-app-usage-closure-v1',identity=identity,
                input_graph_sha256=digest(edges),input_metadata_sha256=digest(metadata),
                decoder_backend_sha256=sha256((ROOT/'src/build/libamiga_backend.so').read_bytes()).hexdigest(),
                auditor_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                counts=dict(instructions=len(decoded),native_edges=len(edges),reviewed_original_data_edges=len(extra),A6_writes=len(writes),
                            app_candidate_sites=len(app),original_entry_linked=sum(s['original_entry_link'] for s in app),
                            app_entry_not_established=sum(not s['original_entry_link'] for s in app),omitted_A6_sites=len(conditional),
                            omitted_native_graph_linked=sum(s['source_offset'] in native_reached for s in conditional),
                            omitted_original_entry_linked=sum(s['original_entry_link'] for s in conditional),
                            omitted_entry_not_established=sum(not s['original_entry_link'] for s in conditional),
                            hardware_sites=sum(s['hardware'] for s in sites),cursor_origins=sum(map(len,cursor.values())),cursor_families=len(cursor)),
                A6_writes=writes,restore_save_pairs=[dict(restore=p,save=q) for p,q in restores.items()],
                audio_clobber_callers=audio_calls,reviewed_data_edges=extra,app_sites=app,unestablished_entry_groups=groups,
                cursor_origins={str(k):v for k,v in cursor.items()},reviewed_cursor_contracts=cursor_contracts,named_slot_alias_checks=slot_checks,
                limits=['Original-entry links are CFG possibilities under normal-return/valid-stack and original stored-target contracts, not observed gameplay.',
                        'All18 accepted-code A6 modifiers are checked; unknown/external entry and mutable callback/record replacement are not closed.',
                        'The178 prior omissions are base-attribution omissions, not178 missing semantic field meanings.',
                        'Unbounded row/deposit/name-index aliases prevent unconditional unread/write-only/dead storage claims.',
                        'The662 generic unresolved register aliases are not all app accesses and are not all excluded; pointer exclusivity is not proved.'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence-dir',type=Path,default=ROOT/'.runtime-state/pandora-app-access-audit')
    p.add_argument('--graph-dir',type=Path,default=ROOT/'.runtime-state/pandora-app-usage-closure')
    p.add_argument('--metadata',type=Path,default=ROOT/'.runtime-state/pandora-original-layout-closeout/metadata.json')
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    rows,nav,identity=load_evidence(args.evidence_dir)
    binary=(DIRECTORY/'binary.bin').read_bytes()
    if sha256(binary).hexdigest()!=identity['files'][str((DIRECTORY/'binary.bin').relative_to(ROOT))]:raise AuditIncomplete('original binary identity differs')
    graph_identity=json.loads((args.graph_dir/'graph-identity.json').read_text())
    if graph_identity['revision']!=identity['revision']:raise AuditIncomplete('graph and access snapshots differ')
    result=build_report(rows,nav,identity,json.loads((args.graph_dir/'edges.json').read_text()),json.loads(args.metadata.read_text()),binary,
                        json.loads((ROOT/'docs/validation/pandora-indirect-closeout.json').read_text()))
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['counts'],indent=2))


if __name__=='__main__':main()
