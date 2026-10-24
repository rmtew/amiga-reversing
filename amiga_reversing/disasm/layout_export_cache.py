"""Disposable native export-plan ownership; no placements or target facts live here.

One baseline per target is owned by the existing projection service. Native code
decides whether a layout can reuse it. Image/bootstrap changes rebuild; invalid
placements refuse. Semantic input changes evict before use.
"""
from __future__ import annotations

import atexit
import hashlib
import json
from contextlib import contextmanager, closing

from . import c_backend, effective_metadata, source_rendering, source_package
from .behaviour_validation import LoadedSource, BehaviourError
from .binary_source import read_binary_source_bytes
from .facts_v2_source_refusal import facts_v2_source_refused
from .listing_projection import ListingProjectionService
from .target_history import target_lock

LOADED_SOURCE=LoadedSource(__file__)
_CACHE=ListingProjectionService()
atexit.register(_CACHE.reset)


class LayoutExportRefused(ValueError):
    def __init__(self,reason,message,*,restart_required=False):
        self.payload=dict(status='refused',reason=reason,message=message,restart_required=restart_required)
        super().__init__(message)


def implementation_identities(owner):
    return {name:source.require_current() for name,source in (
        ('layout_export_cache',LOADED_SOURCE),('source_export',owner),
        ('c_backend',c_backend.LOADED_SOURCE),('effective_metadata',effective_metadata.LOADED_SOURCE),
        ('source_rendering',source_rendering.LOADED_SOURCE),('source_package',source_package.LOADED_SOURCE))}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class _Owner:
    def __init__(self,artifact,profile,layout_identity=None):
        self.artifact,self.profile,self.layout_identity=artifact,profile,layout_identity
    def close(self):self.artifact.close()


class _Projection:
    def __init__(self,payload,owner,identities,backend,*,native_matches=False):
        self.payload=payload
        self._native=owner.artifact if native_matches else None
        self.profile=dict(backend=owner.profile.get('backend'),facts_v2={'asm_source_refused':False},
            layout_projection=payload['projection'],baseline_analysis_profile=owner.profile,
            implementation_identities=identities,loaded_backend_identity=backend)
    def source_projection_with_profile(self,*,use_persisted_policy=False):
        return self.payload['canonical_source_text'],self.profile,None
    def inline_source_text_with_profile(self):return self.payload['canonical_source_text'],self.profile
    def source_package_payload(self,minimum_asset_size):return dict(self.payload['package'])
    def memory_layouts_payload(self):return self.payload['memory_layouts']
    def _matching_native(self):
        if self._native is None:
            raise LayoutExportRefused('allocation_planning_requires_matching_baseline',
                'Projected layouts cannot borrow allocation plans from a different native baseline')
        self._native.loaded_backend_identity()
        return self._native
    def loaded_backend_identity(self):return self._matching_native().loaded_backend_identity()
    def runtime_allocation_plan(self,*args):return self._matching_native().runtime_allocation_plan(*args)
    def runtime_allocation_batch_plan(self,*args):return self._matching_native().runtime_allocation_batch_plan(*args)



@contextmanager
def acquire(paths,project_root,metadata_path,builder,owner_source,minimum_asset_size,*,require_native_baseline=False):
    """Lease one artifact/projection through rendering and package emission."""
    project=str(paths.target_dir.resolve())
    try:
        with target_lock(paths.target_dir):
            identities=implementation_identities(owner_source)
            metadata=json.loads(metadata_path.read_text())
            full=dict(metadata);full.pop('selected_memory_layout_id',None)
            full_hash=hashlib.sha256((json.dumps(full,sort_keys=True,indent=2)+'\n').encode()).hexdigest()
            if effective_metadata.effective_metadata_hash(paths.target_dir)!=full_hash:
                raise LayoutExportRefused('stale','Canonical metadata changed before export')
            input_hash=hashlib.sha256(read_binary_source_bytes(paths.binary_source)).hexdigest()
            layout_identity=digest(dict(memory_layouts=metadata['memory_layouts'],selected_memory_layout_id=metadata['selected_memory_layout_id']))
            core=dict(full);core.pop('memory_layouts',None)
            backend=c_backend.native_backend_identity(project_root)
            key=digest(dict(core_metadata=core,input=input_hash,source=repr(paths.binary_source),
                            implementation=identities,backend=backend))
            owner=_CACHE.valid_artifact(project,key)
            projected=None
            if owner is not None:
                owner.artifact.loaded_backend_identity()
                payload=owner.artifact.layout_projection_payload(dict(memory_layouts=metadata['memory_layouts'],
                    selected_memory_layout_id=metadata['selected_memory_layout_id']),minimum_asset_size)
                if payload['status']=='refused':
                    raise LayoutExportRefused(payload['reason'],'Native layout projection refused: '+payload['reason'])
                if payload['status']=='rebuild_required' or (require_native_baseline and getattr(owner,'layout_identity',None)!=layout_identity):
                    _CACHE.clear_project(project);owner=None
                else:projected=_Projection(payload,owner,identities,backend,native_matches=getattr(owner,'layout_identity',None)==layout_identity)
            if owner is None:
                artifact=builder()
                try:
                    _,profile=artifact.inline_source_text_with_profile()
                    if artifact.loaded_backend_identity()!=backend:
                        raise LayoutExportRefused('stale','Native backend changed during analysis',restart_required=True)
                    owner=_Owner(artifact,profile,layout_identity)
                    if facts_v2_source_refused(profile):
                        with closing(artifact):yield artifact
                        return
                    _CACHE.set_artifact(project_id=project,cache_key=key,artifact=owner)
                except BaseException:
                    artifact.close();raise
            try:
                yield projected if projected is not None else owner.artifact
                if (effective_metadata.effective_metadata_hash(paths.target_dir)!=full_hash or
                        hashlib.sha256(read_binary_source_bytes(paths.binary_source)).hexdigest()!=input_hash):
                    raise LayoutExportRefused('stale','Export input or canonical metadata changed during export')
                implementation_identities(owner_source)
                if c_backend.native_backend_identity(project_root)!=backend:
                    raise LayoutExportRefused('stale','Native backend identity changed',restart_required=True)
            except BaseException:
                _CACHE.clear_project(project);raise
    except (c_backend.NativeBackendStale,BehaviourError) as exc:
        _CACHE.clear_project(project)
        raise LayoutExportRefused('stale',str(exc),restart_required=True) from exc
