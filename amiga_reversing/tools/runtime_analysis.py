"""One immutable canonical analysis snapshot per public runtime CLI invocation.

All callers retain their existing close discipline. Within the scope they
borrow the same read-only artifact; the owner closes it on exit, including
exceptions. Payload/manifest validation remains independent at every boundary.
"""
from contextlib import contextmanager
from contextvars import ContextVar

_current = ContextVar('runtime_analysis_snapshot', default=None)


class _BorrowedArtifact:
    def __init__(self, artifact):
        self._artifact = artifact

    def __getattr__(self, name):
        return getattr(self._artifact, name)

    def close(self):
        pass  # The scope owns this artifact.


@contextmanager
def analysis_scope():
    cache = {}
    token = _current.set(cache)
    try:
        yield
    finally:
        _current.reset(token)
        for profile in cache.values():
            profile[2].close()


def build_project_listing_artifact_profile(target_id):
    from amiga_reversing.disasm.c_backend import build_project_listing_artifact_profile as build
    cache = _current.get()
    if cache is None:
        return build(target_id)
    if target_id not in cache:
        cache[target_id] = build(target_id)
    profile = cache[target_id]
    return profile[0], profile[1], _BorrowedArtifact(profile[2])
