"""Post-clear player-record seed path, not complete world initialization/lifetime."""
import pytest
from tests.test_starglider2_text_editor import original_image,memory,state,run,put,get,APP,STACK


@pytest.mark.parametrize('angles',[(0,0,0),(1,4095,2048),(65535,32768,32767),(0x1234,0xFEDC,0xA55A)])
@pytest.mark.parametrize('initial',[0,0xA5,255])
def test_original_player_seed_publishes_type30_then_stores_three_orientation_words(original_image,memory,angles,initial):
    m=memory;raw=original_image[0]
    pool=get(raw,0x17DF2-4096,2);obj=APP+pool
    assert pool==0x2330
    m[obj-2:obj+70]=bytes([initial])*72
    expected=bytearray(m[obj-2:obj+70]);expected[2:4]=(30).to_bytes(2,'big')
    expected[4]=initial|0x12;expected[30]=255
    for pc,offset,angle in zip([0x17E3E,0x17E44,0x17E4A],[16,18,20],angles):
        source=pc-4096
        assert raw[source:source+2]==bytes.fromhex('316e')and get(raw,source+4,2)==offset
        put(m,APP+get(raw,source+2,2),angle,2)
        expected[2+offset:4+offset]=angle.to_bytes(2,'big')
    before=bytearray(m[APP:APP+0x1000]);before[0x700:0x704]=obj.to_bytes(4,'big')
    cpu=state(m,0x17DF0);run(original_image,m,cpu,{0x17E50})
    assert bytes(m[obj-2:obj+70])==expected and bytes(m[APP:APP+0x1000])==before
    assert cpu.a[0]==obj and cpu.a[6]==APP and cpu.a[7]==STACK
    assert cpu.d[0]==30 and cpu.d[7]&65535==1
