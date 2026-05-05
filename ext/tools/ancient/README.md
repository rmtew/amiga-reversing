Ancient.exe is the decompression provider used by the C backend.

This build was produced from the local Ancient clone at
`resources/clone_common/ancient` with an added `scan-json input_file` command.
The command scans a carrier file and emits one JSON object per provider-validated
packed stream:

`{"offset":N,"packed_size":N,"raw_size":N,"codec_id":"...","codec_name":"..."}`

The C backend treats this provider output as authoritative candidate discovery.
Header-shaped bytes that Ancient does not validate are not accepted as packed
payload candidates.

Run `cmd /c src\build.bat build-ancient-provider` from the repository root to
rebuild the local Ancient clone and refresh this staged executable.
