from __future__ import annotations

from dataclasses import dataclass

from disasm.target_metadata import (
    TargetMetadata,
    effective_entry_register_seeds,
    target_metadata_seed_key,
)
from m68k.abstract_values import _concrete, _unknown
from m68k.m68k_executor import CPUState
from m68k.memory_provenance import (
    MemoryRegionAddressSpace,
    MemoryRegionProvenance,
    provenance_named_base,
)
from m68k.os_calls import LibraryBaseTag, PlatformState, TypedMemoryRegion
from m68k.registers import parse_reg_name
from m68k_kb import runtime_os


@dataclass(frozen=True, slots=True)
class EntrySeedConfig:
    initial_state: CPUState | None
    initial_register_regions: dict[str, TypedMemoryRegion]
    initial_register_tags: dict[str, object]
    entry_initial_states: dict[int, CPUState]
    entry_register_regions: dict[int, dict[str, TypedMemoryRegion]]
    entry_register_tags: dict[int, dict[str, object]]
    seed_key: str


def _normalize_register_name(register: str) -> str:
    parsed = parse_reg_name(register)
    if parsed is None:
        raise ValueError(f"Invalid entry seed register: {register}")
    mode, reg_num = parsed
    prefix = "a" if mode == "an" else "d"
    return f"{prefix}{reg_num}"


def _build_region(kind: str,
                  struct_name: str | None,
                  library_name: str | None,
                  context_name: str | None,
                  ) -> TypedMemoryRegion:
    if struct_name is None:
        raise ValueError(f"Missing struct_name for entry seed kind {kind}")
    struct_def = runtime_os.STRUCTS.get(struct_name)
    if struct_def is None:
        raise KeyError(f"Unknown entry seed struct: {struct_name}")
    if kind == "library_base":
        if library_name is None:
            raise ValueError("library_base entry seed requires library_name")
        provenance = provenance_named_base(library_name)
    elif kind == "struct_ptr":
        provenance = MemoryRegionProvenance(address_space=MemoryRegionAddressSpace.REGISTER)
    else:
        raise ValueError(f"Unsupported entry seed kind: {kind}")
    return TypedMemoryRegion(
        struct=struct_name,
        size=struct_def.size,
        provenance=provenance,
        context_name=context_name,
    )


def _build_seed_state(seeds: tuple[object, ...]) -> tuple[
    CPUState | None,
    dict[str, TypedMemoryRegion],
    dict[str, object],
]:
    initial_state = CPUState()
    initial_register_regions: dict[str, TypedMemoryRegion] = {}
    initial_register_tags: dict[str, object] = {}
    used_initial_state = False

    for seed in seeds:
        register_name = _normalize_register_name(seed.register)
        region = _build_region(
            seed.kind,
            seed.struct_name,
            seed.library_name,
            seed.context_name,
        )
        initial_register_regions[register_name] = region
        if seed.kind == "library_base":
            assert seed.library_name is not None
            assert seed.struct_name is not None
            tag = LibraryBaseTag(
                library_base=seed.library_name,
                struct_name=seed.struct_name,
            )
            initial_register_tags[register_name] = tag
            parsed = parse_reg_name(register_name)
            assert parsed is not None
            mode, reg_num = parsed
            if seed.library_name == runtime_os.META.exec_base_addr.library:
                initial_state.set_reg(
                    mode,
                    reg_num,
                    _concrete(runtime_os.META.exec_base_addr.address, tag=tag),
                )
            else:
                initial_state.set_reg(mode, reg_num, _unknown(tag=tag))
            used_initial_state = True

    return (
        initial_state if used_initial_state else None,
        initial_register_regions,
        initial_register_tags,
    )


def build_entry_seed_config(metadata: TargetMetadata | None) -> EntrySeedConfig:
    seeds = effective_entry_register_seeds(metadata)
    if not seeds:
        return EntrySeedConfig(
            initial_state=None,
            initial_register_regions={},
            initial_register_tags={},
            entry_initial_states={},
            entry_register_regions={},
            entry_register_tags={},
            seed_key="default",
        )

    global_seeds = tuple(seed for seed in seeds if seed.entry_offset is None)
    entry_seed_groups: dict[int, list[object]] = {}
    for seed in seeds:
        if seed.entry_offset is None:
            continue
        entry_seed_groups.setdefault(seed.entry_offset, []).append(seed)

    initial_state, initial_register_regions, initial_register_tags = _build_seed_state(global_seeds)
    entry_initial_states: dict[int, CPUState] = {}
    entry_register_regions: dict[int, dict[str, TypedMemoryRegion]] = {}
    entry_register_tags: dict[int, dict[str, object]] = {}
    for entry_offset, group in entry_seed_groups.items():
        entry_state, entry_regions, entry_tags = _build_seed_state(tuple(group))
        if entry_state is not None:
            entry_initial_states[entry_offset] = entry_state
        if entry_regions:
            entry_register_regions[entry_offset] = entry_regions
        if entry_tags:
            entry_register_tags[entry_offset] = entry_tags

    return EntrySeedConfig(
        initial_state=initial_state,
        initial_register_regions=initial_register_regions,
        initial_register_tags=initial_register_tags,
        entry_initial_states=entry_initial_states,
        entry_register_regions=entry_register_regions,
        entry_register_tags=entry_register_tags,
        seed_key=target_metadata_seed_key(metadata),
    )


def apply_entry_seed_config(platform: PlatformState, seed_config: EntrySeedConfig) -> None:
    platform.initial_register_regions = (
        dict(seed_config.initial_register_regions)
        if seed_config.initial_register_regions
        else None
    )
    platform.initial_register_tags = (
        dict(seed_config.initial_register_tags)
        if seed_config.initial_register_tags
        else None
    )
    platform.entry_register_regions = (
        {
            entry: dict(regions)
            for entry, regions in seed_config.entry_register_regions.items()
        }
        if seed_config.entry_register_regions
        else None
    )


def scoped_entry_initial_states(
    seed_config: EntrySeedConfig,
    entry_points: tuple[int, ...],
) -> dict[int, CPUState]:
    return {
        entry: seed_config.entry_initial_states[entry]
        for entry in entry_points
        if entry in seed_config.entry_initial_states
    }
