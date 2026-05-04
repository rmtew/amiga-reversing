# Decompression

This document should be ignored until it is completed.

A nuance to executable target files are that they may not contain the real data, instead they may have been compressed
and running them possibly decompresses a data payload to an absolute address, then jumps to an entrypoint within the
decompressed data range which may or may not be the start address.

If we can identify that this is the case we now know that what we need to disassembly, analyse and reassemble to
reproduce what the user is really interested in is not the decompression code and it's payload, but the decompressed
payload. This will be disassembled using the obtained entrypoint address, disassembled and analysed and we will
compare the roundtrip of the reassembled rendered source code to that decompressed payload. The rendered source code
will contain an ORG statement to ensure it assembles to the right matching bytes, along with the restored labelised
and symbolised source code resulting from our auto-analysis.

Note that as of the time of writing our handling of decompression is undefined. As we evolve our handling this
design document must be updated to reflect what we decided to do, and how we do it.

## Handling decompression

At this time there is no current decompression detection or extraction support. There are several aspects to how we
integrate the required support including:

- Decompression integration. Do we incorporate the logic ourselves or depend on complex external dependencies?
- User project integration. Knowing the user wants to reverse the decompressed payload to non-absolute form and not
  the decompressor with compressed payload, using that decompressed payload as the actual target but noting
  the compression involved and extraction so the user understands what happened and what is being reproduced. 
- Corpus integration. Indexing of the corpus should factor it in appropriately, as should transient viewing of
  corpus target data.

## Decompression approaches

We have at hand two different resources for reference:

- The Ancient decompressor suite (shallow local clone to `resources/clone_common/ancient`). This compiles on Windows
  to an executable which can be used for both compressor identification and payload decompression.
- xfdmaster_Dev.lha (extracted and committed to `ext/amiga/xfd_Developer`). This has a range of assembly code for
  different decompression routines that link together for a larger library and tooling to integrate, and use to
  identify and decompress payloads. The assembly routines are in it's `source/ASM` folder.

To identify a compressed payload we want to know:

- The compressor used.
- If an absolute address is used for decompression base address.
- If an absolute address other than the decompression base address is the entrypoint.
- If not tied to an absolute address, how we treat it based on the compressor.

To obtain the decompressed payload the user is really interested in reversing and which we want to actually
disassemble, analyse and render to the user's interest, we need both that metadata and the ability to do the
decompression.

We could implement our own code to identify and decompress payloads. This would allow cleaner integration and could
be done using heuristics based on the assembly code contained in the XFD library combined with hints from the Ancient
decompressor suite. But perhaps better would be to write a `build.bat` script for the Ancient decompressor suite that
compiles it in a way that our C code could call it and invoke it as we need it. The benefit of doing this is that we
can benefit from the work of it's developer in any further improvements.

To be updated as decompression integration formalised.

## User project integration

Knowing that the decompressed payload of a compressed file is the actual desired target to reverse, the user wants to
both be able to see that they are working on the decompressed payload, but see perhaps the compression-related code and
data it came from if they really want to. The benefit of understanding that 

To be updated as decompression integration is added.

## Corpus integration

We tag files in the corpus based on analysis. Knowing that the decompressed payload of a compressed file is the
actual desired target to reverse, the value is perhaps in tagging it is compressed, tagging what compressor was used
at the least. Then processing the decompressed payload as the analysed corpus data.

To be updated as decompression integration is added.
