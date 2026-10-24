"""Bounded Pandora A6 contract audit from retained accepted-code evidence.

This admits only reviewed original targets under normal returns and matched
stacks. It is not an arbitrary-entry proof or a gameplay reachability claim.
Run with the retained access/graph directories; proprietary payload stays local.
"""
import argparse
from amiga_reversing.disasm.project_paths import PROJECT_ROOT,resolve_project_paths
from amiga_reversing.tools.pandora_layout_walkthrough import TARGET
import json,hashlib
from pathlib import Path
from collections import defaultdict,deque
from amiga_reversing.disasm.app_access_audit import explicit_register_writes

def validate_retained_inputs(original,rows,facts_bytes,edges_bytes,receipt):
    """Bind decoded semantics and graph to the already published review input.

    A newly printed digest is not admission. Coordinate and byte checks also
    prevent silent dict overwrite or pairing facts with a different listing.
    """
    digest=lambda data:hashlib.sha256(data).hexdigest()
    proof=receipt['caller_contract']['proof']
    if digest(original)!=receipt['input_sha256']:
        raise ValueError('Reviewed original input identity differs')
    if digest(facts_bytes)!=proof['facts_sha256']:
        raise ValueError('Retained decoded facts identity differs from review receipt')
    if digest(edges_bytes)!=proof['edges_sha256']:
        raise ValueError('Retained graph identity differs from review receipt')
    facts=json.loads(facts_bytes);edges=json.loads(edges_bytes)
    def index(items):
        result={}
        for item in items:
            key=(item.get('section_index'),item.get('source_offset'))
            if (key[0]!=0 or type(key[1]) is not int or key[1]<0 or key in result
                    or type(item.get('size')) is not int or item['size']<=0):
                raise ValueError('Retained instruction coordinates must be unique and bounded')
            result[key]=item
        return result
    listed,decoded=index(rows),index(facts)
    if listed.keys()!=decoded.keys():raise ValueError('Retained instruction coordinate sets differ')
    for key,row in listed.items():
        raw=bytes.fromhex(row['bytes']);offset=key[1]
        if (len(raw)!=row['size'] or decoded[key]['size']!=row['size']
                or original[offset:offset+row['size']]!=raw):
            raise ValueError('Retained instruction sizes or original bytes differ')
    return facts,edges

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-directory',type=Path,required=True)
    parser.add_argument('--graph-directory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not __debug__:raise RuntimeError('This diagnostic requires enabled assertion checks')
    r=args.graph_directory
    a=args.evidence_directory
    original=(resolve_project_paths(TARGET).target_dir/'binary.bin').read_bytes()
    assert hashlib.sha256(original).hexdigest()=='70480017cbedb4ed1d28c0bb190917720b8d2780914c37622b0df92c070aee8f'
    rows=json.loads((a/'instructions.json').read_text())
    receipt=json.loads((PROJECT_ROOT/'runtime/observations/pandora-passage-address-frame-contract.json').read_text())
    facts,native_edges=validate_retained_inputs(original,rows,(r/'decoded-registers.json').read_bytes(),
        (r/'edges.json').read_bytes(),receipt)
    assert len(rows)==len(facts)==7059
    for x in rows:assert original[x['source_offset']:x['source_offset']+x['size']]==bytes.fromhex(x['bytes'])
    ins={x['source_offset']:dict(x,register_writes=explicit_register_writes(x)) for x in facts}
    closure=json.loads((PROJECT_ROOT/'docs/validation/pandora-app-usage-closure.json').read_text())
    restores={x['restore']:x['save'] for x in closure['restore_save_pairs']};saves=sorted(set(restores.values()));slots={p:i for i,p in enumerate(saves)}
    assert {p for p,x in ins.items() if 'A6' in x['register_writes']}==set(restores)|{0x48c,0x8e8,0x4d978,0x4d98e}
    if hashlib.sha256(json.dumps(native_edges,sort_keys=True).encode()).hexdigest()!=closure['input_graph_sha256']:
        raise ValueError('Native graph differs from canonical prior closure receipt')
    edges=native_edges+closure['reviewed_data_edges']
    by=defaultdict(list)
    for e in edges:by[e['source_offset']].append(e)
    # Explicit original audio callers are immediately enclosed by an A6 save and
    # restore. Their normal return is the only edge skipped into the HW clobbering
    # callee in the APP invariant; audit that callee separately below.
    protected={0x9d0:0x4d8fc,0xfe2:0x4d8fc}
    assert {e['source_offset'] for e in edges if e['kind']=='call' and e.get('target_offset')==0x4d8fc}==set(protected)
    for call,target in protected.items():
     assert restores[call+ins[call]['size']]==call-4
    for restore,save in restores.items():
     def regs(pc,access):
      out=set()
      for op in ins[pc]['operand_facts']:
       if op['access']==access:out.update(op['register_list'] or ([op['direct_register']] if op['direct_register'] else []))
      return out
     rs=regs(restore,'register_list_write')|regs(restore,'register_write')
     ss=regs(save,'register_list_read')|regs(save,'memory_read')
     assert 'A6' in rs and rs==ss,(hex(save),hex(restore),ss,rs)
    
    def successors(pc,*,cut_audio=False):
     row=ins[pc];ee=by[pc]
     if ee:
      return sorted({e['target_offset'] for e in ee if e.get('status')=='resolved' and e['kind']!='return' and e.get('target_offset') in ins and not(cut_audio and pc in protected and e['kind']=='call')})
     return [pc+row['size']] if row['flow']=='sequential' and pc+row['size'] in ins else []
    # All original return edges stop here; caller returns are handled only under
    # normal-return/intact-stack. There is no inferred return from HW to a store.
    reached=set();todo=[0x4d8fc]
    while todo:
     p=todo.pop()
     if p in reached:continue
     reached.add(p);todo.extend(successors(p))
    assert not reached & {0x78c4,0x79f2,0x9f38,0x4b0ce}
    APP,UNKNOWN,UNSET=1,2,4
    
    def analyze(extra_clobber=None):
     states={};pending=deque();undefined=[UNSET]*len(saves)
     def add(pc,state):
      if pc not in ins:return
      old=states.get(pc);new=tuple(a|b for a,b in zip(old,state)) if old else tuple(state)
      if new!=old:states[pc]=new;pending.append(pc)
     add(0x48c,[UNKNOWN]+undefined);add(0x8e4,[UNKNOWN]+undefined)
     while pending:
      pc=pending.popleft();state=list(states[pc]);row=ins[pc]
      if pc in slots:state[slots[pc]+1]=state[0]
      if pc in (0x48c,0x8e8):state[0]=APP
      elif pc in restores:
       value=state[slots[restores[pc]]+1];state[0]=value if not value&UNSET else value|UNKNOWN
      elif 'A6' in row['register_writes']:state[0]=UNKNOWN
      if pc==extra_clobber:state[0]=UNKNOWN
      # Relative opcode22 has no original stored command in the reviewed
      # corpus: do not invent a normal-return edge for an unsupported path.
      if pc==0x11f2:continue
      if pc==0x932:state[0]=UNKNOWN  # Unknown BLIT callback cannot promise A6.
      for q in successors(pc,cut_audio=True):add(q,state)
     return states
    states=analyze()
    points=[0x78c4,0x79f2,0x9f38,0x7a00,0x93f4,0x4b0ce]
    result={hex(p):states.get(p,(0,))[0] for p in points}
    irq_returns={0x90e,0x926,0x93e,0x94c}
    normal_returns=[p for p,s in states.items() if ins[p]['flow']=='return' and p not in irq_returns]
    assert all(states[p][0]==APP for p in normal_returns),[(hex(p),states[p][0]) for p in normal_returns if states[p][0]!=APP]
    print('A6 values',result,'states',len(states),'audio scope',len(reached))
    assert all(v==APP for v in result.values()),result
    # A new clobber immediately preceding the callback dispatch must poison it.
    negative=analyze(0x93f2)
    print('negative callback',negative.get(0x4b0ce,(0,))[0]);assert negative[0x4b0ce][0]&UNKNOWN
    out=dict(status='conditional_original_paths_APP_invariant',points=result,states=len(states),normal_returns=len(normal_returns),audio_scope=len(reached),save_pairs=restores,excluded_relative_command=hex(0x11f2),unknown_BLIT_return=hex(0x932),
     assumptions=['Normal call returns and intact matched stack frames; no hostile stack mutation.', 'Only reviewed original stored callback/command targets; no arbitrary or replacement entry.', 'Original IRQ entry saves caller A6 and establishes its own APP frame; no reentry that overwrites a live saved-frame slot.'],
     input_sha256=hashlib.sha256(original).hexdigest(),auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),facts_sha256=hashlib.sha256((r/'decoded-registers.json').read_bytes()).hexdigest(),edges_sha256=hashlib.sha256((r/'edges.json').read_bytes()).hexdigest())
    args.output.write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':main()
