from types import SimpleNamespace
import pytest
from amiga_reversing.disasm import c_backend
from amiga_reversing.tools.runtime_analysis import analysis_scope, build_project_listing_artifact_profile


def test_runtime_scope_borrows_one_snapshot_and_closes_it_after_last_use(monkeypatch):
    built=[];closed=[]
    def build(target):
        built.append(target)
        return 0,{},SimpleNamespace(value=target,close=lambda:closed.append(target))
    monkeypatch.setattr(c_backend,'build_project_listing_artifact_profile',build)
    with analysis_scope():
        a=build_project_listing_artifact_profile('one')[2]
        a.close()
        b=build_project_listing_artifact_profile('one')[2]
        assert b.value=='one' and not closed and built==['one']
    assert closed==['one']
    with analysis_scope():build_project_listing_artifact_profile('one')[2].close()
    assert built==['one','one'] and closed==['one','one']


def test_scope_closes_on_failure_and_does_not_leak_into_unscoped_calls(monkeypatch):
    closed=[]
    monkeypatch.setattr(c_backend,'build_project_listing_artifact_profile',lambda target:(0,{},SimpleNamespace(close=lambda:closed.append(target))))
    with pytest.raises(RuntimeError):
        with analysis_scope():
            build_project_listing_artifact_profile('failed')
            raise RuntimeError('probe failed')
    assert closed==['failed']
    outside=build_project_listing_artifact_profile('outside')[2]
    assert closed==['failed']
    outside.close();assert closed==['failed','outside']
