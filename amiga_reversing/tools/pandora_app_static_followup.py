"""Read-only targeted follow-up from retained Pandora native facts.

No fresh analysis, guest execution, source generation, target mutations or
instruction decoding. Native operand facts and existing reviewed CFG edges are
inputs; pointer coincidences are leads, not newly invented control-flow edges.
"""
import argparse,bisect,hashlib,json,re
from collections import defaultdict,deque
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def require(condition,message):
    if not condition:raise ValueError(message)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def build(root):
    local=root/'.runtime-state';directory=root/'targets/amiga_disk_pandora-1988-firebird/targets/amiga_raw_pandora_3e1ee0f1_bk_00_000000e8'
    paths={'instructions':local/'pandora-app-access-audit/instructions.json',
           'decoded':local/'pandora-app-usage-closure/decoded-registers.json',
           'edges':local/'pandora-app-usage-closure/edges.json',
                      'reached':local/'pandora-app-usage-closure/augmented-reachable.json',
           'metadata':local/'pandora-original-layout-closeout/metadata.json',
           'closure':root/'docs/validation/pandora-app-usage-closure.json', 'inventory':root/'docs/validation/pandora-app-access-audit.json',
           'indirect':root/'docs/validation/pandora-indirect-closeout.json',
           'binary':directory/'binary.bin','source':next(directory.glob('*.s')),
           'shape_header':root/'src/m68k_simulator.h','navigation':local/'pandora-app-access-audit/navigation.json'}
    rows=load(paths['instructions']);by={r['source_offset']:r for r in rows};decoded=load(paths['decoded']);D={r['source_offset']:r for r in decoded}
    closure=load(paths['closure']);metadata=load(paths['metadata']);binary=paths['binary'].read_bytes();edges=load(paths['edges']);extra=closure['reviewed_data_edges'];reached=set(load(paths['reached']))
    require(len(by)==len(D)==7059 and set(by)==set(D),'Retained populations differ')
    require(digest(edges)==closure['input_graph_sha256'] and digest(metadata)==closure['input_metadata_sha256'],'Reviewed graph/metadata identity differs')
    require(sha(paths['binary'])=='70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f','Original payload differs')
    for pc,row in by.items():
        require(binary[pc:pc+row['size']]==bytes.fromhex(row['bytes']) and D[pc]['size']==row['size'],'Instruction identity differs')
    def render(pc):return {'source_offset':pc,'instruction':by[pc]['text']}
    # Register-copy routes were not independently enumerated by the old cursor
    # origin list. Preserve the old valid-stack/normal-return qualification.
    direct=[];escapes=[]
    for row in decoded:
        reads=[o for o in row['operand_facts'] if o.get('direct_register')=='A6' and o['access'] not in ('register_write','memory_write')]
        if reads:
            direct.append(render(row['source_offset']))
            dest=row['operand_facts'][-1]
            if not(dest.get('base_register')=='A7' and dest['access']=='memory_write'):escapes.append(render(row['source_offset']))
    require({r['source_offset'] for r in direct}=={0x102A,0x97BE},'A6 direct-read population changed')
    register_list_saves=[row for row in decoded if any('A6' in o.get('register_list',[]) and o['access']=='register_list_read' for o in row['operand_facts'])]
    known_saves={p['save'] for p in closure['restore_save_pairs']}
    require({r['source_offset'] for r in register_list_saves}|{r['source_offset'] for r in direct}==known_saves,'Unreviewed A6 save/copy producer')
    require(all(any(o.get('base_register')=='A7' and o['access']=='memory_write' for o in r['operand_facts']) for r in register_list_saves),'A6 group copy escapes the stack')
    pairs=[]
    for pair in closure['restore_save_pairs']:
        save,restore=D[pair['save']],D[pair['restore']]
        s=next((o.get('register_list') for o in save['operand_facts'] if o.get('register_list')),None)
        r=next((o.get('register_list') for o in restore['operand_facts'] if o.get('register_list')),None)
        if s is not None or r is not None:require(s==r and 'A6' in s,'Register-list restoration differs')
        else:require(save['operand_facts'][0].get('direct_register')==restore['operand_facts'][-1].get('direct_register')=='A6','Direct stack restoration differs')
        pairs.append({**pair,'save_instruction':by[pair['save']]['text'],'restore_instruction':by[pair['restore']]['text'],'register_list_matches':True})
    graph=defaultdict(list)
    for edge in edges+extra:
        if edge['status']=='resolved' and edge['kind']!='return':graph[edge['source_offset']].append(edge['target_offset'])
    def walk(start):
        pending=deque([start]);seen=set()
        while pending:
            pc=pending.popleft()
            if pc in seen or pc not in by:continue
            seen.add(pc)
            if pc in graph:pending.extend(graph[pc])
            elif D[pc]['flow']=='sequential':pending.append(pc+by[pc]['size'])
        return seen
    require(walk(0x48C)|walk(0x8E8)==reached,'Retained reachability projection differs')
    # Read the named native enum from the pinned header, not an opcode mask.
    # Only LEA/PEA address expressions use this exact native PC-displacement
    # query; register-indexed destinations remain explicitly unresolved.
    shape=int(re.search(r'M68K_SIM_EA_SHAPE_PC_DISPLACEMENT\s*=\s*(\d+)',paths['shape_header'].read_text())[1])
    starts=sorted(by)
    def containing(p):
        i=bisect.bisect_right(starts,p)-1
        return starts[i] if i>=0 and p<starts[i]+by[starts[i]]['size'] else None
    groups=[]
    for entry in [0x248A,0x6DCA]:
        exclusive=walk(entry)-reached
        native_incoming=[e for e in edges+extra if e['status']=='resolved' and e['target_offset'] in exclusive and e['source_offset'] not in exclusive]
        producers=[];dynamic_pc_addresses=[]
        for row in decoded:
            pc=row['source_offset']
            if pc in exclusive:continue
            for op in row['operand_facts']:
                values=[(key,op.get(key)) for key in ('absolute_address','immediate_value')]
                if op.get('access')=='address' and op.get('ea_shape_id')==shape:
                    require(by[pc]['mnemonic'] in ('lea','pea'),'Unreviewed PC address producer form')
                    values.append(('native_PC_displacement_address',0x10000+pc+2+op['displacement']))
                elif op.get('access')=='address' and op.get('indexed'):dynamic_pc_addresses.append(render(pc))
                for kind,value in values:
                    if value is not None and value-0x10000 in exclusive:producers.append({**render(pc),'kind':kind,'target_source':value-0x10000})
        seeds=[]
        for seed in metadata['seeded_entities']:
            p=seed.get('addr')
            if type(p) is int and seed.get('end')==p+4 and seed.get('value_kind') in ('target_pointer','struct_pointer','string_pointer','raw_pointer'):
                value=int.from_bytes(binary[p:p+4],'big')-0x10000
                if value in exclusive:seeds.append({'source_offset':p,'target_source':value,'name':seed.get('name'),'field':seed.get('field_name'),'value_kind':seed['value_kind']})
        raw=[]
        for p in range(len(binary)-3):
            value=int.from_bytes(binary[p:p+4],'big')-0x10000
            if value in exclusive and containing(p) not in exclusive:raw.append({'source_offset':p,'target_source':value,'containing_instruction':containing(p),'aligned_word':p%2==0, 'canonical_owners':[{'name':l.get('name'),'start':l['source_start'],'end':l['source_end'],'role':l.get('role')} for l in metadata['data_block_layouts'] if l['source_start']<=p<l['source_end']]})
        groups.append({'entry':entry,'exclusive_accepted_instructions':len(exclusive),'sites':[pc for pc in [0x6DBA,0x6DBE,0x6DD6,0x6F22] if pc in exclusive],
            'external_resolved_edges':native_incoming,'outside_concrete_address_producers':producers,'typed_original_pointer_seeds':seeds,'outside_raw_DWORD_coincidences_all_byte_alignments':raw,
            'indexed_address_producer_leads':sorted({r['source_offset'] for r in dynamic_pc_addresses}),
            'remaining':'No original external entry established. A computed/stack target from an unresolved domain or original entry evidence is still needed. No gameplay trigger invented; no dead-code claim.'})
    # Check the tempting repeatable-receptacle hypothesis against all six
    # original primary states. Later mutations/lifetime conservation are NOT
    # proved by initial stock counts.
    layouts={l.get('name'):l for l in metadata['data_block_layouts']};table=layouts['item_receptacle_position_descriptors'];base=table['source_start']
    require(table['source_end']-base==72,'Receptacle descriptor population changed')
    def long(p):return int.from_bytes(binary[p:p+4],'big')
    def word(p):return int.from_bytes(binary[p:p+2],'big')
    receptacles=[]
    for i in range(6):
        p=base+i*12;state=long(p)-0x10000;interaction=long(state+26)-0x10000
        receptacles.append({'index':i,'descriptor_source':p,'x':word(p+4),'y':word(p+6),'primary_state_source':state,'initial_attachment_runtime':long(state+20),
            'interaction_source':interaction,'initial_saved_attachment_runtime':long(interaction),'required_item_id':binary[interaction+4]})
    require(all(r['initial_attachment_runtime']!=0 and r['initial_saved_attachment_runtime']==0 for r in receptacles),'Initial receptacle hypothesis needs rereview')
    # Adjudicate the sole indexed address-producing candidate, rather than
    # leaving it as an unexplained possibility. Direct profile writers0/1
    # establish the ordinary domain; unchecked/corrupted state is not closed.
    indexed={r['source_offset'] for r in decoded for o in r['operand_facts'] if o.get('access')=='address' and o.get('indexed')}
    require(indexed=={0xA15E},'Indexed producer population changed')
    profile_writers=[]
    for row in decoded:
        if any(o.get('base_register')=='A6' and o.get('displacement')==0x2CA and o['access']=='memory_write' for o in row['operand_facts']):profile_writers.append(row['source_offset'])
    require(set(profile_writers)=={0x6AE,0x6C6,0x9EEC},'Camera profile writers changed')
    require(by[0x6AE]['mnemonic']=='clr' and all(D[p]['operand_facts'][0].get('immediate_value')==1 for p in [0x6C6,0x9EEC]),'Camera index domain changed')
    nav=load(paths['navigation']);profile=next(x['addr'] for x in nav['groups']['labels'] if x['symbol']=='camera_scroll_profiles')
    require(profile==0xA146 and [word(profile+i) for i in range(0,12,2)]==[4,0,0,6,32,16],'Camera table identity differs')
    computed_review={'source_offset':0xA15E,'instruction':by[0xA15E]['text'],'direct_scalar_writers':[render(p) for p in sorted(profile_writers)],
        'ordinary_profile_indices':[0,1],'index_calculation':[render(p) for p in [0xA152,0xA156,0xA158,0xA15A,0xA15C]],
        'ordinary_table_element_sources':[profile,profile+6],'immediate_consumers':[render(p) for p in [0xA162,0xA166,0xA168]],
        'disposition':'Camera data address, not an established code-entry producer under the original profile0/1 domain.',
        'limits':'Direct scalar writer/initialized-state domain only; existing corrupted index/alias domains are not proved impossible.'}
    intena=[{**render(pc),'operands':D[pc]['operand_facts']} for pc in starts if 'intena' in by[pc]['text'].lower()]
    prior_path=Path(__file__).resolve().parents[2]/'runtime/observations/pandora-saved-route-app-watch.json'
    prior=load(prior_path);inventory=load(paths['inventory'])
    require(sha(paths['source'])==prior['input_identities']['original_rendered_source_sha256'],'Source differs from reviewed watch inventory')
    counts={'unexplained_slots':len([x for x in closure['named_slot_alias_checks'] if x['app_offset'] in (0x2D4,0x368)]),'conditional_A6_entry_sites':closure['counts']['omitted_entry_not_established'],'gap_regions':inventory['counts']['declaration_gaps'],'gap_bytes':inventory['counts']['declaration_gap_bytes']}
    question_sites={name:[render(pc) for pc in positions] for name,positions in {'190':[0x4B6,0x6130],'2D4':[0x8362,0x8366,0x9FB2],'368':[0x8F4,0x928,0x92E,0x932]}.items()}
    return {'schema_version':1,'scope':'targeted_static_followup_not_new_runtime_coverage','target_id':closure['identity']['target'],
        'input_sha256':{str(p.relative_to(root)):sha(p) for p in paths.values()},'auditor_sha256':sha(Path(__file__)),
        'prior_watch_receipt_sha256':sha(prior_path),'before':counts,'after':dict(counts),
        'newly_closed_semantic_obligations':0,'adjudicated_new_static_leads':2,'new_runtime_runs':0,
        'discarded_intermediate_cache':{'file':'.runtime-state/pandora-app-usage-closure/reviewed-data-edges.json','reason':'Private intermediate store provenance0xA9E differs from canonical0xA9C. The published closure supplies all40 reviewed edges; the intermediate is NOT consumed.'},
        'new_mechanism_checks':{'accepted_instruction_rows_checked':len(by),'direct_A6_read_instructions':direct,'direct_A6_register_copy_escapes':escapes,'register_list_A6_saves':[render(r['source_offset']) for r in register_list_saves],'reviewed_balanced_save_restore_pairs':pairs,
            'orphan_entry_groups':groups,'indexed_producer_review':computed_review,'original_receptacle_states':receptacles},
        'known_slot_instructions':question_sites,'accepted_INTENA_writes':intena,
        'conclusions':[
            'All accepted-code direct A6 reads are the two reviewed stack saves; no direct A6-to-other-register copy producer was found. Stack/group restore checks retain normal-return/valid-stack assumptions.',
            'The14 earlier reviewed save/restore pairs match register populations. This does not establish exclusive values for662 generic register aliases or opaque/computed memory loads.',
            'Initial NULL-attachment farming is not available in the six original receptacle seeds. A later reachable detach leaving saved attachment NULL would need a concrete original producer before a repetition scenario is justified.',
            'INTENA writes alone do not establish that the raw BLIT callback branch cannot be selected: source$8F4 samples INTREQR without masking by INTENA. A sole raw BLIT request at that sample is the exact branch condition. No original condition producing that entry/sample combination was established.',
            'The+$2D4 shadow producer/reset is already documented and now runtime-observed. No new consumer purpose follows; existing unchecked cursor/lifetime domains remain.',
            'The+$190 noop seed and text-row alias are both established operations; neither identifies initialization intent. A former callback-offset/typo explanation remains a hypothesis requiring another original build/source or producer/consumer evidence.',
            'The only indexed address producer at$A15E is the camera data-table lookup. Direct profile writers use0/1 and compute six-byte element addresses$A146/$A14C, not orphan code addresses. The single unaligned raw DWORD coincidence at$44BEF→$6F00 is canonically owned by scene pixel bank47 and has no pointer seed or code reference; it is not admitted as an entry edge.',
            'No original normal-input condition for the four unestablished A6 entries was found. The existing ending route is not repeated; arbitrary routine entry or injected state would not settle original use.'],
        'limits':['Accepted code and reviewed original seeds/CFG only. Computed, split, opaque, modified data and unaccepted-code targets are not excluded.',
            'Raw DWORD coincidences, if any, are leads only, not recognized pointers or control-flow edges.',
            'No dead-storage/unused-memory proof, source output changes, native-C work or paused capability work.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--qualified-checkout',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=build(a.qualified_checkout.resolve());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'before':report['before'],'after':report['after'],'groups':report['new_mechanism_checks']['orphan_entry_groups']},indent=2))

if __name__=='__main__':main()
