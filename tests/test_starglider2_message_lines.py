"""Original queue/message CPU paths; no IRQ timing or hardware scanout proof.

Run through the real frame-producing wrappers. Explicit queue/count and key
stimuli are fixture inputs, not evidence that invalid states occur in gameplay.
"""
import pytest

from tests.test_starglider2_text_editor import (
    original_image, memory, state, run, put, get,
    APP, FB, INPUT, STACK, RETURN, FONT, COL, ROW, DEST, COLOUR, INVERSE,
)

QUEUE,COUNT,TIMER,LINE,BLANK = 0xE084,APP+0x7AE,APP+0x7B4,0x71D8E,0xE0B8


def draw_expected(memory,text):
    expected=bytearray(memory[FB:FB+0x8000]);font=bytes(memory[FONT:FONT+760])
    for plane in [0x4000,0x6000]:
        for row in range(8):
            start=LINE-FB+plane+40*row
            expected[start:start+28]=bytes(28)
    for column,character in enumerate(text):
        glyph=font[8*(character-32):8*(character-31)]
        assert len(glyph)==8
        for row,value in enumerate(glyph):
            for plane in [0x4000,0x6000]:expected[LINE-FB+plane+40*row+column]=value
    return expected


@pytest.mark.parametrize('length',[0,1,28,29])
def test_timed_message_uses_real_frame_and_does_not_clip_to_clear_width(original_image,memory,length):
    text=b'A'*length;memory[INPUT:INPUT+length+1]=text+b'\0'
    memory[COLOUR],memory[INVERSE]=0,255  # this renderer ignores these cursor controls
    put(memory,TIMER,9,2);put(memory,COUNT,3,2)
    cpu=state(memory,0xDAF4);cpu.a[1]=INPUT
    old_d,old_a=list(cpu.d),list(cpu.a);font=bytes(memory[FONT:FONT+760])
    expected=draw_expected(memory,text);old_cursor=(get(memory,DEST),memory[COL],memory[ROW])
    run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[FB:FB+0x8000])==expected and bytes(memory[FONT:FONT+760])==font
    assert get(memory,TIMER,2)==75 and get(memory,COUNT,2)==3
    assert list(cpu.d)==old_d and list(cpu.a)[:7]==old_a[:7] and cpu.a[7]==STACK+4
    assert (get(memory,DEST),memory[COL],memory[ROW])==old_cursor
    assert (memory[COLOUR],memory[INVERSE])==(0,255)


@pytest.mark.parametrize('count',range(10))
@pytest.mark.parametrize('same_predecessor',[False,True])
def test_enqueue_compares_only_preceding_pointer_and_appends_empty_first_item(original_image,memory,count,same_predecessor):
    values=[0x50000+4*i for i in range(12)]
    for i,value in enumerate(values):put(memory,QUEUE-4+4*i,value)
    candidate=get(memory,QUEUE+4*(count-1))if same_predecessor else INPUT
    put(memory,COUNT,count,2);put(memory,TIMER,33,2)
    before=bytes(memory[QUEUE-4:QUEUE+44]);expected=bytearray(before)
    cpu=state(memory,0xDAB2);cpu.a[1]=candidate;old_d0,old_a0=cpu.d[0],cpu.a[0]
    run(original_image,memory,cpu,{RETURN})
    if same_predecessor:out_count,out_timer=count,33
    else:
        position=4+4*count;expected[position:position+4]=candidate.to_bytes(4,'big')
        out_count,out_timer=count+1,33
        if count==0:
            expected[position+4:position+8]=BLANK.to_bytes(4,'big');out_count,out_timer=2,0
    assert bytes(memory[QUEUE-4:QUEUE+44])==expected
    assert (get(memory,COUNT,2),get(memory,TIMER,2))==(out_count,out_timer)
    assert cpu.d[0]==old_d0 and cpu.a[0]==old_a0 and cpu.a[7]==STACK+4


@pytest.mark.parametrize('count',[10,11,32767])
def test_enqueue_signed_capacity_rejection_keeps_queue_and_timer(original_image,memory,count):
    put(memory,COUNT,count,2);put(memory,TIMER,33,2)
    before=bytes(memory[QUEUE-8:QUEUE+48]);cpu=state(memory,0xDAB2);cpu.a[1]=INPUT
    run(original_image,memory,cpu,{RETURN})
    assert bytes(memory[QUEUE-8:QUEUE+48])==before
    assert (get(memory,COUNT,2),get(memory,TIMER,2))==(count,33)


def test_negative_enqueue_count_retains_original_prefix_store(original_image,memory):
    put(memory,COUNT,0xFFFF,2);put(memory,TIMER,33,2);put(memory,QUEUE-8,INPUT+4)
    cpu=state(memory,0xDAB2);cpu.a[1]=INPUT
    run(original_image,memory,cpu,{RETURN})
    assert get(memory,QUEUE-4)==INPUT and get(memory,COUNT,2)==0 and get(memory,TIMER,2)==33
    # Supplied negative count, not a reachable-game corruption claim.


@pytest.mark.parametrize('count',range(1,11))
def test_advance_draws_head_and_shifts_count_longs_including_inactive_tail(original_image,memory,count):
    values=[INPUT]+[0x50000+4*i for i in range(1,11)]
    values[10]=0xCAFE1234  # trailing backing LONG, not an admitted pointer or eleventh slot
    for i,value in enumerate(values):put(memory,QUEUE+4*i,value)
    memory[INPUT:INPUT+2]=b'A\0';put(memory,COUNT,count,2);put(memory,TIMER,1,2)
    expected=draw_expected(memory,b'A');cpu=state(memory,0xDB02);old_d,old_a=list(cpu.d),list(cpu.a)
    run(original_image,memory,cpu,{RETURN})
    assert [get(memory,QUEUE+4*i)for i in range(count)]==values[1:count+1]
    assert [get(memory,QUEUE+4*i)for i in range(count,11)]==values[count:]
    assert (get(memory,COUNT,2),get(memory,TIMER,2))==(count-1,75)
    assert bytes(memory[FB:FB+0x8000])==expected
    assert list(cpu.d)==old_d and list(cpu.a)[:7]==old_a[:7] and cpu.a[7]==STACK+4


def test_zero_count_advance_sets_underflow_counter_without_a_guard(original_image,memory):
    put(memory,COUNT,0,2);put(memory,QUEUE,INPUT);cpu=state(memory,0xDB02)
    run(original_image,memory,cpu,{0xDB1E})
    assert cpu.d[0]&0xFFFF==0xFFFF and get(memory,TIMER,2)==75
    assert get(memory,COUNT,2)==0  # stop before the 65536-copy loop and its later decrement


@pytest.mark.parametrize('timer,count,draw',[(0,0,False),(0,1,True),(1,1,True),(2,1,False),(0,0xFFFF,False),(0xFFFF,1,False)])
def test_amiga_message_service_gate_keeps_signed_queue_and_countdown_rules(original_image,memory,timer,count,draw):
    put(memory,TIMER,timer,2);put(memory,COUNT,count,2);put(memory,QUEUE,INPUT);put(memory,QUEUE+4,0)
    memory[INPUT:INPUT+2]=b'A\0';cpu=state(memory,0xC758)
    before=bytes(memory[FB:FB+0x8000]);expected=draw_expected(memory,b'A')if draw else before
    run(original_image,memory,cpu,{0xC770})
    assert bytes(memory[FB:FB+0x8000])==expected
    assert get(memory,TIMER,2)==(75 if draw else ((timer-1)&0xFFFF if timer else 0))
    assert get(memory,COUNT,2)==(count-1 if draw else count)


@pytest.mark.parametrize('keys,result,text',[
    ([0x0A,0x1C],0,b'0'), ([7,0x1C],7,b'7'),
    ([9,9,0x1C],99,b'99'), ([1,0x0A,0x0A,0x1C],100,b'100'),
    ([2,5,6,0x1C],0,b'256'), ([2,5,9,0x1C],3,b'259'),
    ([1,2,0x41,3,0x1C],13,b'13'), ([2,5,9,0x41,0x1C],0x30000,b'25'),
    ([1,2,0x45],0xFFFFFFFF,b'12'), ([0x41,0x1C],0,b''),
])
def test_viewer_keyline_retains_byte_add_carry_loss_and_word_delete_result(original_image,memory,keys,result,text):
    cpu=state(memory,0xF218);cpu.a[1]=0xFD22
    prompt=bytes(memory[0xFD22:0xFD22+19]);assert prompt==b'Enter shape number:'
    expected=draw_expected(memory,b'');events=[];pending=iter(keys)
    def key(pc):
        if pc==0xD7AA:
            value=next(pending,None);assert value is not None
            memory[APP+0x203]=value;events.append(value)
    run(original_image,memory,cpu,{RETURN},key)
    assert events==keys and list(pending)==[] and cpu.a[7]==STACK+4
    assert cpu.d[4]==result
    assert get(memory,0xFD08)==0xFD18+len(text) and get(memory,0xFD0C)==0xFD22
    assert bytes(memory[0xFD18:0xFD18+len(text)+1])==text+b'\0'
    assert bytes(memory[0xFD20:0xFD22])==b'\0\0'  # beyond the eight-byte initialization clear
    assert bytes(memory[FB:FB+0x8000])==expected and get(memory,TIMER,2)==75
    if text:assert bytes(memory[0xFD4D:0xFD4D+20+len(text)])==prompt+text+b'\0'


@pytest.mark.parametrize('timer,count,called',[(0,0,False),(0,1,True),(0,0xFFFF,True),(1,1,False)])
def test_alternate_queue_poll_retains_distinct_negative_count_gate(original_image,memory,timer,count,called):
    put(memory,TIMER,timer,2);put(memory,COUNT,count,2);cpu=state(memory,0x3ACFC)
    run(original_image,memory,cpu,{0x3B0CE,0x3AD0C})
    assert cpu.pc==(0x3B0CE if called else 0x3AD0C)
    assert get(memory,TIMER,2)==timer and get(memory,COUNT,2)==count
    # Stop at the real call bridge; negative-count dequeue safety is not asserted.


@pytest.mark.parametrize('timer',[0,1,2,0xFFFF])
def test_alternate_countdown_tick_does_not_itself_dispatch_queue(original_image,memory,timer):
    put(memory,TIMER,timer,2);put(memory,COUNT,2,2);cpu=state(memory,0x3B1C8)
    run(original_image,memory,cpu,{0x3B1D2})
    assert get(memory,TIMER,2)==((timer-1)&0xFFFF if timer else 0)
    assert get(memory,COUNT,2)==2


def test_nonadjacent_duplicate_pointer_is_not_filtered(original_image,memory):
    put(memory,COUNT,3,2)
    for i,value in enumerate([INPUT,INPUT+4,INPUT+8]):put(memory,QUEUE+4*i,value)
    cpu=state(memory,0xDAB2);cpu.a[1]=INPUT
    run(original_image,memory,cpu,{RETURN})
    assert get(memory,COUNT,2)==4 and get(memory,QUEUE+12)==INPUT


def test_first_enqueued_message_is_followed_by_real_empty_message_after_75_service_steps(original_image,memory):
    memory[INPUT:INPUT+2]=b'A\0';put(memory,COUNT,0,2);put(memory,TIMER,33,2)
    cpu=state(memory,0xDAB2);cpu.a[1]=INPUT
    run(original_image,memory,cpu,{RETURN})
    assert (get(memory,COUNT,2),get(memory,TIMER,2))==(2,0)
    expected_a=draw_expected(memory,b'A')
    cpu=state(memory,0xC758);run(original_image,memory,cpu,{0xC770})
    assert bytes(memory[FB:FB+0x8000])==expected_a
    assert (get(memory,COUNT,2),get(memory,TIMER,2),get(memory,QUEUE))==(1,75,BLANK)
    for remaining in range(74,0,-1):
        cpu=state(memory,0xC758);run(original_image,memory,cpu,{0xC770})
        assert (get(memory,COUNT,2),get(memory,TIMER,2))==(1,remaining)
    expected_empty=draw_expected(memory,b'')
    cpu=state(memory,0xC758);run(original_image,memory,cpu,{0xC770})
    assert bytes(memory[FB:FB+0x8000])==expected_empty
    assert (get(memory,COUNT,2),get(memory,TIMER,2))==(0,75)
    # These are explicit CPU service invocations, not measured VBlank/wall-clock time.
