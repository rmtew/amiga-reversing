"""Strict offline native-ASM versus runtime-fixup comparison on one DOS host.

This does not establish original-vs-restored equivalence for the shared wrapper.
No clock fitting, resampling, pixel masks or audio tolerances are applied.
"""

import argparse
import hashlib
import json
from pathlib import Path
from amiga_reversing.tools.pandora_rebase_output_compare import pcm_interval


def require(value, message):
    if not value:
        raise ValueError(message)


def pixels(left, right):
    from PIL import Image

    with Image.open(left) as a, Image.open(right) as b:
        a, b = a.convert("RGBA"), b.convert("RGBA")
        require(a.size == b.size, "Image crop/extent mismatch: " + left.name)
        rgba_left, rgba_right = a.tobytes(), b.tobytes()
        count = sum(
            rgba_left[i : i + 4] != rgba_right[i : i + 4]
            for i in range(0, len(rgba_left), 4)
        )
        return dict(
            name=left.name,
            width=a.width,
            height=a.height,
            differing_pixels=count,
            status="pass" if count == 0 else "mismatch",
        )


def initial_state(a, b):
    require(
        a["field_application"]["sha256"] == b["field_application"]["sha256"],
        "Applied game bytes/import differ",
    )
    require(
        a["actual_admission"]["owners"] == b["actual_admission"]["owners"],
        "Actual owners differ",
    )
    require(
        a["first_dispatch"]["after_stop"]["cck"]
        == b["first_dispatch"]["after_stop"]["cck"],
        "Original initializer clocks differ",
    )
    require(
        a["first_dispatch"]["after"] == b["first_dispatch"]["after"],
        "Original initializer registers/CCR/stack differ",
    )
    require(
        a["initial_state"] == b["initial_state"], "Initial retained PRNG bytes differ"
    )
    # The reference's native binding values change its pre-entry validation
    # scratch values and DOS instruction count. Equality begins at the actual
    # measured game boundary, not at an invented global instruction counter.


def compare_title(reference, candidate):
    a = json.loads((reference / "live.json").read_text())
    b = json.loads((candidate / "live.json").read_text())
    require(
        a["status"]
        == b["status"]
        == "bounded_original_helper_settled_title_and_DMA_capture",
        "Incomplete anchored title capture",
    )
    initial_state(a, b)
    x, y = a["anchored_title"], b["anchored_title"]
    for key in (
        "registers",
        "PRNG_bytes",
        "title_stars_sha256",
        "visits",
        "source_offset",
    ):
        require(x[key] == y[key], "Title state differs: " + key)
    require(
        x["source_offset"] == 0xFD2
        and x["stop"]["cck"] == y["stop"]["cck"]
        and x["first_stop"]["cck"] == y["first_stop"]["cck"],
        "Title helper/clocks differ",
    )
    for state in (x, y):
        require(
            state["stop"]["frame"] >= state["first_stop"]["frame"] + 180
            and state["input_count"] == state["guest_state_writes"] == 0,
            "Not an ordinary settled title window",
        )
    for directory, state in ((reference, x), (candidate, y)):
        require(
            hashlib.sha256((directory / "settled-title.png").read_bytes()).hexdigest()
            == state["screenshot_sha256"],
            "Stale settled-title image",
        )
    image = pixels(reference / "settled-title.png", candidate / "settled-title.png")
    slots = []
    for directory, report in ((reference, a), (candidate, b)):
        recorded = report["title_DMA"]["frames"]
        require(
            len(recorded) == 2
            and not report["title_DMA"]["first_abandoned_image_transfers"],
            "Incomplete or unexpected sampled DMA",
        )
        metadata = {
            v["frame"]: v
            for v in map(
                json.loads,
                (directory / "dma-title/profile.jsonl").read_text().splitlines(),
            )
        }
        current = []
        for frame in recorded:
            entry = metadata[frame["frame"]]
            path = (directory / "dma-title" / entry["slots_file"]).resolve()
            require(
                path.is_relative_to((directory / "dma-title").resolve())
                and not entry["partial"]
                and hashlib.sha256(path.read_bytes()).hexdigest()
                == frame["slots_sha256"],
                "Stale title bus sidecar",
            )
            current.append((frame["frame"], frame["slots_sha256"]))
        slots.append(current)
    require(slots[0] == slots[1], "Complete sampled bus slots differ")
    start = a["payload_entry"]["stop"]["cck"]
    end = x["stop"]["cck"]
    require(
        start == b["payload_entry"]["stop"]["cck"], "Title audio entry clocks differ"
    )
    audio = {
        name: pcm_interval(
            reference / "audio-stems" / (name + ".wav"),
            candidate / "audio-stems" / (name + ".wav"),
            start,
            end,
        )
        for name in ("paula", "master", "drivesounds")
    }
    passed = image["status"] == "pass" and all(
        v["status"] == "pass" for v in audio.values()
    )
    return dict(
        status="pass" if passed else "mismatch",
        image=image,
        audio=audio,
        anchor_cck=end,
        source_offset=0xFD2,
        visits=x["visits"],
        complete_sampled_bus_frames=slots[0],
        scope="Settled title prefix on the same OS wrapper; emulator termination after capture is not an OS-return qualification.",
    )


def compare_route(reference, candidate):
    a = json.loads((reference / "live.json").read_text())
    b = json.loads((candidate / "live.json").read_text())
    require(
        a["status"]
        == b["status"]
        == "hosted_saved_earth_natural_exit_cold_route_complete",
        "Incomplete hosted completion/exit",
    )
    initial_state(a, b)
    x = json.loads((reference / "scenario-result.json").read_text())
    y = json.loads((candidate / "scenario-result.json").read_text())
    require(len(x["phases"]) == len(y["phases"]) == 576, "Missing route phases")
    for left, right in zip(x["phases"], y["phases"]):
        require(
            left["name"] == right["name"]
            and left["status"] == right["status"] == "hit",
            "Phase mismatch",
        )
        require(left["pc"] == right["pc"], "Runtime PC differs: " + left["name"])
        require(
            left["stop_event"]["cck"] == right["stop_event"]["cck"],
            "Phase clock differs: " + left["name"],
        )

    def inputs(report):
        return [
            (
                r["method"],
                r["arguments"],
                r["cleanup"],
                r["outcome"],
                r["anchor"]["phase"],
                r["anchor"]["stop"]["cck"],
            )
            for r in report["input_trace"]
        ]

    require(
        len(inputs(x)) == len(inputs(y)) == 509, "Missing controller acknowledgements"
    )
    require(inputs(x) == inputs(y), "Controller calls, releases or clocks differ")
    for report in (a, b):
        loss = report["route"]["loss"]
        require(
            loss["events"] > 0
            and loss["dropped_events"] == loss["dropped_notifications"] == 0,
            "Incomplete event evidence",
        )
        require(
            report["owned_exit"]["retained_count"]
            == report["owned_exit"]["audio_open"]
            == report["owned_exit"]["audio_lock"]
            == 0
            and report["owned_exit"]["signal"] == 0xFFFFFFFF,
            "Incomplete cleanup",
        )
        require(
            len(report["owned_exit"]["freed"]) == 10
            and report["game_DMA_quiescent"]["all_game_leases_still_owned"] == 10
            and not report["game_DMA_quiescent"]["DMACONR"] & 0x47FF,
            "Incomplete DMA-safe lease release",
        )
        ending = report["route"]["ending"]
        require(
            ending["saved_earth"] and ending["escaped"] and ending["health"] == 49,
            "Ending not qualified",
        )
    require(a["owned_exit"]["freed"] == b["owned_exit"]["freed"], "Freed leases differ")
    image_names = [v["phase"] + ".png" for v in a["route"]["screenshots"]]
    require(
        image_names
        == [
            name + ".png"
            for name in (
                "title_menu_loop",
                "ui_overlay_initialization",
                "initial_proximity_context",
                "entry_officer_card_transferred",
                "ei_sonicdriver_hit_1",
                "ac_console_ready",
                "saved_earth_escape",
            )
        ],
        "Missing representative output image",
    )
    require(
        image_names == [v["phase"] + ".png" for v in b["route"]["screenshots"]],
        "Missing output image",
    )
    for directory, report in ((reference, a), (candidate, b)):
        for item in report["route"]["screenshots"]:
            require(
                hashlib.sha256(
                    (directory / (item["phase"] + ".png")).read_bytes()
                ).hexdigest()
                == item["sha256"],
                "Stale output image: " + item["phase"],
            )
    images = [pixels(reference / name, candidate / name) for name in image_names]
    start = a["payload_entry"]["stop"]["cck"]
    end = a["game_DMA_quiescent"]["stop"]["cck"]
    require(
        start == b["payload_entry"]["stop"]["cck"]
        and end == b["game_DMA_quiescent"]["stop"]["cck"],
        "Audio game-boundary clocks differ",
    )
    audio = {
        name: pcm_interval(
            reference / "audio-stems" / (name + ".wav"),
            candidate / "audio-stems" / (name + ".wav"),
            start,
            end,
        )
        for name in ("paula", "master", "drivesounds")
    }
    passed = all(v["status"] == "pass" for v in images) and all(
        v["status"] == "pass" for v in audio.values()
    )
    return dict(
        schema="pandora-hosted-output-comparison/v1",
        status="pass" if passed else "mismatch",
        scope="Native assembly-time address bindings versus runtime fixups under the same OS wrapper, not original-vs-restored wrapper equivalence.",
        matched_phases=576,
        matched_controller_calls=len(inputs(x)),
        images=images,
        audio=audio,
        initializer_cck=a["first_dispatch"]["after_stop"]["cck"],
        initial_PRNG_bytes=a["initial_state"]["PRNG_bytes"],
        limits=[
            "Representative images and this normal-input route only; not all graphics/optional paths.",
            "No shifted samples, resampling, tolerance or crop normalization.",
            "Shared startup/audio ownership effects require separate evidence; original eight-CCK discrepancy remains open.",
            "CPU old-address observations are not DMA/all-fetch coverage.",
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title-reference", type=Path)
    parser.add_argument("--title-candidate", type=Path)
    args = parser.parse_args()
    if bool(args.title_reference) != bool(args.title_candidate):
        parser.error("Both title directories are required")
    result = compare_route(args.reference, args.candidate)
    if args.title_reference:
        result["settled_title"] = compare_title(
            args.title_reference, args.title_candidate
        )
        if result["settled_title"]["status"] != "pass":
            result["status"] = "mismatch"
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(result["status"])
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
