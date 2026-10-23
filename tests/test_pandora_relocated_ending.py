"""Receipt admission guards, not a substitute for the cold gameplay runs."""
import copy
import pytest
from amiga_reversing.tools.pandora_layout_runtime import ending_outcome

BASE=0x80000
IMAGE_SIZE=0x55370


def completed():
    def phase(offset, **extra):
        return dict(status='hit', pc=f'0x{BASE+offset:08x}', address=f'0x{BASE+offset:08x}', **extra)
    reads={0x3D27:'ff',0x3D38:'5c',BASE+0x4C35E:'0031',BASE+0x4CAE5:b'CONGRATU'.hex()}
    selected=phase(0x4C9DC,name='es_saved_earth_outcome_selected',capture=dict(
        registers={'a0':hex(BASE+0x4CAE5)},memory_reads=[dict(address=hex(a),bytes=b) for a,b in reads.items()]))
    return dict(phases=[phase(0x5D6) for _ in range(574)]+[selected,
        phase(0x4C99C,name='es_escape_commit_inhibited',stop_event={'frame':14278})],
        input_trace=[dict(outcome='acknowledged')])


def test_full_route_and_explicit_saved_earth_state_are_required():
    assert ending_outcome(completed(),BASE,IMAGE_SIZE)==dict(saved_earth=True,escaped=True,health=49,
        message_pointer=BASE+0x4CAE5,selection_pc=BASE+0x4C9DC,final_frame=14278)


@pytest.mark.parametrize('defect',['early','phase_failure','old_pc','wrong_selection','wrong_message',
                                   'uncommitted','uncertain_input','unarmed','wrong_flags','health','text','uncopied_tail'])
def test_incomplete_or_wrong_ending_never_qualifies(defect):
    report=copy.deepcopy(completed());selected=report['phases'][-2]
    if defect=='early':report['phases'].pop()
    elif defect=='phase_failure':report['phases'][80]['status']='not_hit'
    elif defect=='old_pc':report['phases'][80]['pc']='0x000105d6'
    elif defect=='uncopied_tail':report['phases'][80]['pc']=report['phases'][80]['address']=hex(BASE+0x56000)
    elif defect=='wrong_selection':selected['name']='different_outcome'
    elif defect=='wrong_message':selected['capture']['registers']['a0']='0x5cae5'
    elif defect=='uncommitted':report['phases'][-1]['name']='before_escape_commit'
    elif defect=='uncertain_input':report['input_trace'][0]['outcome']='uncertain'
    else:
        address={'unarmed':0x3D27,'wrong_flags':0x3D38,'health':BASE+0x4C35E,'text':BASE+0x4CAE5}[defect]
        next(r for r in selected['capture']['memory_reads'] if int(r['address'],0)==address)['bytes']='00'
    with pytest.raises(ValueError):ending_outcome(report,BASE,IMAGE_SIZE)
