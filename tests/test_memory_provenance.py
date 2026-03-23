import pytest

from m68k.memory_provenance import (
    MemoryRegionAddressSpace,
    MemoryRegionDerivation,
    MemoryRegionDerivationKind,
    MemoryRegionProvenance,
    field_pointer_source,
    provenance_base_displacement,
    provenance_field_pointer,
    provenance_named_base,
    require_base_displacement,
)


def test_require_base_displacement_returns_register_and_displacement() -> None:
    provenance = provenance_base_displacement(
        MemoryRegionAddressSpace.APP, "a6", -0x7FF8)

    assert require_base_displacement(
        provenance, expected_space=MemoryRegionAddressSpace.APP) == ("a6", -0x7FF8)


def test_require_base_displacement_rejects_wrong_derivation() -> None:
    provenance = provenance_named_base("dos.library")

    with pytest.raises(ValueError, match="base-displacement provenance"):
        require_base_displacement(provenance)


def test_field_pointer_source_returns_pointer_origin() -> None:
    provenance = provenance_field_pointer("a1", 20)

    assert field_pointer_source(provenance) == ("a1", 20)


def test_field_pointer_source_rejects_missing_payload() -> None:
    provenance = provenance_field_pointer("a1", 20)
    broken = MemoryRegionProvenance(
        address_space=provenance.address_space,
        derivation=MemoryRegionDerivation(
            kind=MemoryRegionDerivationKind.FIELD_POINTER,
            base_register="a1",
            displacement=None,
        ),
    )

    with pytest.raises(ValueError, match="missing register or displacement"):
        field_pointer_source(broken)
