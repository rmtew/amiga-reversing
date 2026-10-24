import pytest
from amiga_reversing.tools import pandora_hosted_title as title


class Client:
    def __init__(self, *, stuck=False):
        self.pc = 0x89F26
        self.visits = 0
        self.stuck = stuck
        self.reads = []
        self.requests = []

    def add_breakpoint(self, pc):
        self.target = pc
        return 1

    def remove_breakpoint(self, identity):
        assert identity == 1

    def registers(self):
        return dict(pc=self.pc)

    def run_until(self, goal, timeout):
        self.visits += 1
        self.pc = self.target
        return dict(
            frame=10 if self.stuck or self.visits == 1 else 190,
            cck=self.visits * 100,
            reason="breakpoint" if self.visits <= 2 or self.stuck else "target",
        )

    def read_memory(self, address, size):
        self.reads.append((address, size))
        return bytes(size)

    def request(self, method, args=None):
        self.requests.append((method, args))
        if method == "step":
            self.pc += 4
            return dict(reason="step")
        if method == "capture.screenshot":
            from pathlib import Path

            Path(args["path"]).write_bytes(b"capture fixture")
        return {}


def native():
    return dict(
        members=[dict(region_id="pandora_prng_state", staged_address=0x7E8)],
        layout=dict(
            items=[
                dict(
                    regions=[
                        dict(
                            region_id="pandora_prng_state",
                            region_kind="workspace",
                            runtime_address=0x1998,
                        ),
                        dict(
                            region_id="pandora_title_stars",
                            region_kind="workspace",
                            runtime_address=0x10AF0,
                        ),
                        dict(
                            region_id="image",
                            region_kind="image",
                            original_address=0x10000,
                            runtime_address=0x80000,
                            size=0x55370,
                        ),
                    ]
                )
            ]
        ),
    )


def test_title_uses_natural_frame_boundary_and_actual_not_staged_owner(
    monkeypatch, tmp_path
):
    client = Client()
    records = {}
    monkeypatch.setattr(title, "summarize_dma", lambda *a: dict(scope="fixture only"))
    with pytest.raises(title.TitleCaptured):
        title.TitleCapture()(
            client,
            0,
            {},
            native(),
            tmp_path,
            lambda key, **data: records.update({key: data}),
        )
    assert records["anchored_title"]["visits"] == 2
    assert (
        records["anchored_title"]["stop"]["frame"]
        - records["anchored_title"]["first_stop"]["frame"]
        == 180
    )
    assert client.reads == [(0x1998, 8), (0x10AF0, 1000)]
    assert [m for m, a in client.requests if m.startswith("profile.")] == [
        "profile.start",
        "profile.stop",
    ]
    assert (
        records["anchored_title"]["guest_state_writes"]
        == records["anchored_title"]["input_count"]
        == 0
    )


def test_title_stuck_visits_never_pass_as_settled_frames(tmp_path):
    client = Client(stuck=True)
    with pytest.raises(ValueError, match="within4096"):
        title.TitleCapture()(client, 0, {}, native(), tmp_path, lambda *a, **k: None)
    assert client.visits == 4096
    assert not any(method == "capture.screenshot" for method, args in client.requests)
