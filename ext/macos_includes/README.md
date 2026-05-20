Classic Mac OS include snapshots extracted from local developer disk images.

These files are committed as source-truth references for checking parsed Classic
Mac OS documentation and OCR/LLM-derived knowledge. They are not generated
runtime metadata.

Current snapshot:

- `mpw_gm/Interfaces`
  - extracted from `resources/platform_macos/MPW-GM.img.bin`
  - contains MPW `Interfaces&Libraries:Interfaces` data forks
  - original Classic Mac line endings and bytes are preserved

Derived files:

- `mpw_gm/inventory.json`: full HFS catalog inventory from the decoded image.
- `mpw_gm/source.json`: source and extraction metadata.
- `mpw_gm/index.json`: conservative symbol index generated from C, assembler,
  and Rez includes for cross-checking documentation-derived facts.

Query examples:

```bat
uv run python src\scripts\query_macos_include_index.py PBGetCatInfoSync
uv run python src\scripts\query_macos_include_index.py fsRdPerm
uv run python src\scripts\query_macos_include_index.py SIZE --kind rez_type
```
