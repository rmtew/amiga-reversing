#!/usr/bin/env py.exe
"""Parse OS_CHANGES files from ADCD 2.1 to build a function→version map.

Input: OS_CHANGES directory with files like "1.3_TO_2.04", "2.04_TO_2.1", etc.
Output: JSON mapping each library/function to the OS version it was introduced.

Can be used standalone or to augment amiga_os_reference.json with version info.
"""

import os
import re
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

def parse_change_file(path: str) -> dict:
    """Parse a single OS_CHANGES file.

    Returns dict with keys:
        added: {lib_name: [func_names]}     - new libraries
        new:   {lib_name: [func_names]}     - new functions in existing libraries
        removed: {lib_name: [func_names]}   - removed libraries/functions
    """
    result = {"added": {}, "new": {}, "removed": {}}

    with open(path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Split into sections: "Added in X.Y:", "Removed in X.Y:", "New functions in X.Y:"
    sections = re.split(r'\n(?=(?:Added|Removed|New functions) in )', content)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Determine section type
        header_m = re.match(r'(Added|Removed|New functions) in ([\d.]+):', section)
        if not header_m:
            continue

        section_type = header_m.group(1).lower()
        # version = header_m.group(2)  # already encoded in filename

        if section_type == "added":
            target = result["added"]
        elif section_type == "removed":
            target = result["removed"]
        else:  # "new functions"
            target = result["new"]

        # Parse library/function entries
        current_lib = None
        for line in section.split('\n')[1:]:  # skip header
            if not line.strip():
                continue

            # Count leading tabs to distinguish:
            #   1 tab = library name
            #   2 tabs = function name
            #   >2 tabs or spaces after tab = continuation/note text
            tabs = len(line) - len(line.lstrip('\t'))

            stripped = line.strip()

            # Library/device/resource name (1 tab indent, contains a dot)
            if tabs == 1 and not stripped.endswith('()') and '.' in stripped:
                # Strip parenthetical notes: "amigaguide.library (Note: ...)"
                lib_name = re.match(r'(\S+)', stripped).group(1)
                current_lib = lib_name
                if current_lib not in target:
                    target[current_lib] = []
                continue

            # Function name (2 tab indent, ends with "()")
            if tabs >= 2 and stripped.endswith('()') and current_lib:
                func_name = stripped.rstrip('()')
                target[current_lib].append(func_name)

    return result


def build_version_map(os_changes_dir: str) -> dict:
    """Build complete function→version mapping from all change files.

    Returns:
        {
            "libraries": {
                "lib.name": {
                    "added_in": "2.04",  // when the library itself was introduced
                    "functions": {
                        "FuncName": {"since": "2.04", "status": "added"},
                        ...
                    }
                }
            },
            "removed": {
                "lib.name": {
                    "removed_in": "2.04",
                    "functions": ["FuncName", ...]
                }
            }
        }
    """
    # Map filenames to version transitions
    change_files = [
        ("1.3_TO_2.04", "2.04"),
        ("2.04_TO_2.1", "2.1"),
        ("2.1_TO_3.0", "3.0"),
        ("3.0_TO_3.1", "3.1"),
    ]

    libraries = {}
    removed = {}

    for filename, version in change_files:
        path = os.path.join(os_changes_dir, filename)
        if not os.path.exists(path):
            print(f"  Warning: {path} not found, skipping")
            continue

        changes = parse_change_file(path)

        # New libraries added in this version
        for lib_name, funcs in changes["added"].items():

            if lib_name not in libraries:
                libraries[lib_name] = {"added_in": version, "functions": {}}
            else:
                # Library existed before but is listed as "added" (re-added?)
                libraries[lib_name]["added_in"] = version
            for func in funcs:
                libraries[lib_name]["functions"][func] = version

        # New functions added to existing libraries
        for lib_name, funcs in changes["new"].items():

            if lib_name not in libraries:
                # Library existed before this version (pre-existing)
                libraries[lib_name] = {"added_in": "pre-existing", "functions": {}}
            for func in funcs:
                libraries[lib_name]["functions"][func] = version

        # Removed libraries/functions
        for lib_name, funcs in changes["removed"].items():

            if lib_name not in removed:
                removed[lib_name] = {"removed_in": version, "functions": funcs}
            else:
                removed[lib_name]["functions"].extend(funcs)

    return {"libraries": libraries, "removed": removed}


def apply_to_os_reference(version_map: dict, ref_path: str, output_path: str):
    """Apply version info to existing amiga_os_reference.json."""
    with open(ref_path, encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    new_entries = 0

    # Apply version info to existing functions
    for lib_key, lib_data in data["libraries"].items():
        # Normalize library name for matching
        lib_lower = lib_key.lower()

        # Find matching version map entry
        vm_entry = None
        for vm_lib in version_map["libraries"]:
            if vm_lib.lower() == lib_lower:
                vm_entry = version_map["libraries"][vm_lib]
                break

        if vm_entry:
            # Tag existing functions that appear in the version map
            existing_names = {f["name"] for f in lib_data["functions"]}
            for func in lib_data["functions"]:
                if func["name"] in vm_entry["functions"]:
                    func["since"] = vm_entry["functions"][func["name"]]
                    updated += 1

            # Add post-1.3 functions to existing libraries
            for func_name, func_ver in vm_entry["functions"].items():
                if func_name not in existing_names:
                    lib_data["functions"].append({
                        "name": func_name,
                        "lvo": None,  # unknown without later NDK FD files
                        "since": func_ver,
                    })
                    new_entries += 1

    # Collect new libraries not in our 1.3 reference
    later_additions = {}
    for lib_name, lib_info in version_map["libraries"].items():
        lib_lower = lib_name.lower()
        found = any(k.lower() == lib_lower for k in data["libraries"])
        if not found:
            later_additions[lib_name] = {
                "added_in": lib_info.get("added_in", "?"),
                "function_count": len(lib_info["functions"]),
                "functions": {f: v for f, v in lib_info["functions"].items()},
            }
            new_entries += len(lib_info["functions"])

    # Store version map and later additions in meta
    data["meta"]["version_coverage"] = "1.0 through 3.1"
    data["meta"]["later_additions"] = later_additions
    data["meta"]["removed"] = version_map["removed"]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return updated, new_entries, later_additions


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Parse OS_CHANGES and apply to reference")
    parser.add_argument("os_changes_dir", help="Path to OS_CHANGES directory")
    parser.add_argument("--ref", default="knowledge/amiga_os_reference.json",
                        help="Path to amiga_os_reference.json")
    parser.add_argument("--output", help="Output path (default: overwrite ref)")
    parser.add_argument("--dump", action="store_true", help="Just dump the version map")
    args = parser.parse_args()

    print("Parsing OS_CHANGES files...")
    version_map = build_version_map(args.os_changes_dir)

    # Summary
    total_funcs = sum(len(v["functions"]) for v in version_map["libraries"].values())
    total_libs = len(version_map["libraries"])
    print(f"  {total_libs} libraries with changes, {total_funcs} functions")

    # Show per-version breakdown
    by_version = {}
    for lib_info in version_map["libraries"].values():
        for func, ver in lib_info["functions"].items():
            by_version.setdefault(ver, 0)
            by_version[ver] += 1
    for ver in sorted(by_version):
        print(f"    {ver}: {by_version[ver]} new functions")

    if version_map["removed"]:
        print(f"  Removed: {sum(len(v['functions']) for v in version_map['removed'].values())} functions")

    if args.dump:
        print(json.dumps(version_map, indent=2))
        return

    # Apply to reference
    output_path = args.output or args.ref
    print(f"\nApplying to {args.ref}...")
    updated, new_entries, later = apply_to_os_reference(
        version_map, args.ref, output_path
    )
    print(f"  Updated {updated} existing functions with version info")
    print(f"  {new_entries} functions in {len(later)} libraries added after 1.3 (stored in meta)")
    for lib_name, info in sorted(later.items()):
        print(f"    {lib_name} (added {info['added_in']}): {info['function_count']} functions")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
