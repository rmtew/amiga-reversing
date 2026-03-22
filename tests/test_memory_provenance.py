import pytest

from m68k.memory_provenance import (MemoryRegionAddressSpace,
                                    MemoryRegionDerivationKind,
                                    field_pointer_source,
                                    provenance_base_displacement,
                                    provenance_field_pointer,
                                    provenance_named_base,
                                    require_base_displacement)


def test_require_base_displacement_returns_register_and_displacement():
    provenance = provenance_base_displacement(
        MemoryRegionAddressSpace.APP, "a6", -0x7FF8)

    assert require_base_displacement(
        provenance, expected_space=MemoryRegionAddressSpace.APP) == ("a6", -0x7FF8)


def test_require_base_displacement_rejects_wrong_derivation():
    provenance = provenance_named_base("dos.library")

    with pytest.raises(ValueError, match="base-displacement provenance"):
        require_base_displacement(provenance)


def test_field_pointer_source_returns_pointer_origin():
    provenance = provenance_field_pointer("a1", 20)

    assert field_pointer_source(provenance) == ("a1", 20)


def test_field_pointer_source_rejects_missing_payload():
    provenance = provenance_field_pointer("a1", 20)
    broken = provenance.__class__(
        address_space=provenance.address_space,
        derivation=provenance.derivation.__class__(
            kind=MemoryRegionDerivationKind.FIELD_POINTER,
            base_register="a1",
            displacement=None,
        ),
    )

    with pytest.raises(ValueError, match="missing register or displacement"):
        field_pointer_source(broken)
