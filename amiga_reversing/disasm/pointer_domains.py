"""Contracts for encoded pointer fields and bounded runtime address symbols.

These declarations describe address interpretation, not storage allocation,
DMA read bounds, lifetime, or temporal non-aliasing.
"""


def validate_pointer_domain(
    *, value_kind: str | None, size: int, address_domain: str | None,
    symbol_group: str | None,
) -> None:
    domain = address_domain or "legacy"
    if domain not in {"legacy", "mapped_source", "runtime_only"}:
        raise ValueError("unsupported pointer_address_domain")
    if domain != "legacy" and (value_kind not in {"target_pointer", "struct_pointer"} or size != 4):
        raise ValueError("explicit pointer domain requires a four-byte pointer field")
    if domain == "runtime_only":
        if not isinstance(symbol_group, str) or not symbol_group.strip() or len(symbol_group.encode()) >= 64:
            raise ValueError("runtime_only pointer requires pointer_symbol_group of at most 63 bytes")
    elif symbol_group is not None:
        raise ValueError("pointer_symbol_group requires runtime_only domain")


def validate_runtime_address_symbol(
    *, value: int, group: str | None, address_domain: str | None,
    extent_bytes: int | None, value_expression: str | None = None,
) -> None:
    if address_domain is None:
        if extent_bytes is not None:
            raise ValueError("extent_bytes requires runtime address_domain")
        return
    if value_expression is not None:
        raise ValueError("runtime address symbol cannot declare value_expression")
    if address_domain != "runtime":
        raise ValueError("address symbol domain must be runtime")
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError("runtime address symbol requires unsigned 32-bit value")
    if not isinstance(group, str) or not group.strip() or len(group.encode()) >= 64:
        raise ValueError("runtime address symbol requires group of at most 63 bytes")
    if type(extent_bytes) is not int or not 0 < extent_bytes <= 0xFFFFFFFF or value + extent_bytes > 0x100000000:
        raise ValueError("runtime address symbol extent must fit the 32-bit address space")
