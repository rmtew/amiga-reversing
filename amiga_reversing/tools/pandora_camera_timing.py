"""Small Pandora camera model for bounded patrol-crossing call windows.

Rules are decoded target logic, not a frame-rate assumption. Profiles must remain
fixed and the route must avoid world wrapping, modal tiles and other encounters.
"""
from dataclasses import dataclass, replace


@dataclass
class Camera:
    x: int
    y: int
    active: bool
    remaining: int
    dx: int
    dy: int
    reload: int
    margin_x: int
    margin_y: int
    player_delay: int
    script_delay: int


def decode(phase, *, profiles):
    capture=phase['capture'];a6=int(capture['registers']['a6'],0);memory={}
    for r in capture['memory_reads']:
        address=int(r['address'],0)
        for i,v in enumerate(bytes.fromhex(r['bytes'])):memory[address+i]=v
    def val(address,size,signed=False):
        try:return int.from_bytes(bytes(memory[address+i] for i in range(size)),'big',signed=signed)
        except KeyError as e:raise ValueError('camera capture missing required bytes') from e
    index=val(a6+0x2ca,2)
    if index not in profiles:raise ValueError('unknown camera profile')
    reload,mx,my=profiles[index]
    if val(a6+0x2c8,2)!=reload:raise ValueError('live camera reload differs from profile')
    return Camera(val(a6+0x1b6,2),val(a6+0x1b8,2),bool(val(a6+0x27b,1)&16),
                  val(a6+0x289,1),val(a6+0x296,2,True),val(a6+0x298,2,True),reload,mx,my,
                  val(0x5c366,2),val(0x5c31a,2))


def idle_tick(camera):
    """One neutral gameplay loop: camera service precedes player dispatch."""
    c=replace(camera);c.remaining=(c.remaining-1)&255
    if not c.remaining:c.active=False;c.dx=c.dy=0
    else:c.x+=c.dx;c.y=max(0,min(1936,c.y+c.dy))
    if c.player_delay:c.player_delay-=1
    if not c.player_delay:
        if not c.active:c.script_delay=1  # hold movement resets the mutable delay
        c.player_delay=c.script_delay
    return c


def call_windows(camera,path,*,initial_input_lag=1):
    """Conservative cumulative bound; camera pauses are charged per burst.

    X requests set script delay2; Y requests set delay1 (source9680 /96AA).
    A full interior burst moves16*(reload-1) pixels, then expires. It is charged
    once, rather than assuming the maximum pause after every accepted move.
    """
    c=replace(camera)
    if c.reload not in (4,6) or c.player_delay not in (0,1,2):raise ValueError('unadmitted camera/delay state')
    upper=max(1,c.player_delay)+initial_input_lag
    if c.active:
        if not 1<=c.remaining<=c.reload:raise ValueError('invalid active countdown')
        upper+=c.remaining;c.x+=c.dx*(c.remaining-1);c.y=max(0,min(1936,c.y+c.dy*(c.remaining-1)))
        c.active=False;c.dx=c.dy=0
    windows=[];bursts=[]
    for i,(direction,pose) in enumerate(path):
        x,y=pose[:2];sx=sy=0
        if not 16<=y<2016:raise ValueError('world wrapping/outcome region outside timing model')
        if direction=='left' and x<c.x+c.margin_x:
            if c.x<80:raise ValueError('left map-edge scroll outside model')
            sx=-16
        elif direction=='right' and x+24>=c.x+320-c.margin_x:
            if c.x+368>=1440:raise ValueError('right map-edge scroll outside model')
            sx=16
        elif direction=='up' and y<c.y+c.margin_y:sy=-16
        elif direction=='down' and y+32>=c.y+128-c.margin_y:sy=16
        delay=2 if direction in ('left','right') else 1
        next_upper=upper+delay
        if sx or sy:
            next_upper+=c.reload-1
            c.x+=sx*(c.reload-1);c.y=max(0,min(1936,c.y+sy*(c.reload-1)))
            bursts.append({'after_move':i+1,'delta':[sx,sy],'scroll_after':[c.x,c.y],'max_extra_calls':c.reload-1})
        windows.append([i,next_upper]);upper=next_upper
    return {'windows':windows,'bursts':bursts,'max_calls_through_final_wait':upper,
            'conditions':['Fixed captured profile, axis-only accepted requests and interior camera rules.',
                          'Collisions, new encounters, modal control and external script changes must stop runtime qualification.']}
