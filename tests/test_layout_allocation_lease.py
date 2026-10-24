"""Only an identical native baseline may serve allocation plans during export."""
from types import SimpleNamespace
import pytest
from amiga_reversing.disasm.layout_export_cache import _Projection,LayoutExportRefused


class Native:
    calls=0
    def loaded_backend_identity(self):return {'backend':'executed'}
    def runtime_allocation_plan(self,*args):self.calls+=1;return ('single',args)
    def runtime_allocation_batch_plan(self,*args):self.calls+=1;return ('batch',args)


@pytest.mark.parametrize('matches',[True,False])
def test_projection_does_not_delegate_other_layout_placements(matches):
    native=Native();owner=SimpleNamespace(artifact=native,profile={})
    p=_Projection({'projection':{},'canonical_source_text':'','memory_layouts':{}},owner,{}, {},native_matches=matches)
    if matches:
        assert p.runtime_allocation_plan('owner','profile')==('single',('owner','profile'))
        assert p.runtime_allocation_batch_plan('profile',{})==('batch',('profile',{}))
        assert native.calls==2
    else:
        for action in (lambda:p.runtime_allocation_plan('owner','profile'),lambda:p.runtime_allocation_batch_plan('profile',{})):
            with pytest.raises(LayoutExportRefused,match='different native baseline'):action()
        assert native.calls==0


def test_stale_native_backend_is_not_a_cached_allocation_pass():
    native=Native()
    def stale():raise RuntimeError('backend replaced')
    native.loaded_backend_identity=stale
    p=_Projection({'projection':{}},SimpleNamespace(artifact=native,profile={}),{}, {},native_matches=True)
    with pytest.raises(RuntimeError,match='backend replaced'):p.runtime_allocation_plan('owner','profile')
    assert native.calls==0
