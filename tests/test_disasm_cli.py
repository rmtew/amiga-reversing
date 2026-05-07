from __future__ import annotations

from pathlib import Path

from amiga_reversing.disasm import cli


def test_gen_disasm_writes_with_selected_assembler_profile(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []
    output_path = tmp_path / "out.s"

    def fake_render(binary_path: str, *, project_root=None) -> str:
        calls.append({"binary_path": binary_path})
        return "SECTION section_0,code\n"

    monkeypatch.setattr(cli, "render_binary_source_with_c_backend", fake_render)

    cli.gen_disasm("bin/demo", "entities.jsonl", str(output_path), assembler_profile_name="devpac")

    assert calls == [{"binary_path": "bin/demo"}]
    assert output_path.read_text(encoding="utf-8") == "SECTION section_0,code\n"


def test_main_passes_output_arguments(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []
    output_path = tmp_path / "out.s"

    def fake_gen_disasm(
        binary_path: str,
        entities_path: str,
        output: str,
        **kwargs: object,
    ) -> None:
        calls.append(
            {
                "binary_path": binary_path,
                "entities_path": entities_path,
                "output": output,
                **kwargs,
            }
        )

    monkeypatch.setattr(cli, "gen_disasm", fake_gen_disasm)

    cli.main(["bin/demo", "--entities", "entities.jsonl", "--output", str(output_path)])

    assert calls[0]["output"] == str(output_path)
    assert calls[0]["assembler_profile_name"] == "vasm"
