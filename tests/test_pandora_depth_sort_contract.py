"""Original 32-entry depth sort within the 67-entry descriptor table.

Explicit valid RAM inputs and nonempty deferred groups; no universal lifetime or
ordinary target hit is inferred from these CPU sorting witnesses.
"""
from collections import Counter

from tests.test_pandora_state_transitions import BASE, cpu_fixture

TABLE, SORT, END = BASE+0x309A, BASE+0x310E, BASE+0x318E


def partition(fixture, flags, heights):
    cpu, memory, schemas, read, write, run = fixture
    pointers = [read(SORT+4*i) for i in range(32)]
    for pointer, flag, height in zip(pointers, flags, heights):
        write(read(pointer)+schemas['world_position_state_record']['world_object_flags'],flag,1)
        write(pointer+6,height,2)
    front=[p for p,f in zip(pointers,flags) if f&64]
    back=[p for p,f in zip(pointers,flags) if not f&64 and f&128]
    middle=[p for p,f in zip(pointers,flags) if not f&192]
    assert middle
    prefix,suffix=bytes(memory[TABLE:SORT]),bytes(memory[END:END+28])
    run(0x849A,budget=20000)
    actual=[read(SORT+4*i) for i in range(32)]
    assert Counter(actual)==Counter(pointers)
    assert actual[:len(front)]==front
    if back:assert actual[-len(back):]==back[::-1]
    selected=actual[len(front):32-len(back)]
    assert Counter(selected)==Counter(middle)
    assert [read(p+6,2) for p in selected]==sorted(read(p+6,2) for p in middle)
    assert bytes(memory[TABLE:SORT])==prefix and bytes(memory[END:END+28])==suffix
    return pointers,selected


def test_all_256_state_flag_bytes_use_only_front_and_back_bits(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    original=bytes(memory[SORT:END])
    for start in range(0,256,31):
        memory[SORT:END]=original
        flags=list(range(start,min(start+31,256)))
        flags += [0]*(32-len(flags))  # A deferred entry is always present.
        partition(cpu_fixture,flags,[(i*1973)&65535 for i in range(32)])


def test_every_nonempty_middle_size_preserves_fixed_prefix_tail_and_sentinel(cpu_fixture):
    cpu,memory,schemas,read,write,run=cpu_fixture
    assert SORT-TABLE==29*4 and END-SORT==32*4 and read(END+6*4)==0
    original=bytes(memory[SORT:END])
    for count in range(1,33):
        memory[SORT:END]=original
        flags=[0]*count+[64 if i&1 else 128 for i in range(32-count)]
        # Unsigned extremes, duplicate keys, and descending spans.
        partition(cpu_fixture,flags,[65535,32768,0,7,7,3,2,1]*4)


def test_equal_y_descriptors_can_reverse_across_gap_passes(cpu_fixture):
    pointers,selected=partition(cpu_fixture,[0]*4+[64]*28,[1,1,0,0]+[0]*28)
    assert selected==[pointers[3],pointers[2],pointers[1],pointers[0]]
