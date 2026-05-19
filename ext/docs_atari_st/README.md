# Atari ST Reference Markdown

Committed page-cited Markdown versions of local Atari ST reference books.

These files are source-prep artifacts for Atari ST platform knowledge work.
They are used as cited references, not as runtime metadata or parsed truth.
Structured KB JSON and reviewed corrections remain the owners of platform
facts.

Each document has:

```text
<stem>.md
<stem>.source.json
```

The Markdown keeps page markers:

```md
<!-- source-page: 42 -->
## Page 42
```

Cite pages from the `.md` file:

```json
{
  "source_id": "compute-vdi-vol1-md",
  "citation": {
    "path": "ext/docs_atari_st/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.md",
    "page": 42
  }
}
```

Current documents:

```text
AnatomyOfTheAtariSt.md
Computes_Technical_Ref_Guide_Atari_ST_Vol_one.md
FirstAtariStBook.md
The_Concise_Atari_ST_68K_Prog_Ref_Guide.md
```

See `docs/pdf-to-md.md` for the conversion and repair workflow.
