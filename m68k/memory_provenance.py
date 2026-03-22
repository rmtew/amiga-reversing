from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MemoryRegionAddressSpace(StrEnum):
    APP = "app"
    REGISTER = "register"
    SEGMENT = "segment"
    ABSOLUTE = "absolute"


class MemoryRegionDerivationKind(StrEnum):
    BASE_DISPLACEMENT = "base_displacement"
    NAMED_BASE = "named_base"
    FIELD_POINTER = "field_pointer"


@dataclass(frozen=True, slots=True)
class MemoryRegionDerivation:
    kind: MemoryRegionDerivationKind
    base_register: str | None = None
    displacement: int | None = None
    named_base: str | None = None


@dataclass(frozen=True, slots=True)
class MemoryRegionProvenance:
    address_space: MemoryRegionAddressSpace
    derivation: MemoryRegionDerivation | None = None
    absolute_addr: int | None = None
    segment_addr: int | None = None


def base_displacement_derivation(base_register: str, displacement: int) -> MemoryRegionDerivation:
    return MemoryRegionDerivation(
        kind=MemoryRegionDerivationKind.BASE_DISPLACEMENT,
        base_register=base_register,
        displacement=displacement,
    )


def named_base_derivation(named_base: str) -> MemoryRegionDerivation:
    return MemoryRegionDerivation(
        kind=MemoryRegionDerivationKind.NAMED_BASE,
        named_base=named_base,
    )


def field_pointer_derivation(base_register: str, displacement: int) -> MemoryRegionDerivation:
    return MemoryRegionDerivation(
        kind=MemoryRegionDerivationKind.FIELD_POINTER,
        base_register=base_register,
        displacement=displacement,
    )


def provenance_base_displacement(address_space: MemoryRegionAddressSpace,
                                 base_register: str,
                                 displacement: int) -> MemoryRegionProvenance:
    return MemoryRegionProvenance(
        address_space=address_space,
        derivation=base_displacement_derivation(base_register, displacement),
    )


def provenance_named_base(named_base: str) -> MemoryRegionProvenance:
    return MemoryRegionProvenance(
        address_space=MemoryRegionAddressSpace.REGISTER,
        derivation=named_base_derivation(named_base),
    )


def provenance_field_pointer(base_register: str, displacement: int) -> MemoryRegionProvenance:
    return MemoryRegionProvenance(
        address_space=MemoryRegionAddressSpace.REGISTER,
        derivation=field_pointer_derivation(base_register, displacement),
    )


def require_base_displacement(provenance: MemoryRegionProvenance,
                              *,
                              expected_space: MemoryRegionAddressSpace | None = None
                              ) -> tuple[str, int]:
    if expected_space is not None and provenance.address_space != expected_space:
        raise ValueError(
            f"Expected {expected_space.value} provenance, got {provenance.address_space.value}")
    derivation = provenance.derivation
    if derivation is None or derivation.kind is not MemoryRegionDerivationKind.BASE_DISPLACEMENT:
        raise ValueError("Expected base-displacement provenance")
    if derivation.base_register is None or derivation.displacement is None:
        raise ValueError("Base-displacement provenance missing register or displacement")
    return derivation.base_register, derivation.displacement


def field_pointer_source(provenance: MemoryRegionProvenance) -> tuple[str, int] | None:
    derivation = provenance.derivation
    if derivation is None or derivation.kind is not MemoryRegionDerivationKind.FIELD_POINTER:
        return None
    if derivation.base_register is None or derivation.displacement is None:
        raise ValueError("Field-pointer provenance missing register or displacement")
    return derivation.base_register, derivation.displacement
