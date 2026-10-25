import hashlib

import pytest

from amiga_reversing.tools import starglider2_extract as recipe


def test_reviewed_identity_required():
    with pytest.raises(ValueError, match="reviewed"):
        recipe.extract(bytes(901120))
    with pytest.raises(ValueError, match="reviewed"):
        recipe.extract(b"")


def test_spans_and_copy_boundary_with_synthetic_disk(monkeypatch):
    # Exercise extraction arithmetic without publishing copyrighted fixture bytes.
    disk = bytes(range(256)) * 3520
    monkeypatch.setattr(recipe, "DISK_SHA256", hashlib.sha256(disk).hexdigest())
    payloads, receipt = recipe.extract(disk)
    assert payloads["intro_read"] == disk[0x2C00:0x10600]
    assert payloads["game_read"] == disk[0x16000:0x7AE00]
    assert payloads["game_copy"] == disk[0x16000:0x7AC40]
    assert payloads["game_read"].startswith(payloads["game_copy"])
    assert len(payloads["game_read"]) - len(payloads["game_copy"]) == 448
    assert receipt["copy_iterations"] * receipt["copy_width"] == 412736
    assert receipt["spans"][-1]["entrypoint"] == 0x1000
    assert receipt["status"] == "static_extraction"
