"""Bounded CPU data-access stream over Pandora app declaration gaps.

Uses Copperline events.subscribe/mmio, rather than stopping or stepping the
successful route. Counts all received accesses; keeps at most256 distinct
PC/address/width/direction signatures. Server loss or local signature overflow
makes coverage incomplete. Phase-boundary registers are NOT access-time regs.
"""
from __future__ import annotations
from collections import Counter

APP_BASE = 0x39FC
GAPS = ((0x190,0x195),(0x1A6,0x1AA),(0x1AE,0x1B2),(0x1B4,0x1B6),
        (0x1CE,0x1D4),(0x1F8,0x20A),(0x21C,0x222),(0x223,0x224),
        (0x28A,0x28E),(0x2BE,0x2C2),(0x2C3,0x2C8),(0x33F,0x356),
        (0x35C,0x360),(0x36C,0x604))
SLOTS = ((0x2D4,0x2D8),(0x368,0x36C))


class RouteAppWatch:
    def __init__(self,ranges=GAPS+SLOTS,*,max_signatures=256):
        if not ranges or len(ranges)>16:raise ValueError('Require1..16 bounded ranges')
        if any(type(a) is not int or type(b) is not int or not 0<=a<b<=0x800 for a,b in ranges):raise ValueError('Invalid app range')
        if any(a<d and c<b for i,(a,b) in enumerate(ranges) for c,d in ranges[i+1:]):raise ValueError('Overlapping app ranges')
        if type(max_signatures) is not int or not 1<=max_signatures<=256:raise ValueError('Invalid signature bound')
        self.ranges=tuple(ranges);self.max_signatures=max_signatures;self.counts=Counter();self.records={}
        self.phase=None;self.client=None;self.start=None;self.end=None;self.dropped=0;self.queue_dropped=0;self.overflow=False;self.notifications=0
        self.original_queue=None;self.registration=None;self.readback=None;self.pending=set()

    def arm(self,client,start):
        if self.client is not None:raise RuntimeError('Already armed')
        owner=self;self.client=client;self.start=dict(start);self.original_queue=client.events
        class Sink:
            def append(self,message):
                owner.consume(message);owner.original_queue.append(message)
            def __iter__(self):return iter(owner.original_queue)
        client.events=Sink()
        filters=[{'addr':APP_BASE+a,'len':b-a,'access':'access'} for a,b in self.ranges]
        try:
            self.registration=client.request('events.subscribe',{'events':['mmio'],'mmio':filters})
            self.readback=client.request('events.list')
            actual=self.readback.get('mmio',[])
            def normalize(row):
                addr=row['addr'];return (int(addr,0) if isinstance(addr,str) else addr,row['len'],row.get('access','access'))
            if 'mmio' not in self.readback.get('active',[]) or sorted(map(normalize,actual))!=sorted(map(normalize,filters)):
                raise RuntimeError('Subscription filter readback mismatch')
        except BaseException:
            self.close(None);raise

    def consume(self,message):
        if message.get('method')!='event.mmio':return
        data=message.get('params',{});self.notifications+=1
        dropped=data.get('dropped_notifications')
        if type(dropped) is not int or dropped<0:raise RuntimeError('Missing subscription loss accounting')
        queue_dropped=data.get('dropped_events')
        if type(queue_dropped) is not int or queue_dropped<0:raise RuntimeError('Missing MMIO queue loss accounting')
        self.dropped=max(self.dropped,dropped);self.queue_dropped=max(self.queue_dropped,queue_dropped)
        addr,pc,size,access=(data.get(k) for k in ('addr','pc','size','access'))
        if type(addr) is not int or type(pc) is not int or type(size) is not int or not 1<=size<=4 or access not in ('read','write'):
            raise RuntimeError('Unsupported CPU data-access event')
        if not any(APP_BASE+a<=addr<APP_BASE+b for a,b in self.ranges):raise RuntimeError('Out-of-range stream access')
        if not isinstance(data.get('position'),dict) or type(data['position'].get('frame')) is not int:raise RuntimeError('Missing access position')
        key=(pc,addr,size,access);self.counts[access]+=1
        if key not in self.records:
            if len(self.records)>=self.max_signatures:self.overflow=True;return
            self.records[key]={'pc':pc,'address':addr,'app_offset':addr-APP_BASE,'width':size,'access':access,
                               'count':0,'first_value':data.get('value'),'first_position':data['position'],'first_phase':self.phase}
            self.pending.add(key)
        row=self.records[key];row['count']+=1;row['last_value']=data.get('value');row['last_position']=data['position'];row['last_phase']=self.phase

    def boundary(self,client,result):
        if not self.pending:return
        regs=client.registers();context={'phase':result['name'],'stop_event':result.get('stop_event'),
            'registers_at_later_boundary':regs,'stack_at_later_boundary_hex':client.read_memory(regs['a7'],32).hex()}
        for key in self.pending:self.records[key]['later_boundary_context']=context
        self.pending.clear()

    def close(self,end):
        if self.client is None:return
        try:
            self.client.request('events.unsubscribe',{'events':['mmio']})
            self.final_state=self.client.request('events.list')
            if 'mmio' in self.final_state.get('active',[]):raise RuntimeError('Subscription cleanup failed')
            self.end=end
        finally:self.client.events=self.original_queue

    def report(self):
        return {'schema_version':1,'app_base':APP_BASE,'engine':'cpu','ranges':[{'start':a,'end':b} for a,b in self.ranges],
            'start':self.start,'end':self.end,'registration':self.registration,'readback':self.readback,
            'events_received':self.notifications,'access_counts':dict(self.counts),'server_dropped_notifications':self.dropped,
            'server_dropped_mmio_events':self.queue_dropped,'local_signature_overflow':self.overflow,'capture_complete':bool(self.end) and not self.dropped and not self.queue_dropped and not self.overflow,
            'signatures':list(self.records.values()),'limits':[
            'CPU data access only; instruction fetch and DMA are excluded.',
            'Starting-address filters do not close cross-boundary accesses beginning outside ranges.',
            'Registers and stack are from the next canonical phase boundary, not the access instant.',
            'No-hit is not unused-memory proof. Server loss or signature overflow makes coverage incomplete.']}
