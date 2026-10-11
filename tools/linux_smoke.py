"""Exercise native assembly/rendering, HTTP import, reproduction and browser UI.

Run from the repository root with PYTHONPATH=. and the server already running.
BRAVE_PATH may select Chromium; M68K_RUN_BRAVE_CDP=1 enables the browser check.
Only a synthetic four-instruction input is created. Outputs are local/ignored.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen

from amiga_reversing.disasm.binary_source import resolve_target_binary_source
from amiga_reversing.disasm.c_backend import (
    assemble_platform_source_text_with_c_backend,
    render_project_source_with_c_backend,
)
from tests.cdp_brave import brave_page


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8123")
    args = parser.parse_args()
    root = Path.cwd()
    output = root / ".runtime-state" / "linux-smoke"
    output.mkdir(parents=True, exist_ok=True)

    def api(path: str, body: dict | None = None) -> dict:
        data = None if body is None else json.dumps(body).encode()
        request = Request(args.url + path, data=data, headers={
            "Content-Type": "application/json", "X-Amiga-Web-App-Contract": "2",
        })
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
        assert payload["ok"], payload
        return payload["data"]

    source = "    SECTION demo,code\nstart:\n    moveq #42,d0\n    addq.l #1,d0\n    rts\n    nop\n"
    original, _ = assemble_platform_source_text_with_c_backend("amiga-hunk", source)
    # Independently fixed expected HUNK bytes, not another renderer as oracle.
    assert original.hex() == (
        "000003f30000000000000001000000000000000000000002"
        "000003e900000002702a52804e754e71000003f2"
    )
    job = api("/api/projects", {
        "filename": "cloud-smoke.hunk", "media_base64": base64.b64encode(original).decode(),
    })
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        state = api("/api/projects/create/status?job_id=" + job["job_id"])
        if state["status"] in {"ready", "failed"}:
            break
        time.sleep(0.1)
    assert state["status"] == "ready", state
    project_id = state["result_project_id"]
    binary_source = resolve_target_binary_source(root / "targets" / project_id, project_root=root)
    rendered = render_project_source_with_c_backend(binary_source)
    rebuilt, _ = assemble_platform_source_text_with_c_backend("amiga-hunk", rendered)
    assert rebuilt == original
    source_path = output / "rendered.s"
    source_path.write_text(rendered)
    vasm_output = output / "vasm.hunk"
    subprocess.run([
        str(root / "tools" / "vasmm68k_mot.exe"), "-Fhunkexe", "-nosym",
        "-o", str(vasm_output), str(source_path),
    ], check=True, stdout=subprocess.DEVNULL)
    assert vasm_output.read_bytes() == original

    with brave_page() as page:
        page.call("Page.navigate", {"url": args.url + "/" + project_id})
        page.wait_for_event("Page.loadEventFired")
        page.wait_for_expression("document.querySelectorAll('.listing-row').length >= 3", timeout=30)
        listing = page.evaluate(
            "Array.from(document.querySelectorAll('.listing-code')).map(x=>x.textContent).join('\\n')"
        )
        assert "moveq.l #42,d0" in listing and "rts" in listing, listing
        page.assert_no_errors()
        screenshot = page.call("Page.captureScreenshot", {"format": "png"})
        (output / "ui.png").write_bytes(base64.b64decode(screenshot["data"]))
    result = {"project": project_id, "url": args.url + "/" + project_id,
              "roundtrip": "C and vasm full-file exact", "sha256": hashlib.sha256(original).hexdigest(),
              "browser": "rendered real native listing, no page errors"}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
