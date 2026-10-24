import copy
import subprocess
import shutil
import pytest
from amiga_reversing.tools.pandora_hosted_output_compare import initial_state


def boundary():
    return dict(
        field_application=dict(sha256="actual-input"),
        actual_admission=dict(owners={"prng": 0x1998}),
        first_dispatch=dict(
            after_stop=dict(cck=89022898), after=dict(pc=0x89F26, sr=0x2700, a7=0x8044E)
        ),
        initial_state=dict(PRNG_bytes="da05da004f23bb9d"),
    )


@pytest.mark.parametrize(
    "change", ["clock", "CCR", "retained_PRNG_byte", "input", "owner"]
)
def test_shared_OS_boundary_refuses_nonmatching_evidence(change):
    a = boundary()
    b = copy.deepcopy(a)
    initial_state(a, b)
    if change == "clock":
        b["first_dispatch"]["after_stop"]["cck"] += 1
    elif change == "CCR":
        b["first_dispatch"]["after"]["sr"] ^= 1
    elif change == "retained_PRNG_byte":
        b["initial_state"]["PRNG_bytes"] = "da05da004f23bb9e"
    elif change == "input":
        b["field_application"]["sha256"] = "different"
    else:
        b["actual_admission"]["owners"]["prng"] += 8
    with pytest.raises(ValueError):
        initial_state(a, b)


def test_pixel_comparison_never_normalizes_crops_or_ignores_a_pixel(tmp_path):
    # The existing offline image tool uses installed system Python + Pillow,
    # separately from the native project's Python 3.14 environment.
    code = """from pathlib import Path
from PIL import Image
from amiga_reversing.tools.pandora_hosted_output_compare import pixels
import sys
a=Path(sys.argv[1])/'a.png';b=a.with_name('b.png')
Image.new('RGBA',(3,2),(0,0,0,255)).save(a)
Image.new('RGBA',(3,2),(0,0,0,255)).save(b)
assert pixels(a,b)['status']=='pass'
i=Image.open(b);i.putpixel((2,1),(0,0,1,255));i.save(b)
assert pixels(a,b)['differing_pixels']==1 and pixels(a,b)['status']=='mismatch'
Image.new('RGBA',(2,2),(0,0,0,255)).save(b)
try:pixels(a,b)
except ValueError as error:assert 'crop/extent' in str(error)
else:raise AssertionError('Mismatched crop admitted')
"""
    result = subprocess.run(
        [shutil.which("python3"), "-c", code, str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_reference_only_normalizes_declared_typed_import():
    # Native tool imports require the project's Python3.14; this test does not
    # execute the original game, synthesize a candidate, or bypass native facts.
    from amiga_reversing.tools.pandora_OS_output_reference import verify_reference_bytes

    data = b"prefix\x00\x08\x9f\x26suffix"
    before = b"prefix\x00\xc0\x7d\xbasuffix"
    field = dict(
        width=4,
        role="host_mission_restart_dispatch",
        source_offset=6,
        staged_value=0x89F26,
    )
    verify_reference_bytes(data, before, field)
    assert before == b"prefix\x00\xc0\x7d\xbasuffix"
    with pytest.raises(ValueError, match="outside import"):
        verify_reference_bytes(data, b"changed" + before[7:], field)
    with pytest.raises(ValueError, match="lengths differ"):
        verify_reference_bytes(data, before[:-1], field)
    with pytest.raises(ValueError, match="Only the native typed"):
        verify_reference_bytes(data, before, dict(field, width=2))


def test_asset_audit_refuses_changed_bytes_or_wrong_original():
    import hashlib
    from amiga_reversing.tools.pandora_OS_output_reference import audit_assets_dma

    original = b"abcd"
    manifest = dict(
        manifest=dict(
            target_identity_sha256=hashlib.sha256(original).hexdigest(),
            files=[
                dict(
                    kind="asset",
                    source_offset=0,
                    size=4,
                    source_section_index=0,
                    sha256=hashlib.sha256(original).hexdigest(),
                    path="asset.bin",
                )
            ],
        )
    )
    with pytest.raises(ValueError, match="Canonical asset bytes differ"):
        audit_assets_dma({}, b"abce", manifest, [], original=original)
    with pytest.raises(ValueError, match="different original binary"):
        audit_assets_dma({}, original, manifest, [], original=b"other")
