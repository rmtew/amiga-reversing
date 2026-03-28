from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from m68k_kb.runtime_os import OsConstant, OsValueDomain


class _ValueDomainKb(Protocol):
    @property
    def VALUE_DOMAINS(self) -> Mapping[str, OsValueDomain]: ...

    @property
    def CONSTANTS(self) -> Mapping[str, OsConstant]: ...


@dataclass(frozen=True, slots=True)
class ResolvedValueDomainExpression:
    names: tuple[str, ...]
    raw_remainder: int | None = None

    @property
    def text(self) -> str:
        parts = list(self.names)
        if self.raw_remainder is not None:
            parts.append(f"${self.raw_remainder:X}")
        return "|".join(parts)


def _exact_value_matches(
    *,
    domain_name: str,
    value: int,
    domain: OsValueDomain,
    constants: Mapping[str, OsConstant],
) -> tuple[str, ...]:
    matches: list[str] = []
    for constant_name in domain.members:
        constant = constants.get(constant_name)
        if constant is None:
            raise KeyError(
                f"Missing constant {constant_name} for value domain {domain_name}"
            )
        if constant.value is None:
            raise ValueError(
                f"Non-concrete constant {constant_name} in value domain {domain_name}"
            )
        if constant.value == value:
            matches.append(constant_name)
    return tuple(matches)


def resolve_value_domain_expression(
    os_kb: _ValueDomainKb,
    domain_name: str,
    value: int,
) -> ResolvedValueDomainExpression | None:
    domain = os_kb.VALUE_DOMAINS.get(domain_name)
    if domain is None:
        raise KeyError(f"Missing value domain {domain_name}")
    exact_matches = _exact_value_matches(
        domain_name=domain_name,
        value=value,
        domain=domain,
        constants=os_kb.CONSTANTS,
    )
    if exact_matches:
        if len(exact_matches) > 1:
            if domain.exact_match_policy == "canonical_by_member_order":
                return ResolvedValueDomainExpression((exact_matches[0],))
            raise ValueError(
                f"Ambiguous value-domain match for {domain_name}={value}: {list(exact_matches)}"
            )
        return ResolvedValueDomainExpression(exact_matches)

    if value == 0 and domain.zero_name is not None:
        if domain.zero_name not in os_kb.CONSTANTS:
            raise KeyError(
                f"Missing zero_name constant {domain.zero_name} for value domain {domain_name}"
            )
        return ResolvedValueDomainExpression((domain.zero_name,))

    if domain.kind != "flags":
        return None
    if domain.composition != "bit_or":
        raise ValueError(
            f"Unsupported value-domain composition for {domain_name}: {domain.composition!r}"
        )
    if value == 0:
        return None

    flag_values: list[tuple[int, str]] = []
    for constant_name in domain.members:
        constant = os_kb.CONSTANTS.get(constant_name)
        if constant is None:
            raise KeyError(
                f"Missing constant {constant_name} for value domain {domain_name}"
            )
        if constant.value is None:
            raise ValueError(
                f"Non-concrete constant {constant_name} in value domain {domain_name}"
            )
        constant_value = constant.value
        if constant_value <= 0:
            continue
        flag_values.append((constant_value, constant_name))
    remaining = value
    names: list[str] = []
    for constant_value, constant_name in flag_values:
        if remaining & constant_value != constant_value:
            continue
        names.append(constant_name)
        remaining &= ~constant_value
        if remaining == 0:
            break
    if remaining != 0:
        if domain.remainder_policy == "append_hex" and names:
            return ResolvedValueDomainExpression(tuple(names), raw_remainder=remaining)
        raise ValueError(
            f"No complete flag decomposition for {domain_name}={value} "
            f"(remaining 0x{remaining:X})"
        )
    if not names:
        return None
    return ResolvedValueDomainExpression(tuple(names))
