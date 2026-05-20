# ndif2raw

A program to convert Apple New Disk Image Format (NDIF) images to raw disk
images.  Apple used to provide this functionality as part of macOS but removed
it in macOS 11 ("Big Sur").

NDIF images can be recognized by an HFS type ID of `'dimg'`, `'rohd'`, or
`'hdro'` (as shown by `GetFileInfo` on Mac) and by the presence of an HFS
resource fork containing a resource of type `'bcem'` (as shown by e.g. `DeRez`
on Mac).

The code currently knows how to decode a subset of the possible NDIF image
types and will abort if it sees something it doesn't know how to handle.

## Usage

```sh
$ ndif2raw [--force] [--verbose] [--format=<format>] <input NDIF path> <output raw path>
```

Supported formats are `resource-fork`, `appledouble`, `applesingle`, and
`macbinary`. The `macbinary` format is a local adaptation for Classic Mac OS
files transferred as MacBinary II, where the NDIF data fork and `bcem` resource
fork are stored in one `.bin` file.

On Windows, build the adapted tool with:

```bat
build.bat
```

## Contributors:

* @mhjacobson – initial version with ADC support
* @Windoze345 — checksum verification and KenCode support
* @erichelgeson — AppleSingle/AppleDouble support
