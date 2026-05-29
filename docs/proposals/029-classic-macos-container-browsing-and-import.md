# Proposal 029: Classic Mac OS Container Browsing And Import

Status: Proposed.

Classic Mac OS HFS images should behave like Amiga and Atari disk projects:
the parent project is a container browser, and selected supported entries become
child targets with their own listing/source/rendering state. The current Mac
project path partially renders a Mac target directly from the parent container.
That works for some preview/proof views, but it causes architectural drift:
generic listing UI state is applied to a container, and selecting the Mac
project from the home page can trigger a `PUT /ui-preferences` error because
the server only accepts listing preferences for binary projects.

This proposal makes the Mac path consistent with the existing disk browsing
model.

## Checkpoint Index

- [ ] Problem Statement
- [ ] Existing Disk Model
- [ ] Desired Mac Model
- [ ] Tutorial: Opening An HFS Container
- [ ] Tutorial: Importing A Mac File Or Resource
- [ ] Target Layout And Metadata
- [ ] Migration And Git History
- [ ] API Shape
- [ ] UI Shape
- [ ] Preference And Navigation State
- [ ] Validation Gates
- [ ] Implementation Slices
- [ ] Acceptance Criteria
- [ ] Non-Goals

## Problem Statement

Today `macos_hfs_mpw_gm` is both:

```text
HFS disk image container
  and
Mac CODE/resource preview target
```

Those are different responsibilities.

Container responsibility:

```text
show files/folders
show forks and resources
show which entries are importable
launch/import selected entries as child targets
```

Listing target responsibility:

```text
own binary/resource payload
own analysis/listing/source state
own listing preferences
round-trip/export where supported
```

The current mixed path leaks listing behavior into the container. One visible
symptom is:

```text
open macos_hfs_mpw_gm from home
  -> Mac view renders
  -> generic listing preference save runs
  -> PUT /api/projects/macos_hfs_mpw_gm/ui-preferences
  -> server rejects it because the project is not ProjectKind.BINARY
```

The server is correct that the HFS parent is not a binary listing target. The
UI is wrong to treat it like one.

## Existing Disk Model

Amiga and Atari disk projects already use the shape we want.

Textual model:

```text
targets/amiga_disk_example/
  manifest.json
  disk/project metadata
  targets/
    amiga_hunk_game_xxxxxxxx/
      binary.bin
      source_binary.json
      asm.s
    amiga_raw_bootblock/
      binary.bin
      source_binary.json
      asm.s
```

User workflow:

```text
open disk project
  -> see disk/container browser
  -> see imported auto/manual child targets
  -> click child target
  -> navigate to child listing project
```

The disk parent can have container UI state. The child target has listing UI
state.

Mac should follow the same split.

## Desired Mac Model

Mac HFS project:

```text
macos_hfs_mpw_gm
  kind: macos_hfs_container
  role: browse image contents and resource forks
```

Imported Mac child target:

```text
macos_hfs_mpw_gm__macos_file_mpw_tools_asm
  kind: macos_resource_code_file
  role: analyze/render selected file/resource CODE payloads
```

The parent page should answer:

```text
What is inside this HFS image?
Which files have supported forks/resources?
Which entries are already imported?
Which entries can be imported?
```

The child page should answer:

```text
What CODE resources exist in this selected file?
Which CODE resource/segment is selected?
What source/listing facts are available?
What remains unsupported/deferred?
```

## Tutorial: Opening An HFS Container

When the user opens the Mac project from the home page:

```text
GET /
  -> project card: macos_hfs_mpw_gm

click Open
  -> navigate /macos_hfs_mpw_gm
  -> render container browser
```

The parent view should not load listing windows or save listing preferences.
It should use container APIs:

```text
GET /api/projects/macos_hfs_mpw_gm/macos/container
```

Example payload sketch:

```json
{
  "kind": "macos_hfs_container",
  "image_path": "resources/platform_macos/MPW-GM.img.bin",
  "volume_name": "MPW-GM",
  "files": [
    {
      "path": "MPW-GM/MPW/Tools/Asm",
      "finder_type": "MPST",
      "creator": "MPS ",
      "data_fork_size": 0,
      "resource_fork_size": 2048,
      "supported_imports": ["resource_code_file"],
      "imported_target_id": "macos_hfs_mpw_gm__macos_file_mpw_tools_asm"
    }
  ]
}
```

Textual UI:

```text
macos_hfs_mpw_gm

Files
  MPW-GM/
    MPW/
      Tools/
        Asm        MPST/MPS   resource fork   imported

Resources for Asm
  CODE 0    jump table metadata
  CODE 1    Main
  CODE 2    FPOpTable
  CURS 128  metadata only
  vers 1    candidate metadata
```

## Tutorial: Importing A Mac File Or Resource

The user should be able to import supported entries from the container.

Example:

```text
select MPW-GM/MPW/Tools/Asm
click Import CODE File
```

Backend flow:

```text
HFS image + file path
  -> read file metadata/forks
  -> parse resource fork
  -> create child target
  -> write child binary/resource metadata
  -> render supported source/listing artifacts
  -> update parent manifest
```

API sketch:

```http
POST /api/projects/macos_hfs_mpw_gm/macos/import
Content-Type: application/json

{
  "entry_kind": "resource_code_file",
  "hfs_path": "MPW-GM/MPW/Tools/Asm",
  "selected_code_resource_id": 1
}
```

Response:

```json
{
  "target_id": "macos_hfs_mpw_gm__macos_file_mpw_tools_asm",
  "target_path": "targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm",
  "status": "imported"
}
```

Then the UI navigates to the child target:

```text
/macos_hfs_mpw_gm__macos_file_mpw_tools_asm
```

## Target Layout And Metadata

Parent:

```text
targets/macos_hfs_mpw_gm/
  manifest.json
  container.json
  targets/
    macos_file_mpw_tools_asm/
      binary.bin
      source_binary.json
      macos_resource_inventory.json
      asm.s
```

Parent manifest imported target entry:

```json
{
  "target_name": "macos_hfs_mpw_gm__macos_file_mpw_tools_asm",
  "entry_path": "MPW-GM/MPW/Tools/Asm",
  "target_type": "macos_resource_code_file",
  "import_kind": "manual",
  "finder_type": "MPST",
  "creator": "MPS ",
  "resource_types": ["CODE", "CURS", "vers"]
}
```

Child `source_binary.json` should identify the exact selected source:

```json
{
  "kind": "macos_resource_code_file",
  "container_project_id": "macos_hfs_mpw_gm",
  "source_image": "resources/platform_macos/MPW-GM.img.bin",
  "hfs_path": "MPW-GM/MPW/Tools/Asm",
  "finder": {"type": "MPST", "creator": "MPS "},
  "fork": "resource",
  "selected_code_resource_id": 1
}
```

The child target may still expose all CODE/resource details, but its identity
comes from the selected HFS file/resource fork, not from the parent container.

## Migration And Git History

The existing Mac rendered source and metadata must not disappear or be
regenerated into a fresh path without history. Proposal 029 changes ownership:
the parent HFS project becomes a container, and the selected MPW Asm file
becomes a child target. Existing child-owned files should therefore move with
`git mv`.

Migration sketch:

```text
before:
  targets/macos_hfs_mpw_gm/
    asm.s
    binary.bin
    source_binary.json
    macos_resource_inventory.json

after:
  targets/macos_hfs_mpw_gm/
    manifest.json
    container.json
    targets/
      macos_file_mpw_tools_asm/
        asm.s
        binary.bin
        source_binary.json
        macos_resource_inventory.json
```

Command shape:

```text
git mv targets/macos_hfs_mpw_gm/asm.s \
       targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/asm.s
```

Move the complete child-owned artifact set together:

```text
asm.s
binary.bin
source_binary.json
resource/code inventory files
listing/source metadata files
round-trip or reproduction metadata that describes the selected Mac file
```

Leave only parent-owned container files at the parent root:

```text
manifest.json
container/HFS inventory cache
project metadata for the HFS image
```

Regression rule:

```text
platform-rendered-source-roundtrip
  -> must still discover the moved asm.s
  -> must still report Mac source assembly as unsupported until supported
  -> must fail or report drift if the tracked Mac asm.s disappears
```

The deterministic report at
`docs/validation/rendered-source-roundtrip-report.json` must be updated in the
same migration commit so reviewers can see that the target identity/path changed
without losing rendered-source coverage.

## API Shape

Add Mac container APIs parallel to disk browsing APIs.

Container read:

```text
GET /api/projects/{project_id}/macos/container
```

Import:

```text
POST /api/projects/{project_id}/macos/import
```

Open child:

```text
GET /api/projects/{child_target_id}
```

The generic project payload should route by project kind:

```python
if project.kind is ProjectKind.MACOS_CONTAINER:
    return build_macos_container_payload(project)

if project.kind is ProjectKind.MACOS_RESOURCE_CODE_FILE:
    return build_macos_project_payload(project.id)
```

If the enum remains `ProjectKind.MACOS` for compatibility, use target type to
split parent and child:

```python
if project.kind is ProjectKind.MACOS and project.target_type == "macos_hfs_container":
    return build_macos_container_payload(project)

if project.kind is ProjectKind.MACOS and project.target_type == "macos_hfs_resource_code_file":
    return build_macos_project_payload(project.id)
```

## UI Shape

Parent Mac container page:

```text
project header
  classic mac
  container

left/content:
  HFS tree
  file metadata
  fork/resource inventory

actions:
  Import CODE file
  Open imported target
```

Child Mac target page:

```text
project header
  classic mac
  source
  container

listing/source panel:
  CODE details
  CODE 0 metadata
  CODE resource previews/listing rows
  non-CODE resource metadata
```

The current Mac CODE details view belongs on the child target, not the parent
container.

## Preference And Navigation State

Container preferences and listing preferences must be separate.

Container preference example:

```json
{
  "selected_hfs_path": "MPW-GM/MPW/Tools/Asm",
  "expanded_paths": ["MPW-GM", "MPW-GM/MPW", "MPW-GM/MPW/Tools"]
}
```

Listing preference example:

```json
{
  "target_id": "macos_hfs_mpw_gm__macos_file_mpw_tools_asm",
  "listing_location": {
    "locator": {"row_id": "CODE_1_loc_00000028"}
  }
}
```

Rules:

```text
Mac container parent:
  may save container UI preferences
  must not call binary listing preference save

Mac child target:
  may save listing preferences if it owns listing rows
```

Immediate bug covered by this rule:

```text
PUT /api/projects/macos_hfs_mpw_gm/ui-preferences
  should not happen for the container page
```

The server should still be defensive:

```python
def _save_ui_preferences_payload(project_name, body):
    project = get_project(project_name)
    if project.kind is not ProjectKind.BINARY and not is_listing_target(project):
        return {"preferences": {}}
    ...
```

But the clean UI fix is to stop scheduling listing preference saves from the
container view.

## Validation Gates

CDP/browser tests:

```text
open Mac container from home
  -> no browser errors
  -> no PUT binary ui-preferences request
  -> HFS/resource browser visible

select MPW-GM/MPW/Tools/Asm
  -> CODE/CURS/vers inventory visible

import/open Asm child target
  -> child target route opens
  -> Mac CODE details visible
  -> unsupported Mac source assembly remains explicit
```

Backend tests:

```text
container payload lists HFS file metadata and resource fork inventory
import creates child target under parent targets/
parent manifest records imported child
child source_binary.json records exact HFS path/fork/resource context
reimport is idempotent
unsupported resources remain browseable metadata, not fake targets
```

Regression test for the current symptom:

```text
test_brave_cdp_can_open_real_macos_project_from_home
  should pass with no HTTP 400 from /ui-preferences
```

## Implementation Slices

### Slice 1: Classify Parent Versus Child

Make the project records distinguish Mac container parent from Mac target child.

Possible target types:

```text
macos_hfs_container
macos_hfs_resource_code_file
macos_resource_code_resource
macos_resource_data_asset
```

Before changing render/import behavior, move existing Mac child-owned artifacts
into the child target directory with `git mv` and update project metadata to
point at the new location.

### Slice 2: Container Payload Builder

Build a Mac container payload from the HFS image:

```python
def build_macos_container_payload(project_id: str) -> dict[str, object]:
    image = load_hfs_image(project.source_path)
    return {
        "kind": "macos_hfs_container",
        "files": list_hfs_files(image),
        "imported_targets": list_imported_macos_targets(project_id),
    }
```

### Slice 3: Resource/Fork Inventory

Expose file-level fork/resource metadata without importing everything:

```text
finder type/creator
data fork size
resource fork size
resource types/counts
CODE resource ids/names/sizes
non-CODE metadata status
supported import actions
```

### Slice 4: Import Action

Add explicit import command:

```python
def import_macos_resource_code_file(project_id, hfs_path, selected_code_resource_id):
    resource_fork = read_resource_fork(project_id, hfs_path)
    target_id = stable_macos_target_id(project_id, hfs_path)
    write_child_target(target_id, resource_fork, selected_code_resource_id)
    update_parent_manifest(project_id, target_id)
    return target_id
```

### Slice 5: Route UI By Project Role

Parent route:

```javascript
if (payload.kind === "macos_hfs_container") {
  renderMacosContainer(payload);
  return;
}
```

Child route:

```javascript
if (payload.kind === "macos_project") {
  renderMacosProject(payload);
  bindListingSelection();
  return;
}
```

### Slice 6: Preference Split

Stop generic listing preference behavior on container pages.

```javascript
function projectHasListingPreferences(payload) {
  return payload.kind !== "macos_hfs_container" && payload.kind !== "disk_project";
}
```

### Slice 7: Tests And Fixture Update

Add tests for:

```text
real Mac container opens from home
container view has no listing preference PUT
resource inventory is visible
imported child target opens CODE details
server no-ops non-listing preference PUT defensively
```

## Acceptance Criteria

- `macos_hfs_mpw_gm` opens as a container browser from the home page without
  browser errors.
- The parent Mac container does not use binary/listing UI preference save paths.
- The HFS browser shows files, Finder metadata, forks, resource types, and CODE
  resource inventory for supported entries.
- Supported Mac entries can be imported as child targets under the parent
  `targets/` directory.
- Imported Mac child targets own CODE/resource listing/source state.
- Existing Mac rendered source and metadata are moved with `git mv`, preserving
  history where Git can track it.
- `platform-rendered-source-roundtrip` continues to cover the moved Mac `asm.s`
  and the deterministic validation report records the new path/target status.
- Existing Mac CODE detail rendering moves to or remains available through the
  child target path.
- Unsupported non-CODE resources remain explicit metadata, not fake decoded
  targets.
- Reimporting the same HFS entry is idempotent.
- CDP tests cover home selection, container browsing, import/open child, and
  no `/ui-preferences` 400.

## Non-Goals

- Do not make Mac source assembly supported here.
- Do not promote Mac byte-entry, relocation/fixup, source-to-CODE, or non-CODE
  payload facts beyond their current accepted/deferred/unsupported states.
- Do not auto-import every HFS file.
- Do not decode every resource type.
- Do not treat the HFS parent as a binary listing target.
- Do not create child targets for unsupported resources without a parser or
  accepted provenance/role model.
