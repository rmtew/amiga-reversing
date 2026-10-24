"""Consume a bounded native allocation plan; never discover or place references."""
from __future__ import annotations

import hashlib
import json
import re

CPU_SCOPE='reviewed_symbolic_absolute_operands_and_LONG_data_not_all_path_alias_proof'
DMA_ADDRESS_SCOPE='reviewed_symbolic_LONG_LEA_and_data_Chip_only_not_all_path_alias_proof'


def plan_digest(plan):
    return hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def capsule(plan, *, scratch_extra=0, fault=None,prior_allocation_bytes=0):
    result=dict(plan=plan,plan_sha256=plan_digest(plan),scratch_extra=scratch_extra,fault=fault)
    if plan.get('scope')==CPU_SCOPE:result['prior_allocation_bytes']=prior_allocation_bytes
    elif prior_allocation_bytes:raise ValueError('Prior allocation profile requires the CPU contract')
    validate(result)
    return result


def validate(value):
    if not isinstance(value,dict):raise ValueError('Explicit native allocation capsule required')
    p=value.get('plan');cpu=isinstance(p,dict) and p.get('scope')==CPU_SCOPE
    dma_address=isinstance(p,dict) and p.get('scope')==DMA_ADDRESS_SCOPE
    if set(value)!=({'plan','plan_sha256','scratch_extra','fault'}|({'prior_allocation_bytes'} if cpu else set())):
        raise ValueError('Explicit native allocation capsule required')
    if (not isinstance(p,dict) or p.get('status')!='bounded_allocation_candidate'
            or p.get('scope') not in ('reviewed_typed_LONG_data_only_not_all_path_alias_proof',CPU_SCOPE,DMA_ADDRESS_SCOPE)
            or plan_digest(p)!=value['plan_sha256']):
        raise ValueError('Missing, stale or refused native allocation candidate')
    if type(value['scratch_extra']) is not int or value['scratch_extra'] not in (0,64):
        raise ValueError('Only the bounded zero/64-byte scratch profiles are supported')
    if cpu and (value['scratch_extra']!=0 or type(value['prior_allocation_bytes']) is not int
            or value['prior_allocation_bytes'] not in (0,4096)):
        raise ValueError('CPU profile requires zero quarantine padding and zero/4096 prior bytes')
    if value['fault'] not in (None,'before_owner','after_owner'):
        raise ValueError('Unsupported declared loader fault')
    if (type(p.get('size')) is not int or not 0<p['size']<=0x10000
            or p.get('memory_requirement')!='chip' or p.get('alignment') not in (1,2,4,8)
            or p.get('lifetime')!='retain_until_DMA_quiescent_exit'):
        raise ValueError('Unsupported native allocation owner')
    layout=p.get('layout',{}).get('items',[])
    if len(layout)!=1 or layout[0].get('status')!='placement_valid':
        raise ValueError('Native fixed context is refused')
    fixes=p.get('fixups')
    if not isinstance(fixes,list) or not fixes or len(fixes)>128:
        raise ValueError('Bounded typed fixup list required')
    previous=-4
    for f in sorted(fixes,key=lambda f:f.get('source_offset',-1)):
        fields={'source_section_index','source_offset','width','encoding','address_domain','region_offset','staged_value'}
        instruction=(cpu and f.get('encoding') in ('absolute_long_operand','absolute_long_immediate')) or (dma_address and f.get('encoding')=='absolute_long_operand')
        if instruction:fields|={'instruction_source_offset','operand_index','opcode','symbol'}
        if (set(f)!=fields
                or f['source_section_index']!=0 or f['width']!=4
                or (not instruction and f['encoding']!='absolute_long_data') or f['address_domain']!='runtime_only'
                or any(type(f[k]) is not int for k in ('source_offset','region_offset','staged_value'))
                or f['source_offset']<previous+4 or not 0<=f['region_offset']<p['size']
                or not 0<=f['staged_value']<=0xffffffff):
            raise ValueError('Unsupported, overlapping or untyped runtime fixup')
        if instruction and (any(type(f[k]) is not int for k in ('instruction_source_offset','operand_index','opcode'))
                or f['instruction_source_offset']<0 or f['instruction_source_offset']%2
                or f['source_offset']<f['instruction_source_offset']+2
                or not 0<=f['operand_index']<4 or not 0<=f['opcode']<=0xffff
                or not isinstance(f['symbol'],str) or not f['symbol']):
            raise ValueError('Missing native instruction field identity')
        if (cpu or dma_address) and f['staged_value']!=p['staged_address']+f['region_offset']:
            raise ValueError('Native staged instruction value is inconsistent')
        previous=f['source_offset']
    if dma_address:
        owner=next((r for r in layout[0]['regions'] if r['region_id']==p['region_id']),None)
        if (not owner or owner.get('parent_region_id') or owner.get('region_kind')!='storage'
                or owner['size']!=p['size'] or owner['runtime_address']!=p['staged_address']
                or 'address_frame' in owner or 'address_frame_guards' in p
                or any(r.get('parent_region_id')==p['region_id'] for r in layout[0]['regions'])
                or p.get('numeric_immediate_candidates_not_fixups')!=0
                or not any(f['encoding']=='absolute_long_operand' for f in fixes)):
            raise ValueError('DMA storage requires native LONG LEA/data fields without unknown numeric aliases')
    if cpu:
        owner=next((r for r in layout[0]['regions'] if r['region_id']==p['region_id']),None)
        frame=owner.get('address_frame',{}) if owner else {}
        guards=p.get('address_frame_guards')
        # A leaf such as the keyboard table has no lowered frame-relative
        # instructions. Admit only native-projected symbolic LONG operands;
        # never waive an existing frame contract or promote numeric candidates.
        if owner and 'address_frame' not in owner:
            if (owner.get('parent_region_id') or owner.get('region_kind')!='storage'
                    or owner['size']!=p['size'] or owner['runtime_address']!=p['staged_address']
                    or any(r.get('parent_region_id')==p['region_id'] for r in layout[0]['regions'])
                    or 'address_frame_guards' in p or 'address_frame_contract_sha256' in p
                    or p.get('numeric_immediate_candidates_not_fixups')!=0
                    or any(f['encoding'] not in ('absolute_long_operand','absolute_long_immediate') for f in fixes)):
                raise ValueError('CPU leaf allocation requires only native symbolic LONG operands')
            return p,layout[0]
        if (not owner or owner.get('parent_region_id') or owner['size']!=p['size']
                or owner['runtime_address']!=p['staged_address'] or not frame.get('active')
                or frame.get('contract_sha256')!=p.get('address_frame_contract_sha256')
                or not re.fullmatch('[0-9a-f]{64}',str(p.get('address_frame_contract_sha256','')))
                or not isinstance(guards,list) or not 1<=len(guards)<=8
                or len(guards)!=len(frame.get('sites',[]))):
            raise ValueError('CPU allocation requires the native reviewed address-frame guards')
        expected={s['source_offset'] for s in frame['sites']};seen=set()
        for g in guards:
            if (set(g)!={'instruction_source_offset','opcode','displacement_source_offset','displacement','base_register','instruction_size'}
                    or any(type(x) is not int for x in g.values()) or g['instruction_source_offset'] not in expected
                    or g['instruction_source_offset'] in seen or g['instruction_size']!=8
                    or g['displacement_source_offset']!=g['instruction_source_offset']+6
                    or not 0<=g['opcode']<=0xffff or not 0<=g['displacement']<=0x7fff
                    or frame['register']!='a'+str(g['base_register'])):
                raise ValueError('Invalid native address-frame guard')
            seen.add(g['instruction_source_offset'])
            for off in (g['instruction_source_offset'],g['displacement_source_offset']):
                if any(f['source_offset']<off+2 and off<f['source_offset']+4 for f in fixes):
                    raise ValueError('Runtime patch overlaps an immutable frame guard')
    return p,layout[0]


def replace_static_CPU_lease(config,plan):
    """Remove exactly one native owner claim; retain keyboard and seed backing."""
    if plan.get('scope')!=CPU_SCOPE:raise ValueError('CPU native plan required')
    if len(config.get('loader_family',[]))!=1 or config['layout_id']!=plan['layout']['items'][0]['layout_id']:
        raise ValueError('CPU allocation requires a single reviewed static template')
    address,size=plan['staged_address'],(plan['size']+7)&~7
    spans=config['loader_shared_reservations']
    if address%8 or sum(tuple(s)==(address,size) for s in spans)!=1:
        raise ValueError('Native CPU owner backing is absent or coalesced with another owner')
    if any(a<address+size and address<a+n for a,n in spans if (a,n)!=(address,size)):
        raise ValueError('Another static claim aliases the dynamic CPU owner')
    return dict(config,loader_shared_reservations=[s for s in spans if tuple(s)!=(address,size)],
        runtime_replaced_owner_reservation=dict(region_id=plan['region_id'],address=address,size=size,
            native_plan_sha256=plan_digest(plan)))


def CPU_static_reservation_source(value,spans,marker):
    """Compact emission of the same shared reservation plan, not placement."""
    p,_=validate(value)
    if p['scope']!=CPU_SCOPE or not 1<=len(spans)<=32:
        raise ValueError('Bounded CPU static reservation list required')
    lines=['    moveq #0,d4','    lea allocation_static_table(pc),a2',
        'allocation_static_acquire:', '    movea.l (a2)+,a1','    move.l (a2)+,d0',
        '    jsr _LVOAllocAbs(a6)','    cmp.l -8(a2),d0','    beq.w allocation_static_acquired',
        '    tst.w d4','    beq.w reservation_unowned','    bra.w failed',
        'allocation_static_acquired:','    addq.l #1,d4',f'    move.l d4,${marker-4:X}',
        '    cmpi.w #1,d4','    bne.w allocation_static_next','    lea start(pc),a0',
        f'    move.l a0,${marker-8:X}','allocation_static_next:',
        f'    cmpi.w #{len(spans)},d4','    bne.w allocation_static_acquire',
        '    bra.w allocation_static_table_end','allocation_static_table:']
    lines += [f'    dc.l ${a:X},${n:X}' for a,n in spans]
    lines += ['allocation_static_table_end:']
    return lines


def allocation_backing(value,marker):
    p,layout=validate(value)
    if marker%8 or marker-0xf8<0x1000:raise ValueError('Allocation mailbox must be aligned owned RAM')
    record=marker-0xf8
    for protected in p['protected_ranges']:
        if record<protected['address']+protected['size'] and protected['address']<record+0xf0:
            raise ValueError('Allocation telemetry overlaps a protected canonical runtime extent')
    spans=[(record,0xf0)]
    for r in layout['regions']:
        if not r.get('parent_region_id') and r.get('region_kind') in ('image','display'):
            address,size=r['runtime_address'],r['size']
            if address%8:raise ValueError('Fixed resource lease needs an aligned canonical base')
            spans.append((address,(size+7)&~7))
    return tuple(spans)


def validate_payload(value,payload,load_address,marker,seed_copies=()):
    p,layout=validate(value)
    if len(payload)!=layout['bootstrap']['file_size']:raise ValueError('Allocation capsule input extent is stale')
    record=marker-0xf8
    if load_address<record+0xf0 and record<load_address+len(payload):
        raise ValueError('Allocation telemetry overlaps live staged input')
    for f in p['fixups']:
        offset=f['source_offset']
        if offset+4>len(payload) or payload[offset:offset+4]!=f['staged_value'].to_bytes(4,'big'):
            raise ValueError('Native typed fixup is stale for the staged payload')
        if 'opcode' in f:
            start=f['instruction_source_offset']
            if payload[start:start+2]!=f['opcode'].to_bytes(2,'big'):
                raise ValueError('Native instruction opcode is stale for the staged payload')
        for source,_,size in seed_copies:
            if offset<source+size and source<offset+4:
                raise ValueError('A runtime fixup may not change an original-byte seed')
    for g in p.get('address_frame_guards',[]):
        for off,value in ((g['instruction_source_offset'],g['opcode']),
                          (g['displacement_source_offset'],g['displacement'])):
            if payload[off:off+2]!=value.to_bytes(2,'big'):
                raise ValueError('Native address-frame guard is stale for the staged payload')


def allocation_source(value,contract,payload_size,spans):
    p,layout=validate(value);record=contract.handoff_marker_address-0xf8
    record_index=spans.index((record,0xf0))
    constants=dict(RUNTIME_ALLOCATION=1,ALLOCATION_RECORD=record,ALLOCATION_SIZE=p['size'],
        ALLOCATION_SCRATCH_EXTRA=value['scratch_extra'],ALLOCATION_STATIC_READY=len(spans),
        ALLOCATION_RECORD_OWNED=record_index+1)
    if p['scope']==CPU_SCOPE:
        constants.update(ALLOCATION_CPU=1,ALLOCATION_PRIOR_BYTES=value['prior_allocation_bytes'])
        if any(a<p['staged_address']+p['size'] and p['staged_address']<a+n for a,n in spans):
            raise ValueError('CPU owner is still covered by a fixed static lease')
    if value['fault']:constants['ALLOCATION_FAIL_'+('BEFORE' if value['fault']=='before_owner' else 'AFTER')]=1
    exclusions=[]
    for i,r in enumerate(p['protected_ranges']):
        start,end=r['address'],r['address']+r['size']
        if any(base<=start and end<=base+size for base,size in spans):continue
        exclusions.extend((f'    cmpi.l #${end:X},d2',f'    bcc.w allocation_next_{i}',
            f'    cmpi.l #${start:X},d3',f'    bls.w allocation_next_{i}',
            f'    move.l #${end:X},d6','    bra.w allocation_collision',f'allocation_next_{i}:'))
    exclusions.append('    bra.w allocation_owner_valid')
    fixes=[]
    for f in p['fixups']:
        address=contract.load_address+f['source_offset']
        if f['source_offset']+4>payload_size:raise ValueError('Fixup outside full input')
        fixes.extend((f"    cmpi.l #${f['staged_value']:X},${address:X}",'    bne.w failed',
                      f'    move.l ${record+4:X},d0'))
        if f['region_offset']:fixes.append(f"    addi.l #${f['region_offset']:X},d0")
        fixes.append(f'    move.l d0,${address:X}')
    unwind=[]
    if p['scope']==CPU_SCOPE:
        unwind=['    lea allocation_static_table(pc),a2','    move.w d4,d5',
            '    lsl.w #3,d5','    adda.w d5,a2','    move.w d4,d5',
            'allocation_static_free_next:','    subq.w #1,d5','    beq.w allocation_static_free_done',
            '    subq.l #8,a2',f'    cmpi.w #{record_index},d5','    beq.w allocation_static_free_next',
            '    movea.l (a2),a1','    move.l 4(a2),d0','    jsr _LVOFreeMem(a6)',
            '    bra.w allocation_static_free_next','allocation_static_free_done:']
    else:
        for i in reversed(range(1,len(spans))):
            if i==record_index:continue
            address,size=spans[i]
            unwind.extend((f'    cmpi.l #{i+1},d4',f'    bcs.w allocation_static_skip_{i}',
                f'    movea.l #${address:X},a1',f'    move.l #${size:X},d0',
                '    jsr _LVOFreeMem(a6)',f'allocation_static_skip_{i}:'))
    return {name:'\n'.join(lines)+'\n' for name,lines in (
        ('direct_payload_allocation_exclusions.i',exclusions),
        ('direct_payload_allocation_fixups.i',fixes),
        ('direct_payload_allocation_static_unwind.i',unwind))},constants


def consume_return(client,contract,payload):
    """Read the guest return; caller must validate actual placement natively before GO."""
    p,_=validate(contract.runtime_allocation);record=contract.handoff_marker_address-0xf8
    cpu=p['scope']==CPU_SCOPE
    raw=client.read_memory(record,32 if cpu else 24)
    if raw[:4]!=b'ALLO' or int.from_bytes(raw[16:20],'big')!=1:
        raise ValueError('Guest allocation did not reach the initialized live-lease state')
    base=int.from_bytes(raw[4:8],'big');guard=int.from_bytes(raw[8:12],'big');guard_size=int.from_bytes(raw[12:16],'big')
    if not base:raise ValueError('Guest allocator returned NULL')
    from .direct_payload_adapter import reservation_plan
    static_spans=reservation_plan(contract,len(payload))
    prior_base=prior_size=0
    if cpu:
        prior_base=int.from_bytes(raw[24:28],'big');prior_size=int.from_bytes(raw[28:32],'big')
        if (prior_size!=contract.runtime_allocation['prior_allocation_bytes']
                or bool(prior_base)!=bool(prior_size) or prior_base%8
                or prior_base+prior_size>p['layout']['items'][0]['chip_bytes']):
            raise ValueError('Guest prior allocation differs from the reviewed profile')
        for a,n in [(base,p['size']),*static_spans,
                    *[(r['address'],r['size']) for r in p['protected_ranges']]]:
            if prior_size and prior_base<a+n and a<prior_base+prior_size:
                raise ValueError('Guest prior lease aliases a game/input resource')
    count=len(static_spans)
    if int.from_bytes(raw[20:24],'big')!=count or int.from_bytes(client.read_memory(contract.handoff_marker_address-4,4),'big')!=count:
        raise ValueError('Guest static backing acquisition is incomplete')
    result=bytearray(payload)
    for f in p['fixups']:
        value=base+f['region_offset']
        if value>0xffffff:raise ValueError('Returned address overflows the guest domain')
        result[f['source_offset']:f['source_offset']+4]=value.to_bytes(4,'big')
    lease=dict(region_id=p['region_id'],base=base,size=p['size'],
        scratch_base=guard,scratch_size=guard_size,record_address=record,static_reservations_acquired=count,
        status='guest_lease_live_requires_native_placement_admission',plan_sha256=contract.runtime_allocation['plan_sha256'])
    if cpu:lease.update(prior_base=prior_base,prior_size=prior_size)
    return bytes(result),lease


def verify_boot_code(client,contract,boot_build):
    from pathlib import Path
    marker=contract.handoff_marker_address
    boot_base=int.from_bytes(client.read_memory(marker-8,4),'big')
    code=Path(boot_build['floppy0']).read_bytes()[12:12+boot_build['allocation_boot_code_size']]
    if (hashlib.sha256(code).hexdigest()!=boot_build['allocation_boot_code_sha256']
            or client.read_memory(boot_base,len(code))!=code):
        raise ValueError('Guest allocation loader code identity differs')
    return dict(base=boot_base,size=len(code),sha256=boot_build['allocation_boot_code_sha256'],
                symbols=boot_build['allocation_boot_symbols'])


def abort_guest(client,contract,boot_build,*,already_aborted=False):
    """No game has entered; release every owned lease through guest Exec calls."""
    from .copperline_runtime import wait_for_marker
    from pathlib import Path
    marker=contract.handoff_marker_address
    if not already_aborted:
        client.request('mem.write',{'addr':marker,'data':b'ABRT'.hex(),'encoding':'hex'})
        client.request('reverse_anchor')
    if not wait_for_marker(client,marker,b'ABOR',30)['matched']:
        raise ValueError('Guest did not reach allocation unwind acknowledgement')
    from .direct_payload_adapter import reservation_plan
    spans=reservation_plan(contract,Path(boot_build['payload']).stat().st_size)
    acquired=int.from_bytes(client.read_memory(marker-4,4),'big')
    record_owned=acquired>spans.index((marker-0xf8,0xf0))
    cpu=contract.runtime_allocation['plan']['scope']==CPU_SCOPE
    record=client.read_memory(marker-0xf8,32 if cpu else 24) if record_owned else b''
    # Before all static claims exist the guest never initializes this record or
    # acquires dynamic leases. Its previous RAM contents are not ownership.
    if acquired==len(spans) and record and any(int.from_bytes(record[offset:offset+4],'big') for offset in ((4,8,24) if cpu else (4,8))):
        raise ValueError('Guest allocation unwind retained an owned lease')
    verified=verify_boot_code(client,contract,boot_build)
    boot_base=verified['base'];closed=boot_base+verified['symbols']['allocation_closed']
    client.request('mem.write',{'addr':marker,'data':b'FREE'.hex(),'encoding':'hex'})
    client.request('reverse_anchor')
    # Observe the exact assembled completion label, including a ROM-task/IRQ
    # preemption. No frame-latency assertion or guest CPU register write.
    from .copperline_runtime import wait_for_pc
    stop=wait_for_pc(client,closed,30)
    if stop['status']!='hit':raise ValueError('Guest final ownership release was not observed')
    registers=client.registers()
    if registers['d3']!=int.from_bytes(b'FREE','big'):
        raise ValueError('Guest final ownership release did not complete: '+repr(dict(stop=stop,registers=registers,pc_bytes=client.read_memory(registers['pc'],24).hex())))
    return dict(status='guest_unwind_complete_diagnostic_hold_not_OS_return',
        pre_release_record=record.hex(),after_release_registers=registers,stop=stop,boot_base=boot_base,completion_pc=closed,
        acknowledgement_scope='Loader protocol only; no gameplay entered or CPU registers forced')
