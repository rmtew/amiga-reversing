"""Normal-input departure from the unarmed console through engineering."""
from .pandora_player import PlayerPlan,goal,PLAYER

LEGS=[('down', [507, 1770]), ('left', [395, 1770]), ('down', [402, 1770]), ('up', [402, 1650]), ('right', [682, 1650]), ('right', [780, 1650]), ('left', [773, 1650]), ('up', [780, 1650]), ('down', [780, 1694]), ('right', [1060, 1694]), ('right', [1067, 1694]), ('left', [1060, 1694]), ('down', [1067, 1754]), ('right', [1298, 1754]), ('left', [1291, 1754]), ('down', [1298, 1754]), ('up', [1298, 1594]), ('up', [1298, 1514]), ('up', [1298, 1354]), ('up', [1298, 1322])]


def depart_engineering():
    p=PlayerPlan(0x5D6,modal=False,xy=[514,1706],held=50,expected_health=32)
    for i,(direction,xy) in enumerate(LEGS):
        if direction=='right' and xy==[1060,1694]:
            p.action('wait_kwik_kleen_start',0x5D6,
                until={'address':0x5BBE6,'size':4,'expect_hex':'03640694'},
                visits=1024,frames=1600)
        p.move_to(f'depart_engineering_{i}',direction,xy)
    p.action('engineering_departure',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads += [{'address':0x3D27,'size':18,'expect_hex':'00'*18,'expect_mask_hex':'ff'+'00'*17},goal(PLAYER+22,bytes([50]))]
    next(r for r in reads if r.get('address')==0x3B92).update(expect_hex='3000312624372123')
    return p.scenario


def prepare_departure(*,cold=False):
    """Inspect the unarmed console and clear engineering, without claiming escape."""
    from .pandora_console import inspect_console
    s=inspect_console(cold=cold);previous=s['phases'][-1]['name'];tail=depart_engineering()
    s['phases']+=tail['phases'][2:]
    for event in tail['input_events']:
        if event['after_phase']=='anchor':event['after_phase']=previous
        s['input_events'].append(event)
    s['identifier']='pandora-unarmed-console-and-departure';return s



def inspect_return():
    """Unarmed checkpoint inspection: console, engineering and shaft wrap.

    Stops ABOVE the live Icelord; this is not an escape-completion plan.
    """
    from .pandora_player import goal,PLAYER
    s=prepare_departure();previous=s['phases'][-1]['name']
    p=PlayerPlan(0x5D6,modal=False,xy=[1298,1322],held=50,expected_health=32)
    for i,yy in enumerate([1482,1642,1802,1962]):
        p.move_to(f'shaft_down_{i}','down',[1298,yy]);p.scenario['phases'][-1]['max_frames']=600
    # The GAME writes Y16 at source$9960 once Y >= (129-3)*16.
    # Ordinary down input reaches that code; this is not an injected teleport.
    p.action('bottom_camera_wrap',0x9966,control='port1 down',frames=600)
    p.scenario['phases'][-1]['capture']['memory_reads'].append(goal(PLAYER,bytes.fromhex('05120010')))
    p.action('top_world_main',0x5D6).move_to('before_icelord','down',[1298,144])
    p.action('return_inspection_stop',0x5D6)
    reads=p.scenario['phases'][-1]['capture']['memory_reads']
    reads[:]=[r for r in reads if r.get('address')!=0x3D16]
    reads += [goal(0x3D27,b'\x00'),goal(PLAYER+22,bytes([50])),{'address':0x59D7A+48,'size':36}]
    next(r for r in reads if r.get('address')==0x3B92).update(expect_hex='3000312624372123')
    s['phases']+=p.scenario['phases'][2:]
    for event in p.scenario['input_events']:
        if event['after_phase']=='anchor':event['after_phase']=previous
        s['input_events'].append(event)
    s['identifier']='pandora-unarmed-return-route-inspection';return s


def main():
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['prepare','inspect-return'],default='prepare')
    parser.add_argument('--cold',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.cold and args.stage=='inspect-return':
        parser.error('Return inspection starts from the verified AWOL checkpoint; cold preparation is a separate scenario.')
    scenario=prepare_departure(cold=args.cold) if args.stage=='prepare' else inspect_return()
    args.output.write_text(json.dumps(scenario,indent=2)+'\n')


if __name__=='__main__':main()
