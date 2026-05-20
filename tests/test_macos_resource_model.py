from __future__ import annotations

from amiga_reversing.disasm.macos_resource_model import (
    build_resource_xrefs,
    parse_resource_constants,
    parse_rez_source,
)

SAMPLE_H = """
#define rMenuBar 128
#define rAboutAlert 128
#define rUserAlert 129
#define rWindow 128
#define rStopRect 128
#define rGoRect 129
#define mApple 128
#define mFile 129
#define mEdit 130
#define mLight 131
#define kMinSize 23
#define kPrefSize 35
"""


SAMPLE_INC1 = """
rMenuBar EQU 128
rUserAlert EQU 129
rWindow EQU 128
rAboutAlert EQU 128
rStopRect EQU 128
rGoRect EQU 129
MinHeap EQU 21*1024
MinSpace EQU 8*1024
"""


SAMPLE_R = """
type 'RECT' {
    rect;
};

resource 'MBAR' (rMenuBar, preload) {
};
resource 'MENU' (mApple, preload) {
};
resource 'ALRT' (rAboutAlert, purgeable) {
};
resource 'DITL' (rAboutAlert, purgeable) {
};
resource 'ALRT' (rUserAlert, purgeable) {
};
resource 'DITL' (rUserAlert, purgeable) {
};
resource 'WIND' (rWindow, preload, purgeable) {
};
resource 'RECT' (rStopRect, preload, purgeable) {
};
resource 'RECT' (rGoRect, preload, purgeable) {
};
resource 'SIZE' (-1) {
};
"""


def _constants_by_name() -> dict[str, dict[str, object]]:
    parsed = parse_resource_constants(SAMPLE_H, SAMPLE_INC1)
    return parsed["by_name"]


def _resources() -> list[dict[str, object]]:
    parsed = parse_rez_source(
        SAMPLE_R,
        path="MPW-GM/MPW/Examples/AExamples/Sample.r",
        constants=_constants_by_name(),
    )
    return parsed["resources"]


def test_sample_r_resource_inventory_resolves_symbolic_ids_and_attributes() -> None:
    parsed = parse_rez_source(
        SAMPLE_R,
        path="MPW-GM/MPW/Examples/AExamples/Sample.r",
        constants=_constants_by_name(),
    )

    assert parsed["type_declarations"] == [{"type": "RECT", "line": 2}]
    resources = {
        (resource["type"], resource["symbolic_id"] or resource["id_expression"]): resource
        for resource in parsed["resources"]
    }
    assert resources[("MBAR", "rMenuBar")]["numeric_id"] == 128
    assert resources[("MBAR", "rMenuBar")]["attributes"] == ["preload"]
    assert resources[("ALRT", "rUserAlert")]["numeric_id"] == 129
    assert resources[("WIND", "rWindow")]["attributes"] == ["preload", "purgeable"]
    assert resources[("RECT", "rStopRect")]["numeric_id"] == 128
    assert resources[("RECT", "rGoRect")]["numeric_id"] == 129
    assert resources[("SIZE", "-1")]["numeric_id"] == -1
    assert all(resource["initial_type"] is True for resource in parsed["resources"])


def test_sample_h_and_inc1_constants_resolve_resource_ids() -> None:
    parsed = parse_resource_constants(SAMPLE_H, SAMPLE_INC1)
    by_name = parsed["by_name"]

    assert by_name["rWindow"]["value"] == 128
    assert by_name["rWindow"]["asm_value"] == 128
    assert by_name["rUserAlert"]["value"] == 129
    assert by_name["rUserAlert"]["asm_value"] == 129
    assert by_name["MinHeap"]["value"] == 21 * 1024
    assert by_name["MinSpace"]["value"] == 8 * 1024


def test_unknown_symbolic_resource_ids_stay_unresolved() -> None:
    parsed = parse_rez_source(
        """
resource 'RECT' (rMissingRect) {
};
resource 'WIND' (rWindow + kOffset) {
};
""",
        path="Sample.r",
        constants={},
    )

    assert parsed["resources"][0]["symbolic_id"] == "rMissingRect"
    assert parsed["resources"][0]["numeric_id"] is None
    assert parsed["resources"][1]["symbolic_id"] == "rWindow + kOffset"
    assert parsed["resources"][1]["numeric_id"] is None


def test_resource_xrefs_connect_sample_call_sites_to_resource_declarations() -> None:
    xrefs = build_resource_xrefs(
        {
            "Sample.a": "\n".join(
                [
                    "\tMOVE.W #rWindow,-(SP)",
                    "\t_GetNewWindow",
                    "\tMOVE.W #rMenuBar,-(SP)",
                    "\t_GetNewMBar",
                    "\tMOVE.W #rStopRect,-(SP)",
                    "\tBSR GoGetRect",
                    "\tMOVE.W #rGoRect,-(SP)",
                    "\tBSR GoGetRect",
                    "\tMOVE.W #rAboutAlert,-(SP)",
                    "\t_Alert",
                ]
            ),
            "SampleMisc.a": "\n".join(
                [
                    "\tMOVE.L #'RECT',-(SP)",
                    "\tMOVE.W RectID(A6),-(SP)",
                    "\t_GetResource",
                    "\tMOVE.W #rUserAlert,-(SP)",
                    "\t_Alert",
                ]
            ),
        },
        _resources(),
        _constants_by_name(),
    )

    keyed = {(xref["call"], xref.get("symbolic_id")): xref for xref in xrefs if xref.get("symbolic_id")}
    assert keyed[("_GetNewWindow", "rWindow")]["resource"]["type"] == "WIND"
    assert keyed[("_GetNewMBar", "rMenuBar")]["resource"]["type"] == "MBAR"
    assert keyed[("GoGetRect", "rStopRect")]["resource"]["type"] == "RECT"
    assert keyed[("GoGetRect", "rGoRect")]["resource"]["numeric_id"] == 129
    assert keyed[("_Alert", "rAboutAlert")]["resource"]["type"] == "ALRT"
    assert keyed[("_Alert", "rUserAlert")]["resource"]["numeric_id"] == 129
    get_resource = [xref for xref in xrefs if xref["call"] == "_GetResource"][0]
    assert get_resource["resource_type"] == "RECT"
    assert get_resource["id_source"] == "caller_supplied_parameter"
    assert get_resource["resource"] is None


def test_unknown_resource_xref_symbol_stays_unresolved() -> None:
    xrefs = build_resource_xrefs(
        {"Sample.a": "\tMOVE.W #rMissingRect,-(SP)\n\tBSR GoGetRect\n"},
        [],
        {},
    )

    assert xrefs == [
        {
            "source": "Sample.a",
            "line": 2,
            "call": "GoGetRect",
            "symbolic_id": "rMissingRect",
            "numeric_id": None,
            "resource": None,
        }
    ]


def test_count_r_cmdo_smoke_inventory() -> None:
    parsed = parse_rez_source(
        """
#include "Cmdo.r"
resource 'cmdo' (128) {
};
""",
        path="MPW-GM/MPW/Examples/AExamples/Count.r",
    )

    assert parsed["resources"] == [
        {
            "type": "cmdo",
            "symbolic_id": None,
            "id_expression": "128",
            "numeric_id": 128,
            "attributes": [],
            "line": 3,
            "line_end": 4,
            "source": "MPW-GM/MPW/Examples/AExamples/Count.r",
            "initial_type": True,
        }
    ]
