#!/usr/bin/env py.exe
"""Parse IFF format specifications from ADCD 2.1 into structured JSON.

Reads the EA IFF 85 specs and third-party chunk docs from the disc,
extracts struct definitions, chunk descriptions, and format grammar,
and produces a machine-readable JSON knowledge file.

Much of this is hand-encoded from the specs since the documentation
format is free-form prose, not machine-parseable. The script serves
as the single source of truth and can be re-run to regenerate.
"""

import json
import os
import sys
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

JsonDict = dict[str, Any]


def build_iff_base() -> JsonDict:
    """IFF container format (EA IFF 85)."""
    return {
        "description": "EA IFF 85 interchange format — all IFF files use this container",
        "byte_order": "big-endian (Motorola)",
        "chunk_header": {
            "fields": [
                {"name": "ckID", "type": "CHAR[4]", "description": "4-byte ASCII chunk identifier"},
                {"name": "ckSize", "type": "ULONG", "description": "byte count of chunk data (excludes header and pad)"},
            ],
            "size": 8,
            "notes": "Every chunk is padded to even length; pad byte not included in ckSize"
        },
        "group_types": {
            "FORM": "typed data container — FORM type follows immediately after ckSize",
            "LIST": "ordered collection of FORMs, may contain PROP for shared properties",
            "CAT ": "unordered concatenation of FORMs",
            "PROP": "shared properties for all FORMs in a LIST"
        },
        "generic_chunks": {
            "ANNO": {"name": "Annotation", "description": "Free-text annotation string"},
            "AUTH": {"name": "Author", "description": "Author/creator name string"},
            "NAME": {"name": "Name", "description": "Name of art, music, etc."},
            "TEXT": {"name": "Text", "description": "Unformatted ASCII text"},
            "(c) ": {"name": "Copyright", "description": "Copyright notice string"},
            "FVER": {"name": "File Version", "description": "AmigaOS 2.0+ $VER: version string"},
            "JUNK": {"name": "Junk", "description": "Always ignore this chunk (padding/alignment)"},
        }
    }


def build_ilbm() -> JsonDict:
    """ILBM — Interleaved Bitmap (the Amiga standard image format)."""
    return {
        "form_id": "ILBM",
        "name": "Interleaved Bitmap",
        "source": "EA IFF 85",
        "description": "Raster bitmap image with color map, optional mask, and Amiga viewport modes. The standard Amiga image format used by DPaint, PPaint, and virtually all graphics software.",
        "grammar": "FORM ILBM { BMHD [CMAP] [GRAB] [DEST] [SPRT] [CAMG] [CRNG*] [CCRT*] [BODY] }",
        "chunks": {
            "BMHD": {
                "name": "Bitmap Header",
                "required": True,
                "struct_name": "BitMapHeader",
                "struct_size": 20,
                "fields": [
                    {"name": "w", "type": "UWORD", "offset": 0, "description": "raster width in pixels"},
                    {"name": "h", "type": "UWORD", "offset": 2, "description": "raster height in pixels"},
                    {"name": "x", "type": "WORD", "offset": 4, "description": "image position X (pixels)"},
                    {"name": "y", "type": "WORD", "offset": 6, "description": "image position Y (pixels)"},
                    {"name": "nPlanes", "type": "UBYTE", "offset": 8, "description": "number of source bitplanes (depth)"},
                    {"name": "masking", "type": "UBYTE", "offset": 9, "description": "0=none, 1=hasMask, 2=hasTransparentColor, 3=lasso"},
                    {"name": "compression", "type": "UBYTE", "offset": 10, "description": "0=none, 1=byteRun1"},
                    {"name": "pad1", "type": "UBYTE", "offset": 11, "description": "unused, set to 0"},
                    {"name": "transparentColor", "type": "UWORD", "offset": 12, "description": "transparent color number (for masking 2 or 3)"},
                    {"name": "xAspect", "type": "UBYTE", "offset": 14, "description": "pixel aspect ratio width (10 for 320x200)"},
                    {"name": "yAspect", "type": "UBYTE", "offset": 15, "description": "pixel aspect ratio height (11 for 320x200)"},
                    {"name": "pageWidth", "type": "WORD", "offset": 16, "description": "source page width in pixels"},
                    {"name": "pageHeight", "type": "WORD", "offset": 18, "description": "source page height in pixels"},
                ],
            },
            "CMAP": {
                "name": "Color Map",
                "required": False,
                "description": "Color register values as RGB triplets. Count = ckSize / 3.",
                "struct_name": "ColorRegister",
                "struct_size": 3,
                "fields": [
                    {"name": "red", "type": "UBYTE", "offset": 0, "description": "red intensity 0-255"},
                    {"name": "green", "type": "UBYTE", "offset": 1, "description": "green intensity 0-255"},
                    {"name": "blue", "type": "UBYTE", "offset": 2, "description": "blue intensity 0-255"},
                ],
                "notes": "Amiga OCS/ECS has 4-bit DACs — use high nibble only. AGA has 8-bit. n_colors = ckSize / 3, normally 2^nPlanes."
            },
            "GRAB": {
                "name": "Hotspot",
                "required": False,
                "struct_name": "Point2D",
                "struct_size": 4,
                "fields": [
                    {"name": "x", "type": "WORD", "offset": 0, "description": "hotspot X relative to upper-left"},
                    {"name": "y", "type": "WORD", "offset": 2, "description": "hotspot Y relative to upper-left"},
                ],
            },
            "DEST": {
                "name": "Destination Merge",
                "required": False,
                "struct_name": "DestMerge",
                "struct_size": 8,
                "fields": [
                    {"name": "depth", "type": "UBYTE", "offset": 0, "description": "bitplanes in original source"},
                    {"name": "pad1", "type": "UBYTE", "offset": 1},
                    {"name": "planePick", "type": "UWORD", "offset": 2, "description": "scatter source planes into dest (bit per plane)"},
                    {"name": "planeOnOff", "type": "UWORD", "offset": 4, "description": "default data for non-picked planes"},
                    {"name": "planeMask", "type": "UWORD", "offset": 6, "description": "gate: 1=write to this dest plane, 0=leave alone"},
                ],
            },
            "SPRT": {
                "name": "Sprite",
                "required": False,
                "struct_size": 2,
                "fields": [
                    {"name": "precedence", "type": "UWORD", "offset": 0, "description": "sprite precedence (0=foremost)"},
                ],
            },
            "CAMG": {
                "name": "Amiga Viewport Mode",
                "required": False,
                "struct_size": 4,
                "fields": [
                    {"name": "viewModes", "type": "ULONG", "offset": 0, "description": "Amiga viewport mode flags"},
                ],
                "constants": {
                    "HAM": {"value": "0x0800", "description": "Hold-And-Modify mode"},
                    "EHB": {"value": "0x0080", "description": "Extra-Half-Brite mode"},
                    "LACE": {"value": "0x0004", "description": "Interlace mode"},
                    "HIRES": {"value": "0x8000", "description": "High resolution (640 px wide)"},
                    "HAM8": {"value": "0x0800", "description": "HAM8 (AGA, 8 planes)"},
                    "SUPERHIRES": {"value": "0x0020", "description": "Super high resolution (1280 px wide)"},
                    "DUALPF": {"value": "0x0400", "description": "Dual playfield mode"},
                }
            },
            "CRNG": {
                "name": "Color Range",
                "required": False,
                "description": "DPaint color cycling range. Can appear multiple times.",
                "struct_name": "CRange",
                "struct_size": 8,
                "fields": [
                    {"name": "pad1", "type": "WORD", "offset": 0, "description": "reserved, set to 0"},
                    {"name": "rate", "type": "WORD", "offset": 2, "description": "color cycle rate (16384 = 60 steps/sec)"},
                    {"name": "active", "type": "WORD", "offset": 4, "description": "nonzero = cycling enabled"},
                    {"name": "low", "type": "UBYTE", "offset": 6, "description": "lower color register"},
                    {"name": "high", "type": "UBYTE", "offset": 7, "description": "upper color register"},
                ],
            },
            "CCRT": {
                "name": "Color Cycling Range and Timing",
                "required": False,
                "description": "Graphicraft color cycling. Alternative to CRNG.",
                "struct_name": "CycleInfo",
                "struct_size": 14,
                "fields": [
                    {"name": "direction", "type": "WORD", "offset": 0, "description": "0=don't cycle, 1=forward, -1=backward"},
                    {"name": "start", "type": "UBYTE", "offset": 2, "description": "lower color register"},
                    {"name": "end", "type": "UBYTE", "offset": 3, "description": "upper color register"},
                    {"name": "seconds", "type": "LONG", "offset": 4, "description": "seconds between color changes"},
                    {"name": "microseconds", "type": "LONG", "offset": 8, "description": "microseconds between color changes"},
                    {"name": "pad", "type": "WORD", "offset": 12, "description": "reserved, set to 0"},
                ],
            },
            "BODY": {
                "name": "Image Body",
                "required": True,
                "description": "Interleaved bitplane data. Each scan line = nPlanes rows (+ mask row if masking=1), each row = ceil(w/16) words. Rows may be ByteRun1 compressed.",
            },
        },
        "compression": {
            "byteRun1": {
                "id": 1,
                "description": "PackBits-style run-length encoding, applied per row",
                "algorithm": [
                    "Read next signed byte n",
                    "If 0 <= n <= 127: copy next n+1 bytes literally",
                    "If -127 <= n <= -1: replicate next byte (-n+1) times",
                    "If n == -128: no-op (skip)",
                    "Repeat until row complete"
                ],
            }
        },
        "raster_layout": {
            "description": "Bitplanes interleaved by row. Plane 0 = low-order bit of color index.",
            "row_width_bytes": "ceil(w / 16) * 2",
            "scan_line_order": "plane 0 row, plane 1 row, ..., plane N-1 row, [mask row]",
            "pixel_order": "left to right, MSB first within each byte",
        }
    }


def build_8svx() -> JsonDict:
    """8SVX — 8-bit Sampled Voice."""
    return {
        "form_id": "8SVX",
        "name": "8-Bit Sampled Voice",
        "source": "EA IFF 85",
        "description": "8-bit audio sample, either one-shot sound or multi-octave musical instrument with optional envelope.",
        "grammar": "FORM 8SVX { VHDR [NAME] [(c) ] [AUTH] [ANNO*] [ATAK] [RLSE] BODY }",
        "chunks": {
            "VHDR": {
                "name": "Voice Header",
                "required": True,
                "struct_name": "Voice8Header",
                "struct_size": 20,
                "fields": [
                    {"name": "oneShotHiSamples", "type": "ULONG", "offset": 0, "description": "samples in high octave one-shot part"},
                    {"name": "repeatHiSamples", "type": "ULONG", "offset": 4, "description": "samples in high octave repeat part"},
                    {"name": "samplesPerHiCycle", "type": "ULONG", "offset": 8, "description": "samples/cycle in high octave (0=unknown)"},
                    {"name": "samplesPerSec", "type": "UWORD", "offset": 12, "description": "sampling rate in Hz"},
                    {"name": "ctOctave", "type": "UBYTE", "offset": 14, "description": "number of octaves of waveform data"},
                    {"name": "sCompression", "type": "UBYTE", "offset": 15, "description": "0=none, 1=fibDelta"},
                    {"name": "volume", "type": "Fixed", "offset": 16, "description": "playback volume, Fixed 16.16 (0x10000=full)"},
                ],
            },
            "BODY": {
                "name": "Sample Data",
                "required": True,
                "description": "Signed 8-bit samples (-128..127). Highest octave first, each successive octave has 2x samples. Total = (2^0 + ... + 2^(ctOctave-1)) * (oneShotHiSamples + repeatHiSamples).",
            },
            "ATAK": {
                "name": "Attack Envelope",
                "required": False,
                "description": "Piecewise-linear attack contour. Array of EGPoint, count = ckSize / 6.",
                "struct_name": "EGPoint",
                "struct_size": 6,
                "fields": [
                    {"name": "duration", "type": "UWORD", "offset": 0, "description": "segment duration in milliseconds"},
                    {"name": "dest", "type": "Fixed", "offset": 2, "description": "destination volume factor (Fixed 16.16)"},
                ],
            },
            "RLSE": {
                "name": "Release Envelope",
                "required": False,
                "description": "Piecewise-linear release contour. Same format as ATAK.",
                "struct_name": "EGPoint",
                "struct_size": 6,
                "fields": [
                    {"name": "duration", "type": "UWORD", "offset": 0, "description": "segment duration in milliseconds"},
                    {"name": "dest", "type": "Fixed", "offset": 2, "description": "destination volume factor (Fixed 16.16)"},
                ],
            },
            "CHAN": {
                "name": "Channel Assignment",
                "required": False,
                "struct_size": 4,
                "fields": [
                    {"name": "sampletype", "type": "LONG", "offset": 0, "description": "2=LEFT, 4=RIGHT, 6=STEREO"},
                ],
                "notes": "Stereo: BODY contains LEFT then RIGHT data, equal length."
            },
            "PAN": {
                "name": "Stereo Panning",
                "required": False,
                "struct_size": 4,
                "fields": [
                    {"name": "sposition", "type": "Fixed", "offset": 0, "description": "stereo position: 0=right, Unity(0x10000)=left, Unity/2=center"},
                ],
            },
        },
        "compression": {
            "fibDelta": {
                "id": 1,
                "description": "Fibonacci-delta encoding — 4 bits per sample, halves data size",
                "delta_table": [-34, -21, -13, -8, -5, -3, -2, -1, 0, 1, 2, 3, 5, 8, 13, 21],
                "algorithm": [
                    "First 2 bytes: pad byte + initial 8-bit value",
                    "Remaining bytes: each byte holds 2 nybbles (high first)",
                    "Each nybble indexes delta_table, delta added to running value",
                    "Output: 2*(n-2) samples from n input bytes"
                ],
            }
        },
    }


def build_anim() -> JsonDict:
    """ANIM — Cel Animation."""
    return {
        "form_id": "ANIM",
        "name": "Cel Animation",
        "source": "SPARTA Inc. / Aegis Development",
        "description": "Animated sequence of ILBM frames. First frame is full ILBM, subsequent frames are delta-compressed differences. Uses double-buffering playback (each delta modifies frame 2 back).",
        "grammar": "FORM ANIM { FORM ILBM(frame1) [FORM ILBM(frame2..N)]* }",
        "structure": [
            "Frame 1: Full FORM ILBM with BMHD, CMAP, BODY (+ optional ANHD for timing)",
            "Frame 2: FORM ILBM with ANHD + DLTA (delta from frame 1)",
            "Frame 3+: FORM ILBM with ANHD + DLTA (delta from 2 frames back)",
            "Looping: last 2 frames duplicate first 2 frames",
        ],
        "chunks": {
            "ANHD": {
                "name": "Animation Header",
                "required": True,
                "description": "Per-frame animation parameters. Replaces BMHD in delta frames.",
                "struct_size": 24,
                "fields": [
                    {"name": "operation", "type": "UBYTE", "offset": 0, "description": "compression method: 0=direct, 1=XOR, 2=longDelta, 3=shortDelta, 4=generalDelta, 5=byteVertical, 6=stereo5, 74('J')=reserved(Eric Graham)"},
                    {"name": "mask", "type": "UBYTE", "offset": 1, "description": "XOR mode: plane mask (bit set = has data)"},
                    {"name": "w", "type": "UWORD", "offset": 2, "description": "XOR mode: width of delta area"},
                    {"name": "h", "type": "UWORD", "offset": 4, "description": "XOR mode: height of delta area"},
                    {"name": "x", "type": "WORD", "offset": 6, "description": "XOR mode: X position of delta area"},
                    {"name": "y", "type": "WORD", "offset": 8, "description": "XOR mode: Y position of delta area"},
                    {"name": "abstime", "type": "ULONG", "offset": 10, "description": "absolute time from first frame (1/60 sec jiffies)"},
                    {"name": "reltime", "type": "ULONG", "offset": 14, "description": "time since previous frame (1/60 sec jiffies)"},
                    {"name": "interleave", "type": "UBYTE", "offset": 18, "description": "frames back to modify (0=default=2 for double-buffering)"},
                    {"name": "pad0", "type": "UBYTE", "offset": 19},
                    {"name": "bits", "type": "ULONG", "offset": 20, "description": "option bits for methods 4&5"},
                ],
                "option_bits": {
                    "0": "0=short data, 1=long data",
                    "1": "0=set, 1=XOR",
                    "2": "0=separate info per plane, 1=one info list for all planes",
                    "3": "0=not RLC, 1=run-length coded",
                    "4": "0=horizontal, 1=vertical",
                    "5": "0=short info offsets, 1=long info offsets",
                },
            },
            "DLTA": {
                "name": "Delta Data",
                "required": True,
                "description": "Frame difference data. Format depends on ANHD.operation.",
                "methods": {
                    "1": {
                        "name": "XOR",
                        "description": "XOR between current and 2-frames-back, stored as ByteRun1 in BODY chunk"
                    },
                    "2": {
                        "name": "Long Delta",
                        "description": "Changed longwords with offsets. 8 LONG pointers to per-plane data. Positive offset = skip + 1 longword. Negative offset = -(offset+2) then count + N contiguous longwords. Terminates with 0xFFFF."
                    },
                    "3": {
                        "name": "Short Delta",
                        "description": "Same as method 2 but with WORD-sized data instead of LONG."
                    },
                    "4": {
                        "name": "General Delta",
                        "description": "16 LONG pointers: 8 data + 8 offset/count lists. Supports short/long, horizontal/vertical, set/XOR, RLC options via ANHD.bits."
                    },
                    "5": {
                        "name": "Byte Vertical (Jim Kent)",
                        "description": "16 LONG pointers (first 8 used). Per-plane, per-column compression. Each column: op-count byte, then ops: skip (0x01-0x7F), uniq (0x80|count + literal bytes), same (0x00 + count + fill byte). Dest advances by bytes_per_row.",
                        "ops": [
                            {"name": "skip", "byte_range": "0x01-0x7F", "description": "skip N rows (advance dest by N * bytesPerRow)"},
                            {"name": "uniq", "byte_range": "0x80-0xFF", "description": "copy (byte & 0x7F) literal bytes"},
                            {"name": "same", "byte_range": "0x00", "description": "next byte = count, then byte = fill value, repeat count times"},
                        ],
                    },
                },
            },
        },
        "playback": {
            "buffers": 2,
            "method": "Double-buffered: display A, modify B with delta, flip. Delta for frame N modifies frame N-2.",
            "timing": "ANHD.reltime in jiffies (1/60 sec). Use VBlank interrupt for timing.",
        },
    }


def build_acbm() -> JsonDict:
    """ACBM — Amiga Contiguous Bitmap."""
    return {
        "form_id": "ACBM",
        "name": "Amiga Contiguous Bitmap",
        "source": "Carolyn Scheppner, CBM",
        "description": "Like ILBM but with contiguous (non-interleaved) bitplane data. Faster loading from AmigaBasic. Uses ABIT chunk instead of BODY.",
        "grammar": "FORM ACBM { BMHD [CMAP] ABIT }",
        "chunks": {
            "BMHD": {"name": "Bitmap Header", "description": "Same as ILBM BMHD"},
            "CMAP": {"name": "Color Map", "description": "Same as ILBM CMAP"},
            "ABIT": {
                "name": "Amiga Bitplanes",
                "required": True,
                "description": "Contiguous bitplane data: all of plane 0, then all of plane 1, etc. Each plane = h * ceil(w/16) * 2 bytes.",
            },
        },
    }


def build_registry(registry_path: str) -> dict[str, JsonDict]:
    """Parse the FORM/chunk registry file."""
    entries: dict[str, JsonDict] = {}
    if not os.path.exists(registry_path):
        return entries

    with open(registry_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip()
            if not line or line.startswith(" ") and "IFF FORM" in line:
                continue
            # Format: "NAME              \tSOURCE\tDescription"
            # or "(any).CHUNK       \tSOURCE\tDescription"
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[0].strip()
                if not name or name.startswith(("The ", "additional")):
                    continue
                source = parts[1].strip() if len(parts) > 1 else ""
                desc = parts[2].strip() if len(parts) > 2 else ""
                entries[name] = {"source": source, "description": desc}

    return entries


def main() -> None:
    output_path = os.path.join("knowledge", "amiga_iff_formats.json")
    registry_path = "D:/EXTRAS/IFF/IFF_FORMS/REGISTRY_930210"

    print("Building IFF format knowledge base...")

    # Build the full structure
    data: JsonDict = {
        "meta": {
            "description": "IFF interchange format specifications for Amiga",
            "sources": [
                "EA IFF 85 specification (Electronic Arts, 1985)",
                "ILBM specification (Jerry Morrison, EA, 1986)",
                "8SVX specification (Steve Hayes & Jerry Morrison, EA, 1985)",
                "ANIM specification (SPARTA Inc. & Aegis Development, 1988)",
                "ADCD 2.1: D:/EXTRAS/IFF/IFF_FORMS/ and D:/EXTRAS/IFF/OLD_IFF_PACKAGES/",
                "Third-party chunk specifications from IFF_FORMS directory",
            ],
            "type_sizes": {
                "UBYTE": 1, "BYTE": 1, "CHAR": 1,
                "UWORD": 2, "WORD": 2,
                "ULONG": 4, "LONG": 4,
                "Fixed": 4,
            },
            "type_descriptions": {
                "Fixed": "16.16 fixed-point: 16 bits integer + 16 bits fraction. Unity = 0x10000 = 1.0",
            }
        },
        "iff_container": build_iff_base(),
        "forms": {
            "ILBM": build_ilbm(),
            "8SVX": build_8svx(),
            "ANIM": build_anim(),
            "ACBM": build_acbm(),
        },
        "registry": build_registry(registry_path),
    }

    # Count stats
    n_forms = len(data["forms"])
    n_chunks = sum(len(f.get("chunks", {})) for f in data["forms"].values())
    n_fields = sum(
        len(c.get("fields", []))
        for f in data["forms"].values()
        for c in f.get("chunks", {}).values()
    )
    n_registry = len(data["registry"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  {n_forms} FORM types, {n_chunks} chunk types, {n_fields} struct fields")
    print(f"  {n_registry} registered FORM/chunk IDs from registry")
    print(f"Wrote {output_path}")

    # Also generate human-readable reference
    md_path = os.path.join("knowledge", "amiga_iff_reference.md")
    generate_markdown(data, md_path)
    print(f"Wrote {md_path}")


def generate_markdown(data: JsonDict, md_path: str) -> None:
    """Generate human-readable IFF reference from JSON data."""
    lines = []
    lines.append("# Amiga IFF Format Reference")
    lines.append("")
    lines.append("Auto-generated from `scripts/parse_iff_specs.py`. See `amiga_iff_formats.json` for machine-readable version.")
    lines.append("")

    # IFF container
    lines.append("## IFF Container (EA IFF 85)")
    lines.append("")
    lines.append("Byte order: **big-endian** (Motorola)")
    lines.append("")
    lines.append("### Chunk Header (8 bytes)")
    lines.append("| Offset | Type | Field | Description |")
    lines.append("|--------|------|-------|-------------|")
    lines.append("| 0 | CHAR[4] | ckID | 4-byte ASCII chunk identifier |")
    lines.append("| 4 | ULONG | ckSize | data byte count (excludes header + pad) |")
    lines.append("")
    lines.append("Every chunk padded to even length. Groups: FORM (typed container), LIST (ordered collection), CAT (unordered), PROP (shared properties).")
    lines.append("")

    # Generic chunks
    lines.append("### Generic Chunks (valid in any FORM)")
    lines.append("| ID | Name | Description |")
    lines.append("|----|------|-------------|")
    for cid, info in data["iff_container"]["generic_chunks"].items():
        lines.append(f"| {cid} | {info['name']} | {info['description']} |")
    lines.append("")

    # Each FORM
    for form_id, form in data["forms"].items():
        lines.append(f"## FORM {form_id} — {form['name']}")
        lines.append("")
        lines.append(form["description"])
        lines.append("")
        if "grammar" in form:
            lines.append(f"Grammar: `{form['grammar']}`")
            lines.append("")
        if "structure" in form:
            for s in form["structure"]:
                lines.append(f"- {s}")
            lines.append("")

        for chunk_id, chunk in form.get("chunks", {}).items():
            req = " (required)" if chunk.get("required") else ""
            lines.append(f"### {chunk_id} — {chunk.get('name', chunk_id)}{req}")
            lines.append("")
            if "description" in chunk:
                lines.append(chunk["description"])
                lines.append("")

            if "fields" in chunk:
                lines.append(f"Struct: `{chunk.get('struct_name', chunk_id)}` ({chunk.get('struct_size', '?')} bytes)")
                lines.append("")
                lines.append("| Offset | Type | Field | Description |")
                lines.append("|--------|------|-------|-------------|")
                for fld in chunk["fields"]:
                    off = fld.get("offset", "?")
                    desc = fld.get("description", "")
                    lines.append(f"| {off} | {fld['type']} | {fld['name']} | {desc} |")
                lines.append("")

            if "constants" in chunk:
                lines.append("Constants:")
                lines.append("")
                for name, info in chunk["constants"].items():
                    lines.append(f"- `{name}` = {info['value']} — {info['description']}")
                lines.append("")

            if "option_bits" in chunk:
                lines.append("Option bits (ANHD.bits):")
                lines.append("")
                for bit, desc in chunk["option_bits"].items():
                    lines.append(f"- Bit {bit}: {desc}")
                lines.append("")

            if "methods" in chunk:
                lines.append("Delta compression methods:")
                lines.append("")
                for mid, method in chunk["methods"].items():
                    lines.append(f"**Method {mid}: {method['name']}**")
                    lines.append(f"  {method['description']}")
                    if "ops" in method:
                        for op in method["ops"]:
                            lines.append(f"  - `{op['byte_range']}` {op['name']}: {op['description']}")
                    lines.append("")

            if "notes" in chunk:
                lines.append(f"*{chunk['notes']}*")
                lines.append("")

        # Compression algorithms
        if "compression" in form:
            lines.append("### Compression")
            lines.append("")
            for name, comp in form["compression"].items():
                lines.append(f"**{name}** (id={comp['id']}): {comp['description']}")
                lines.append("")
                if "algorithm" in comp:
                    for step in comp["algorithm"]:
                        lines.append(f"  {step}")
                    lines.append("")
                if "delta_table" in comp:
                    lines.append(f"  Delta table: `{comp['delta_table']}`")
                    lines.append("")

        # Raster layout
        if "raster_layout" in form:
            rl = form["raster_layout"]
            lines.append("### Raster Layout")
            lines.append("")
            lines.append(f"{rl['description']}")
            lines.append(f"- Row width: `{rl['row_width_bytes']}` bytes")
            lines.append(f"- Scan line: {rl['scan_line_order']}")
            lines.append(f"- Pixel order: {rl['pixel_order']}")
            lines.append("")

        # Playback info
        if "playback" in form:
            pb = form["playback"]
            lines.append("### Playback")
            lines.append("")
            lines.append(f"- Buffers: {pb['buffers']}")
            lines.append(f"- Method: {pb['method']}")
            lines.append(f"- Timing: {pb['timing']}")
            lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
