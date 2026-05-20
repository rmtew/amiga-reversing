ndif2raw.exe is the Classic Mac OS NDIF decompression provider used for Disk
Copy 6 read-only/compressed images such as `rohd`/`ddsk` MacBinary files.

This build was produced from the local BSD-3-Clause ndif2raw source at
`resources/clone_common/ndif2raw`, adapted for MSVC and MacBinary II input.

Example:

`ext\tools\ndif2raw\ndif2raw.exe --format=macbinary input.img.bin output.raw`

Run `cmd /c resources\clone_common\ndif2raw\build.bat` from the repository root
to rebuild the local source, then copy
`resources\clone_common\ndif2raw\build\ndif2raw.exe` here.
