"""Bounded, read-only Pandora terrain and encounter model.

Consumes native symbols, existing record schemas and a verified Copperline
checkpoint. This is an offline scenario-planning aid, not an emulator or a new
source of target facts. Unknown scripts/events remain explicit.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import time
from pathlib import Path

from amiga_reversing.disasm.effective_metadata import effective_target_metadata
from amiga_reversing.disasm.project_paths import resolve_project_paths
from amiga_reversing.disasm.restoration_client import RestorationClient
from amiga_reversing.tools.direct_payload_adapter import load_contract


def script_envelope(data, start, runtime_base, opcodes, *, max_steps=4096):
    """Interpret only the original script subset needed for patrol bounds.

    Delays/animation selection do not change object world XY. Counters are local
    copies; the original binary is never changed. Repeat tests BEFORE decrement,
    so an ADD preceding a repeat with reload N executes N+1 times.
    """
    pc, xy, memory, seen, points, moves = start, None, {}, set(), [], {}
    repeat_entries = set()
    names = {value: name.removeprefix("WORLD_CMD_") for name, value in opcodes.items()}
    def word(p):
        if not 0 <= p <= len(data)-2:
            raise ValueError("script operand outside source")
        return memory.get(p, int.from_bytes(data[p:p+2], "big"))
    def signed(p):
        v = word(p)
        return v-65536 if v & 32768 else v
    def complete(step):
        return {"status": "bounded_cycle", "steps": step,
                "x_range": [min(p[0] for p in points), max(p[0] for p in points)],
                "y_range": [min(p[1] for p in points), max(p[1] for p in points)],
                "admitted_source_offsets": sorted({state[0] for state in seen}),
                "movement_executions": {hex(k): v for k, v in moves.items()}}
    for step in range(max_steps):
        if not start <= pc < min(len(data)-10, start+4096):
            return {"status": "unknown", "reason": "outside local script budget"}
        state = (pc, xy, tuple(sorted(memory.items())))
        if state in seen:
            if not points:
                return {"status": "unknown", "reason": "no position established"}
            return complete(step)
        seen.add(state)
        name = names.get(word(pc))
        if name == "SET_POSITION":
            xy = (word(pc+2), word(pc+4)); pc += 6
        elif name in {"ADD_X", "ADD_Y"} and xy is not None:
            axis = int(name == "ADD_Y"); v = list(xy)
            v[axis] += signed(pc+2)
            if not 0 <= v[axis] < 65536:
                return {"status": "unknown", "reason": "coordinate wrapping"}
            xy = tuple(v); moves[pc] = moves.get(pc, 0)+1; pc += 4
        elif name == "SET_DELAY":
            pc += 4
        elif name == "COPY_RELATIVE_WORD":
            displacement = signed(pc+2)
            destination = pc+4+displacement
            if not start <= destination-4 < min(len(data)-8, start+4096) or word(destination-4) != opcodes.get("WORLD_CMD_REPEAT_BRANCH_OR_RELOAD"):
                return {"status": "unknown", "reason": "copy is not a local repeat-counter reset"}
            memory[destination] = word(destination-2); pc += 4
        elif name == "REPEAT_BRANCH_OR_RELOAD":
            if pc not in repeat_entries and word(pc+4) != word(pc+2):
                return {"status": "unknown", "reason": "initial repeat count differs from reload"}
            repeat_entries.add(pc)
            if word(pc+4):
                memory[pc+4] = word(pc+4)-1; pc += signed(pc+6)
            else:
                memory[pc+4] = word(pc+2); pc += 8
        elif name == "JUMP_ABSOLUTE":
            pc = int.from_bytes(data[pc+2:pc+6], "big")-runtime_base
            if pc == start and names.get(word(start)) == "SET_POSITION" and points:
                return complete(step+1)
        elif name == "SET_NODE_FOR_FLAG3_CLEAR":
            pc += 6
        elif name == "TOGGLE_NODE_FOR_FLAG3_CLEAR":
            # Original handler toggles a state-node flag and advances two bytes;
            # it does not change object world X/Y (bounds model only).
            pc += 2
        elif name == "SET_NODE_SEQUENCE_FOR_FLAG3_CLEAR":
            pc += 10
        else:
            return {"status": "unknown", "reason": f"unmodelled opcode {word(pc)} at {hex(pc)}"}
        if xy is not None:
            points.append(xy)
    return {"status": "unknown", "reason": "script step budget exhausted"}


def encounter_outcome(player, actor):
    """Conservative model of the nearby-object gate, before weapon processing."""
    if actor["flags"] & 0x12 or actor["flags"] & 8:
        return "no_automatic_combat"
    if abs(player[0]-actor["xy"][0]) >= 24 or abs(player[1]-actor["xy"][1]) >= 16:
        return "out_of_range"
    if 0 <= actor["selected_item_id"]-7 < 15:
        return "combat"
    return "trade_predicate_unresolved"


def movement_gate(ui_flags, *, status_flags=0, player_flags=0, inhibited=False):
    """Recovered entry/commit gates from source95E2..9802, before tile probes."""
    if ui_flags & 6:
        return "combat_or_inventory_blocks_movement"
    if status_flags & 16:
        return "camera_scroll_defers_movement"
    if player_flags & 2:
        return "defeated_player"
    if inhibited:
        return "commit_inhibited"
    return "geometry_probe_required"


def keepout(envelope):
    # Strict <24/<16 interaction bounds; integer endpoints are inclusive.
    return (envelope["x_range"][0]-23, envelope["x_range"][1]+23,
            envelope["y_range"][0]-15, envelope["y_range"][1]+15)


class Terrain:
    def __init__(self, grid, solid_bits, frames, modal_tiles=()):
        self.grid, self.bits, self.frames = grid, solid_bits, frames
        self.modal = set(modal_tiles)
        self.width, self.height = len(grid[0])*16, len(grid)*16

    def blocked(self, x, y):
        if not 0 <= x < self.width or not 0 <= y < self.height:
            return True
        tile = self.grid[y//16][x//16]
        return tile in self.modal or tile >= len(self.bits)*8 or bool(self.bits[tile//8] & (128 >> (tile%8)))

    def permits(self, x, y, dx, dy):
        for width, height, ox, oy in self.frames:
            left, right, bottom = x+dx+ox, x+dx+ox+width, y+dy+oy+height
            if dx:
                if self.blocked(left if dx < 0 else right, bottom-4):
                    return False
            else:
                yy = bottom-3 if dy < 0 else bottom
                if any(self.blocked(xx, yy) for xx in (left+3, (left+right)//2, right-4)):
                    return False
        return True


def move(state, direction):
    x, y, last = state
    dx, dy = {"right": (7, 0), "left": (-7, 0), "down": (0, 4), "up": (0, -4)}[direction]
    drift = (7 if last == "left" else -7 if last == "right" else 0) if dy else 0
    return (x+dx+drift, y if drift else y+dy, direction), dx, dy


def plan(terrain, start, goal, heuristic, rectangles, *, max_states=250000):
    began = time.monotonic()
    queue, costs, previous = [(0, 0, start)], {start: 0}, {start: None}
    expanded = rejected_events = 0
    while queue and expanded < max_states:
        _, cost, state = heapq.heappop(queue)
        if costs[state] != cost:
            continue
        expanded += 1
        if goal(*state[:2]):
            path = []
            while previous[state] is not None:
                parent, direction = previous[state]; path.append((direction, state)); state = parent
            return {"status": "conditional_candidate", "path": list(reversed(path)),
                    "expanded": expanded, "event_edges_rejected": rejected_events,
                    "seconds": round(time.monotonic()-began, 3)}
        for direction in ("right", "left", "down", "up"):
            nxt, dx, dy = move(state, direction)
            x, y = nxt[:2]
            if not 0 <= x < terrain.width or not 0 <= y < terrain.height:
                continue
            if any(a <= x <= b and c <= y <= d for a, b, c, d in rectangles):
                rejected_events += 1; continue
            if not terrain.permits(*state[:2], dx, dy) or costs.get(nxt, 10**9) <= cost+1:
                continue
            costs[nxt] = cost+1; previous[nxt] = (state, direction)
            heapq.heappush(queue, (cost+1+heuristic(x, y), cost+1, nxt))
    return {"status": "unknown_no_route_within_model_budget", "expanded": expanded,
            "event_edges_rejected": rejected_events,
            "seconds": round(time.monotonic()-began, 3)}


def _symbols(client, target, revision, **filters):
    items, cursor = [], None
    while True:
        page = client.call(target, "query", kind="symbols", expected_revision=revision,
                           limit=100, **filters, **({"cursor": cursor} if cursor else {}))
        items += page["items"]
        if not page["has_more"]:
            return items
        cursor = page["next_cursor"]


def actor_at_source(actors, source_offset):
    """Bind a verified original object coordinate independently of its name."""
    matches = [actor for actor in actors if actor["source_offset"] == source_offset]
    if len(matches) != 1:
        raise ValueError("actor source identity is missing or ambiguous")
    return matches[0]


def build(target, observation_path):
    report = json.loads(observation_path.read_text()); observation = report.get("runner", report)["observation"]
    phase = next((p for p in observation["scenario"]["phases"] if p["name"] == "model_observe_encounter_entry"), None)
    if (phase is None or phase["status"] != "hit" or phase["payload"]["status"] != "pc_matched"
            or phase["payload"]["payload_offset"] != "0x7792"):
        raise ValueError("requires verified canonical combat-entry checkpoint")
    payload = resolve_project_paths(target).binary_source.path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    contract = load_contract("pandora")
    if (target != contract.target_id or digest != contract.payload_sha256
            or observation["direct_payload_handoff"]["payload_sha256"] != digest
            or phase["payload"]["payload_sha256"] != digest):
        raise ValueError("original payload identity mismatch")
    materialization = observation["reverse_boundary"]["materialization"]
    copied = contract.materialization
    expected_copy = payload[copied["source_offset"]:copied["source_offset"]+copied["size"]]
    if (materialization["status"] != "verified"
            or materialization["copied_sha256"] != hashlib.sha256(expected_copy).hexdigest()):
        raise ValueError("requires full copied-image verification")
    base = int(phase["payload"]["runtime_base"], 0)
    if base != copied["runtime_address"]-copied["source_offset"]:
        raise ValueError("checkpoint runtime mapping differs from the materialized view")
    client = RestorationClient(timeout=120); state = client.call(target, "state")
    if not state["ready"]:
        raise ValueError("native facts not ready")
    rev = state["revision"]
    rows = []
    for prefix in ("world_object_", "player_move_", "WORLD_CMD_", "item_receptacle_position_descriptors", "item_receptacle_5", "TILE_ID_"):
        rows += _symbols(client, target, rev, query=prefix)
    for name in ("row_selector_ids", "world_tile_definition_offset_records", "tile_movement_block_bits", "initial_ranged_weapon_ammunition", "player_world_object"):
        rows += _symbols(client, target, rev, symbol=name)
    source = {r["name"]: r["source_offset"] for r in rows if r.get("source_offset") is not None}
    values = {r["name"]: int(r["expression"]) for r in rows if r["name"].startswith("WORLD_CMD_")}
    metadata = effective_target_metadata(resolve_project_paths(target).target_dir)
    structs = {s.name: {f.name: (f.offset, f.size) for f in s.fields} for s in metadata.custom_structs}
    struct_sizes = {s.name: s.size for s in metadata.custom_structs}
    def field(data, layout, name):
        offset, size = structs[layout][name]
        if not 0 <= offset <= len(data)-size:
            raise ValueError("captured field lies outside its record")
        return int.from_bytes(data[offset:offset+size], "big")
    def word(p):
        return int.from_bytes(payload[p:p+2], "big")
    def pointer(p):
        return int.from_bytes(payload[p:p+4], "big")-base
    grid = [[0]*90 for _ in range(129)]
    for sy in range(43):
        for sx in range(30):
            selector = word(source["row_selector_ids"]+(sy*30+sx)*2)
            for yy in range(3):
                for xx in range(3):
                    grid[sy*3+yy][sx*3+xx] = word(source["world_tile_definition_offset_records"]+selector*18+(yy*3+xx)*2)//128
    frames = []
    for direction in ("positive_x", "negative_x", "positive_y", "negative_y"):
        stem = "player_move_"+direction
        count = payload[source[stem+"_animation_frame_count"]] if stem+"_animation_frame_count" in source else payload[source[stem+"_animation"]+structs["WorldPositionStateNode"]["frame_count"][0]]
        for i in range(count+1):
            p = pointer(source[stem+"_frames"]+i*4)
            frame = payload[p:p+26]
            frames.append(tuple(field(frame, "world_position_collision_bounds", f) for f in
                                ("world_x_extent", "world_y_extent", "world_x_origin_offset", "world_y_origin_offset")))
    actors = []
    for i in range(128):
        p = pointer(source["world_object_ptr_table"]+i*4)
        if p == -base:
            break
        record_size = struct_sizes["world_object_shared_prefix"]
        if not 0 <= p <= len(payload)-record_size:
            raise ValueError("object pointer outside original image")
        name = next((r["name"] for r in rows if r.get("source_offset") == p and
                     (r["name"].startswith("world_object_") or r["name"] == "player_world_object")), hex(p))
        record = payload[p:p+record_size]
        script = field(record, "world_object_shared_prefix", "initial_behavior_script_ptr")
        profile = script_envelope(payload, script-base, base, values) if script else {"status": "unknown", "reason": "no script; descriptor initialization needs separate evidence"}
        actors.append({"name": name, "source_offset": p, "initial_script": script-base if script else None, "script_envelope": profile})
    else:
        raise ValueError("object table terminator not found within budget")
    capture = phase["capture"]; actor_source = int(capture["registers"]["a5"], 0)-base
    baseline = next((p for p in observation["scenario"]["phases"] if p["name"] == "entry_officer_card_transferred"), None)
    if (baseline is None or baseline["status"] != "hit" or baseline["payload"]["status"] != "pc_matched"
            or baseline["payload"]["payload_offset"] != "0x4b13c"
            or baseline["payload"]["payload_sha256"] != digest
            or int(baseline["payload"]["runtime_base"], 0) != base):
        raise ValueError("requires the verified pre-movement player checkpoint")
    player_read = baseline["capture"]["memory_reads"][0]
    player_data = bytes.fromhex(player_read["bytes"])
    xy_offset = structs["world_object_shared_prefix"]["world_x"][0]
    if int(player_read["address"], 0) != base+source["player_world_object"]+xy_offset:
        raise ValueError("baseline capture is not the canonical player XY record")
    start_xy = [int.from_bytes(player_data[:2], "big"), int.from_bytes(player_data[2:4], "big")]
    direction_offset = structs["world_object_shared_prefix"]["movement_direction_flags"][0]-xy_offset
    selected_offset = structs["world_object_shared_prefix"]["selected_item_id"][0]-xy_offset
    if len(player_data) <= max(direction_offset, selected_offset) or player_data[direction_offset] != 0:
        raise ValueError("baseline is not a complete initial player-direction checkpoint")
    start_state = (*start_xy, "none")
    actor = actor_at_source(actors, actor_source)
    record = bytes.fromhex(capture["memory_reads"][3]["bytes"]+capture["memory_reads"][4]["bytes"])
    first_read = capture["memory_reads"][3]
    second_read = capture["memory_reads"][4]
    if (int(first_read["address"], 0) != actor_source+base
            or int(second_read["address"], 0) != actor_source+base+len(bytes.fromhex(first_read["bytes"]))):
        raise ValueError("actor record captures are not contiguous at the observed actor")
    observed_actor = {"name": actor["name"], "xy": [field(record, "world_object_shared_prefix", n) for n in ("world_x", "world_y")],
                      "flags": field(record, "world_object_shared_prefix", "world_object_flags"),
                      "selected_item_id": field(record, "world_object_shared_prefix", "selected_item_id")}
    player_bytes = bytes.fromhex(capture["memory_reads"][0]["bytes"])
    player = [int.from_bytes(player_bytes[:2], "big"), int.from_bytes(player_bytes[2:], "big")]
    pointers = bytes.fromhex(capture["memory_reads"][5]["bytes"])
    if int.from_bytes(pointers[8:12], "big") != actor_source+base:
        raise ValueError("captured actor is not the current nearest object")
    envelope = actor["script_envelope"]
    if envelope["status"] != "bounded_cycle":
        raise ValueError("blocking actor has no admitted patrol bound")
    if sum(a["initial_script"] == actor["initial_script"] for a in actors) != 1:
        raise ValueError("shared mutable script counters need separate ownership evidence")
    if (field(record, "world_object_shared_prefix", "initial_behavior_script_ptr")-base != actor["initial_script"]
            or field(record, "world_object_shared_prefix", "behavior_script_ptr")-base not in envelope["admitted_source_offsets"]):
        raise ValueError("live actor script differs from the admitted original patrol")
    rectangle = keepout(envelope)
    modal = [int(r["expression"].removeprefix("$"), 16) if r["expression"].startswith("$") else int(r["expression"])
             for r in rows if r["name"].startswith("TILE_ID_")]
    terrain = Terrain(grid, payload[source["tile_movement_block_bits"]:source["tile_movement_block_bits"]+64], tuple(set(frames)), modal)
    excluded_rows = ["".join("#" if terrain.blocked(x*16, y*16) else "." for x in range(90)) for y in range(129)]
    gun_position = source["item_receptacle_position_descriptors_position_state_ptr_5"]
    gx, gy = word(gun_position+4), word(gun_position+6)
    pickup_source = source["item_receptacle_5_interaction_data"]
    pickup = payload[pickup_source:pickup_source+struct_sizes["item_receptacle_interaction_data"]]
    rifle_id = field(pickup, "item_receptacle_interaction_data", "required_item_definition_id")
    music_actor = actor_at_source(actors, 0x4C1D2)
    music_actor_bytes = payload[music_actor["source_offset"]:music_actor["source_offset"]+struct_sizes["world_object_shared_prefix"]]
    prerequisites = {
        "status": "conditional_dependency_model_not_an_executed_BYTE_path",
        "rifle_pickup": {"xy": [gx, gy], "item_id": rifle_id,
                         "interaction_data_source_offset": pickup_source,
                         "initial_stored_attachment": field(pickup, "item_receptacle_interaction_data", "stored_attachment_state_ptr"),
                         "requires": ["selected item<2", "distance<28", "fresh proximity-latch entry", "inventory/combat UI clear"]},
        "arm_audio": {"center": [840, 168], "requires": ["Pianist alive", "Manhattan distance<256"],
                      "effect": "shared audio bit0 set; WORD volume updated", "source_pc": "0x5534a"},
        "direct_weapon_kill": {"feed_initial_hp": field(music_actor_bytes, "world_object_shared_prefix", "initial_hit_points"),
                               "rifle_damage": 30, "initial_ammunition": list(payload[source["initial_ranged_weapon_ammunition"]:source["initial_ranged_weapon_ammunition"]+2]),
                               "requires": ["rifle selected", "ammo nonzero", "fresh fire edge", "valid accepted aim direction",
                                            "unblocked ray hits CURRENT Pianist geometry", "no earlier nearby combat transition"],
                               "effect": "defeated bit1 set without the combat world-X bias", "source_pc": "0x93fa"},
        "BYTE_write": {"requires": ["Pianist defeated bit1", "shared audio bit0 still set"],
                       "source_pc": "0x552f0", "state": "not dynamically observed"},
        "order": ["acquire rifle", "arm proximity audio alive", "aim and fire without an encounter",
                  "direct kill before same-frame proximity update", "BYTE guard sees both bits"],
        "limit": "Weapon hit and inventory predicates are recovered target rules; unknown NPC timing is not assumed safe."
    }
    # Preserve old consumer keys while exposing current actor-neutral identity.
    prerequisites["direct_weapon_kill"]["music_actor_initial_hp"] = prerequisites["direct_weapon_kill"]["feed_initial_hp"]
    prerequisites["music_actor"] = {"name": music_actor["name"], "source_offset": music_actor["source_offset"]}
    route = plan(terrain, start_state, lambda x, y: x < gx and abs(y-gy) < 8 and 31 <= abs(x-gx)+abs(y-gy) <= 38,
                 lambda x, y: max(0, abs(x-gx)-40)/7+max(0, abs(y-gy)-8)/4, [rectangle])
    def summarize_route(route):
        path = route.pop("path", [])
        runs = []
        for direction, end in path:
            if runs and runs[-1]["direction"] == direction:
                runs[-1]["moves"] += 1; runs[-1]["endpoint"] = end
            else:
                runs.append({"direction": direction, "moves": 1, "endpoint": end})
        route.update(accepted_moves=len(path), runs=runs, checkpoints=[{"after_moves": i+1, "expected_state": p[1], "required_ui_mask6": 0} for i, p in enumerate(path) if (i+1) % 8 == 0 or i+1 == len(path)])
        return route
    route = summarize_route(route)
    # Stop west of the entire patrol envelope, with one accepted-X-step margin.
    # This creates an observable waiting goal instead of guessing a crossing.
    wait_xy = [start_xy[0]+((rectangle[0]-1-start_xy[0])//7-1)*7, player[1]]
    staging = summarize_route(plan(terrain, start_state, lambda x, y: [x, y] == wait_xy,
                                  lambda x, y: abs(x-wait_xy[0])/7+abs(y-wait_xy[1])/4, [rectangle]))
    staging["goal"] = wait_xy
    staging["next_gate"] = "Do not enter the patrol envelope until a short-horizon actor-position or interaction predicate is established."
    if client.call(target, "state")["revision"] != rev:
        raise ValueError("native revision changed during model generation")
    transition = {"status": "not_observed", "limit": "No post-entry movement checkpoint in this receipt."}
    after = next((p for p in observation["scenario"]["phases"] if p["name"] == "model_encounter_disables_movement"), None)
    if after is not None:
        if (after["status"] != "hit" or after["payload"]["status"] != "pc_matched"
                or after["payload"]["payload_offset"] != "0x9984"
                or after["payload"]["payload_sha256"] != digest
                or int(after["payload"]["runtime_base"], 0) != base):
            raise ValueError("post-encounter checkpoint has no matching canonical identity")
        reads = after["capture"]["memory_reads"]
        xy_bytes = bytes.fromhex(reads[0]["bytes"])
        after_xy = [int.from_bytes(xy_bytes[:2], "big"), int.from_bytes(xy_bytes[2:], "big")]
        ui = int(reads[2]["bytes"], 16)
        expected_xy = [(player[0]+10000) & 65535, player[1]]
        if after_xy != expected_xy or not ui & 2:
            raise ValueError("observed encounter transition differs from the model")
        transition = {"status": "validated", "source_pc": "0x9984",
                      "predicted_combat_xy": expected_xy, "observed_player_xy": after_xy,
                      "ui_flags": ui, "movement_gate": movement_gate(ui)}
    return {"schema_version": 1, "target_id": target, "original_sha256": digest, "native_subject_revision": state["subject_revision"],
            "source_bindings": {k: v for k, v in source.items() if k in {
                "row_selector_ids", "world_tile_definition_offset_records", "tile_movement_block_bits", "world_object_ptr_table",
                "item_receptacle_position_descriptors_position_state_ptr_5", "item_receptacle_5_interaction_data",
                "initial_ranged_weapon_ammunition", "player_world_object", music_actor["name"], actor["name"]} or k.endswith("_frames") or k.endswith("_animation_frame_count")},
            "opcode_values": values, "map": {"tiles": [90, 129], "tile_pixels": 16, "world_pixels": [1440, 2064],
                                               "excluded_tile_rows": excluded_rows, "legend": "# = solid or modal tile, not a complete player/event accessibility map"},
            "pose_entries": len(frames), "unique_pose_bounds": len(set(frames)), "actors": actors,
            "initial_player": {"xy": start_xy, "selected_item_id": player_data[selected_offset],
                               "direction": "none", "source_checkpoint": "0x4b13c"},
            "validated_encounter": {"player_xy": player, "actor": observed_actor, "predicted_outcome": encounter_outcome(player, observed_actor),
                                    "observed_outcome": "canonical combat entry7792", "patrol_keepout_inclusive": rectangle},
            "validated_transition": transition,
            "scenario_prerequisites": prerequisites,
            "rifle_staging_route": route,
            "blocking_actor_staging_route": staging,
            "pianist_staging_route": staging,
            "legacy_field_aliases": {"pianist_staging_route": "blocking_actor_staging_route",
                                     "feed_initial_hp": "music_actor_initial_hp"},
            "limits": ["Only the observed blocking actor's complete original-script envelope is enforced by this route; other actors remain explicit unknowns.",
                       "Bounds assume original script and no external coordinate writes/combat bias; delays are not a timing prediction.",
                       "The keepout assumes the captured actor flags and selected item; changed actor state requires reinspection.",
                       "Route is a programmatic candidate requiring short runtime checkpoints, not a newly executed route or BYTE-writer qualification.",
                       "No native facts, original bytes, registers or emulator state are modified by this offline model."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = build(args.target, args.observation)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"encounter": result["validated_encounter"],
                      "transition": result["validated_transition"]["status"],
                      "rifle_route": result["rifle_staging_route"]["status"],
                      "staging_goal": result["blocking_actor_staging_route"]["goal"],
                      "staging_moves": result["blocking_actor_staging_route"]["accepted_moves"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
