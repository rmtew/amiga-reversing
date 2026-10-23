from collections import deque
import pytest
from amiga_reversing.tools.pandora_route_app_watch import APP_BASE,RouteAppWatch

class Client:
    def __init__(self):self.events=deque(maxlen=128);self.filters=[];self.calls=[]
    def request(self,method,params=None):
        self.calls.append((method,params))
        if method=='events.subscribe':self.filters=params['mmio'];return {'active':['mmio']}
        if method=='events.unsubscribe':self.filters=[];return {'active':[]}
        if method=='events.list':return {'active':['mmio'] if self.filters else [],'mmio':self.filters}
        raise AssertionError(method)
    def registers(self):return {'pc':0x16134,'a6':APP_BASE,'a7':0x1000}
    def read_memory(self,addr,size):return bytes(size)

def event(addr=APP_BASE+0x190,pc=0x16130,access='read',dropped=0,queue_dropped=0):
    return {'method':'event.mmio','params':{'addr':addr,'pc':pc,'size':2,'access':access,'position':{'frame':462},'dropped_notifications':dropped,'dropped_events':queue_dropped}}

def test_all_accesses_counted_but_only_unique_signatures_retained_without_running_guest():
    client=Client();original=client.events;watch=RouteAppWatch(((0x190,0x195),));watch.arm(client,{'frame':455});watch.phase='original_route_phase'
    for _ in range(1000):client.events.append(event())
    watch.boundary(client,{'name':'next_phase','stop_event':{'frame':464}});watch.close({'frame':14332})
    report=watch.report();assert report['events_received']==1000 and report['access_counts']=={'read':1000}
    assert len(report['signatures'])==1 and report['signatures'][0]['count']==1000 and report['capture_complete']
    assert report['signatures'][0]['later_boundary_context']['phase']=='next_phase'
    assert client.events is original and len(original)==128
    assert all(name.startswith('events.') for name,params in client.calls)

def test_server_loss_and_local_overflow_never_claim_complete_coverage():
    for lost,queue_lost,limit in [(1,0,2),(0,1,2),(0,0,1)]:
        client=Client();watch=RouteAppWatch(((0x190,0x195),),max_signatures=limit);watch.arm(client,{'frame':455})
        client.events.append(event(dropped=lost,queue_dropped=queue_lost));client.events.append(event(access='write',dropped=lost,queue_dropped=queue_lost));watch.close({'frame':800})
        assert not watch.report()['capture_complete']
        assert watch.report()['server_dropped_notifications']==lost
        assert watch.report()['server_dropped_mmio_events']==queue_lost
        assert watch.report()['local_signature_overflow']==(limit==1)

def test_quiet_windows_require_successful_route_completion():
    for end,want in [({'frame':14332},True),(None,False)]:
        client=Client();watch=RouteAppWatch(((0x190,0x195),));watch.arm(client,{'frame':455});watch.close(end)
        assert watch.report()['capture_complete']==want and not watch.report()['signatures']

def test_filter_readback_mismatch_refuses_and_unsubscribes():
    class Bad(Client):
        def request(self,method,params=None):
            if method=='events.list':return {'active':[],'mmio':[]}
            return super().request(method,params)
    client=Bad();original=client.events;watch=RouteAppWatch(((0x190,0x195),))
    with pytest.raises(RuntimeError,match='readback'):watch.arm(client,{'frame':455})
    assert not client.filters and client.events is original

@pytest.mark.parametrize('ranges',[(),((4,4),),((1,5),(4,8)),((False,3),)])
def test_invalid_or_overlapping_filters_refused(ranges):
    with pytest.raises(ValueError):RouteAppWatch(ranges)

def test_missing_mmio_queue_loss_counter_refused():
    client=Client();watch=RouteAppWatch(((0x190,0x195),));watch.arm(client,{'frame':455})
    message=event();del message['params']['dropped_events']
    with pytest.raises(RuntimeError,match='MMIO queue loss'):client.events.append(message)
    watch.close(None);assert not watch.report()['capture_complete']
