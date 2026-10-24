"""Audit the bounded allocated-body save/restore episode, not all callers/lifetimes."""
from collections import Counter
import json
from pathlib import Path

from .copperline_bus_trace import read_bus_profile

SIZE=2304


def compare_windows(producer,consumer,base):
    """Preserve recorded order; missing consumer words remain explicit coverage."""
    saved={};consumed=set();counts=Counter();mismatches=[];identities=[];last_frame=-1
    for role,report in [('producer',producer),('consumer',consumer)]:
        if report['profile_summary'].get('samples_dropped')!=0 or report['omitted_matching_records']:
            raise ValueError('Incomplete/truncated body DMA evidence')
        # Publish sidecar identities/coverage, not the full raw blit-state dump.
        frames=[{key:value for key,value in frame.items() if key in
                 ('frame','partial','rows','line_cck','cck_length','slots_sha256','slots_bytes')}
                for frame in report['frames']]
        identities.append(dict(role=role,frames=frames,summary=report['profile_summary']))
        for record in report['records']:
            if record['frame']<last_frame:raise ValueError('Body trace order is not chronological')
            last_frame=record['frame']
            if 'old' in record['ranges']:
                raise ValueError('Observed abandoned body-buffer access')
            if record['engine']!='blitter':continue
            address=record['address'];value=record['data']
            if record['size']!=2 or address%2 or not base<=address<base+SIZE:
                raise ValueError('Unsupported body transfer width/alignment/extent')
            counts[role+'_'+record['access']]+=1
            if role=='producer' and record['access']=='write':
                if address in saved:raise ValueError('Repeated body producer write needs separate lifetime analysis')
                saved[address]=value
            elif role=='consumer' and record['access']=='read':
                if address in consumed:raise ValueError('Repeated body consumer read needs separate episode analysis')
                consumed.add(address)
                if saved.get(address)!=value:
                    mismatches.append(dict(address=address,expected=saved.get(address),observed=value,frame=record['frame']))
            else:raise ValueError('Unexpected body-buffer interference')
    if len(saved)!=SIZE//2:raise ValueError('Producer coverage is incomplete')
    reads=counts['consumer_read']
    if reads>SIZE//2:raise ValueError('Repeated consumer episode needs separate analysis')
    return dict(status='mismatch' if mismatches else 'observed_values_match',base=base,size=SIZE,
                producer_words=len(saved),consumer_reads=reads,unobserved_consumer_words=SIZE//2-reads,
                first_mismatches=mismatches[:4],mismatch_count=len(mismatches),counts=dict(counts),windows=identities,
                scope='Recorded save/restore only; intervening uncaptured writes and all-callers lifetime are not certified')


def audit(directory,base):
    directory=Path(directory)
    ranges=[dict(name='new',address=base,length=SIZE),dict(name='old',address=0x7f0,length=SIZE)]
    windows=[read_bus_profile(directory/('resource-dma-'+phase),ranges,5)
             for phase in ('il_icelord_body_row','il_recover_sonicdriver')]
    return compare_windows(*windows,base)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--base',type=lambda value:int(value,0),required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=audit(args.directory,args.base)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('windows','first_mismatches')}))
    raise SystemExit(result['status']=='mismatch')
