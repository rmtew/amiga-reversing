"""Consume a bounded native allocation plan; never discover or place references."""
from __future__ import annotations

import hashlib
import json


def plan_digest(plan):
    return hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def capsule(plan, *, scratch_extra=0, fault=None):
    result=dict(plan=plan,plan_sha256=plan_digest(plan),scratch_extra=scratch_extra,fault=fault)
    validate(result)
    return result


def validate(value):
    if not isinstance(value,dict) or set(value)!={'plan','plan_sha256','scratch_extra','fault'}:
        raise ValueError('Explicit native allocation capsule required')
    p=value['plan']
    if (not isinstance(p,dict) or p.get('status')!='bounded_allocation_candidate'
            or p.get('scope')!='reviewed_typed_LONG_data_only_not_all_path_alias_proof'
            or plan_digest(p)!=value['plan_sha256']):
        raise ValueError('Missing, stale or refused native allocation candidate')
    if type(value['scratch_extra']) is not int or value['scratch_extra'] not in (0,64):
        raise ValueError('Only the bounded zero/64-byte scratch profiles are supported')
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
    if not isinstance(fixes,list) or not fixes or len(fixes)>32:
        raise ValueError('Bounded typed fixup list required')
    previous=-4
    for f in sorted(fixes,key=lambda f:f.get('source_offset',-1)):
        if (set(f)!={'source_section_index','source_offset','width','encoding','address_domain','region_offset','staged_value'}
                or f['source_section_index']!=0 or f['width']!=4
                or f['encoding']!='absolute_long_data' or f['address_domain']!='runtime_only'
                or any(type(f[k]) is not int for k in ('source_offset','region_offset','staged_value'))
                or f['source_offset']<previous+4 or not 0<=f['region_offset']<p['size']
                or not 0<=f['staged_value']<=0xffffffff):
            raise ValueError('Unsupported, overlapping or untyped runtime fixup')
        previous=f['source_offset']
    return p,layout[0]


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
        for source,_,size in seed_copies:
            if offset<source+size and source<offset+4:
                raise ValueError('A runtime fixup may not change an original-byte seed')


def allocation_source(value,contract,payload_size,spans):
    p,layout=validate(value);record=contract.handoff_marker_address-0xf8
    record_index=spans.index((record,0xf0))
    constants=dict(RUNTIME_ALLOCATION=1,ALLOCATION_RECORD=record,ALLOCATION_SIZE=p['size'],
        ALLOCATION_SCRATCH_EXTRA=value['scratch_extra'],ALLOCATION_STATIC_READY=len(spans),
        ALLOCATION_RECORD_OWNED=record_index+1)
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
    raw=client.read_memory(record,24)
    if raw[:4]!=b'ALLO' or int.from_bytes(raw[16:20],'big')!=1:
        raise ValueError('Guest allocation did not reach the initialized live-lease state')
    base=int.from_bytes(raw[4:8],'big');guard=int.from_bytes(raw[8:12],'big');guard_size=int.from_bytes(raw[12:16],'big')
    if not base:raise ValueError('Guest allocator returned NULL')
    from .direct_payload_adapter import reservation_plan
    count=len(reservation_plan(contract,len(payload)))
    if int.from_bytes(raw[20:24],'big')!=count or int.from_bytes(client.read_memory(contract.handoff_marker_address-4,4),'big')!=count:
        raise ValueError('Guest static backing acquisition is incomplete')
    result=bytearray(payload)
    for f in p['fixups']:
        value=base+f['region_offset']
        if value>0xffffff:raise ValueError('Returned address overflows the guest domain')
        result[f['source_offset']:f['source_offset']+4]=value.to_bytes(4,'big')
    return bytes(result),dict(region_id=p['region_id'],base=base,size=p['size'],
        scratch_base=guard,scratch_size=guard_size,record_address=record,static_reservations_acquired=count,
        status='guest_lease_live_requires_native_placement_admission',plan_sha256=contract.runtime_allocation['plan_sha256'])


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
    record_owned=int.from_bytes(client.read_memory(marker-4,4),'big')>spans.index((marker-0xf8,0xf0))
    record=client.read_memory(marker-0xf8,24) if record_owned else b''
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
