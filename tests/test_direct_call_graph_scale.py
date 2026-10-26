"""Direct-call admission is input-sized; SCCs stay terminal, not optimistic."""
import pytest
from tests.test_app_cursor_propagation import cursor_artifact

@pytest.mark.parametrize('count,cycle',[(140,False),(300,True)])
def test_deep_direct_graph_and_large_recursive_component(tmp_path,count,cycle):
    body='bsr.w helper_0\n rts\n'
    for i in range(count):
        body+=f'helper_{i}:\n'
        if i+1<count:body+=f' bsr.w helper_{i+1}\n'
        elif cycle:body+=' bsr.w helper_0\n'
        body+=' rts\n'
    a,_=cursor_artifact(tmp_path,body,regions=False)
    try:
        s=a.analysis_payload()[0]['sections'][0]
        summaries=s['function_summaries']
        assert len(summaries)==count
        assert not any(u['terminal_reason']=='direct_graph_capacity'for u in s['function_summary_uses'])
        if cycle:
            assert all(x['terminal_reason']=='recursive_direct_graph'for x in summaries)
            assert {x['direct_scc']['size']for x in summaries}=={count}
            assert {x['direct_scc']['ordinal']for x in summaries}==set(range(count))
        else:
            assert all(x['terminal_reason']=='none'for x in summaries)
            assert all(x['direct_scc']['size']==1 for x in summaries)
            assert all(x['effects']['registers']['state']=='explicit'for x in summaries)
        assert not a.analysis_payload()[0]['incomplete_analysis']
    finally:a.close()


def test_existing_native_direct_summary_refusals_and_recursion(tmp_path):
    import os,shutil,subprocess
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    compiler=shutil.which('cc');backend=Path(os.environ.get('AMIGA_TEST_BACKEND',root/'src/build/libamiga_backend.so'))
    if compiler is None or not backend.exists():pytest.skip('host compiler and native backend required')
    names=['direct_summary_large_body_is_solved','direct_summary_unknown_nested_call_is_terminal',
        'direct_summary_deep_chain_is_topologically_solved','direct_summary_graph_admits_all_reachable_targets',
        'self_recursive_direct_summary_is_conservative','mutually_recursive_direct_summaries_are_conservative',
        'recursive_scc_with_unknown_callee_is_terminal']
    source=tmp_path/'direct-summary.c';source.write_text('#include "test_m68k_ir.c"\nint main(void) {\n'+
        ''.join(f' if(test_facts_v2_{n}())return {i+1};\n'for i,n in enumerate(names))+'return 0; }\n')
    executable=tmp_path/'direct-summary'
    built=subprocess.run([compiler,'-Isrc','-D_POSIX_C_SOURCE=200809L','-std=c11','-O0',str(source),
        'src/m68k_c_unit_test.c',str(backend),f'-Wl,-rpath,{backend.parent}','-o',str(executable)],
        cwd=root,capture_output=True,text=True,timeout=60)
    assert built.returncode==0,built.stderr
    result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
