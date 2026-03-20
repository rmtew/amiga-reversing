from __future__ import annotations


def parse_reg_name(name: str) -> tuple[str, int]:
    name = name.strip().upper()
    if len(name) == 2 and name[1].isdigit():
        if name[0] == "D":
            return ("dn", int(name[1]))
        if name[0] == "A":
            return ("an", int(name[1]))
    raise ValueError(f"Cannot parse register name: {name}")
