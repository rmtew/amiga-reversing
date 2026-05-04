#ifndef _VBCCINLINE_XFDMASTER_H
#define _VBCCINLINE_XFDMASTER_H

#ifndef EXEC_TYPES_H
#include <exec/types.h>
#endif

struct xfdBufferInfo * __xfdAllocBufferInfo(__reg("a6") struct xfdMasterBase *)="\tjsr\t-30(a6)";
#define xfdAllocBufferInfo() __xfdAllocBufferInfo(xfdMasterBase)

void __xfdFreeBufferInfo(__reg("a6") struct xfdMasterBase *, __reg("a1") struct xfdBufferInfo * bufferinfo)="\tjsr\t-36(a6)";
#define xfdFreeBufferInfo(bufferinfo) __xfdFreeBufferInfo(xfdMasterBase, (bufferinfo))

struct xfdSegmentInfo * __xfdAllocSegmentInfo(__reg("a6") struct xfdMasterBase *)="\tjsr\t-42(a6)";
#define xfdAllocSegmentInfo() __xfdAllocSegmentInfo(xfdMasterBase)

void __xfdFreeSegmentInfo(__reg("a6") struct xfdMasterBase *, __reg("a1") struct xfdSegmentInfo * segmentinfo)="\tjsr\t-48(a6)";
#define xfdFreeSegmentInfo(segmentinfo) __xfdFreeSegmentInfo(xfdMasterBase, (segmentinfo))

BOOL __xfdRecogBuffer(__reg("a6") struct xfdMasterBase *, __reg("a0") struct xfdBufferInfo * bufferinfo)="\tjsr\t-54(a6)";
#define xfdRecogBuffer(bufferinfo) __xfdRecogBuffer(xfdMasterBase, (bufferinfo))

BOOL __xfdDecrunchBuffer(__reg("a6") struct xfdMasterBase *, __reg("a0") struct xfdBufferInfo * bufferinfo)="\tjsr\t-60(a6)";
#define xfdDecrunchBuffer(bufferinfo) __xfdDecrunchBuffer(xfdMasterBase, (bufferinfo))

BOOL __xfdRecogSegment(__reg("a6") struct xfdMasterBase *, __reg("a0") struct xfdSegmentInfo * segmentinfo)="\tjsr\t-66(a6)";
#define xfdRecogSegment(segmentinfo) __xfdRecogSegment(xfdMasterBase, (segmentinfo))

BOOL __xfdDecrunchSegment(__reg("a6") struct xfdMasterBase *, __reg("a0") struct xfdSegmentInfo * segmentinfo)="\tjsr\t-72(a6)";
#define xfdDecrunchSegment(segmentinfo) __xfdDecrunchSegment(xfdMasterBase, (segmentinfo))

STRPTR __xfdGetErrorText(__reg("a6") struct xfdMasterBase *, __reg("d0") ULONG error)="\tjsr\t-78(a6)";
#define xfdGetErrorText(error) __xfdGetErrorText(xfdMasterBase, (error))

BOOL __xfdTestHunkStructure(__reg("a6") struct xfdMasterBase *, __reg("a0") APTR buffer, __reg("d0") ULONG length)="\tjsr\t-84(a6)";
#define xfdTestHunkStructure(buffer, length) __xfdTestHunkStructure(xfdMasterBase, (buffer), (length))

UWORD __xfdTestHunkStructureNew(__reg("a6") struct xfdMasterBase *, __reg("a0") APTR buffer, __reg("d0") ULONG length)="\tjsr\t-90(a6)";
#define xfdTestHunkStructureNew(buffer, length) __xfdTestHunkStructureNew(xfdMasterBase, (buffer), (length))

UWORD __xfdRelocate(__reg("a6") struct xfdMasterBase *, __reg("a0") APTR buffer, __reg("d0") ULONG length, __reg("a1") ULONG * result, __reg("d1") ULONG mode)="\tjsr\t-96(a6)";
#define xfdRelocate(buffer, length, result, mode) __xfdRelocate(xfdMasterBase, (buffer), (length), (result), (mode))

UWORD __xfdTestHunkStructureFlags(__reg("a6") struct xfdMasterBase *, __reg("a0") APTR buffer, __reg("d0") ULONG length, __reg("d1") ULONG flags)="\tjsr\t-102(a6)";
#define xfdTestHunkStructureFlags(buffer, length, flags) __xfdTestHunkStructureFlags(xfdMasterBase, (buffer), (length), (flags))

UWORD __xfdStripHunks(__reg("a6") struct xfdMasterBase *, __reg("a0") APTR buffer, __reg("d0") ULONG length, __reg("a1") ULONG * result, __reg("d1") ULONG flags)="\tjsr\t-108(a6)";
#define xfdStripHunks(buffer, length, result, flags) __xfdStripHunks(xfdMasterBase, (buffer), (length), (result), (flags))

APTR __xfdAllocObject(__reg("a6") struct xfdMasterBase *, __reg("d0") ULONG objecttype)="\tjsr\t-114(a6)";
#define xfdAllocObject(objecttype) __xfdAllocObject(xfdMasterBase, (objecttype))

void __xfdFreeObject(__reg("a6") struct xfdMasterBase *, __reg("a1") APTR object)="\tjsr\t-120(a6)";
#define xfdFreeObject(object) __xfdFreeObject(xfdMasterBase, (object))

BOOL __xfdRecogLinker(__reg("a6") struct xfdMasterBase *, __reg("a0") struct xfdLinkerInfo * linkerinfo)="\tjsr\t-126(a6)";
#define xfdRecogLinker(linkerinfo) __xfdRecogLinker(xfdMasterBase, (linkerinfo))

BOOL __xfdUnlink(__reg("a6") struct xfdMasterBase *, __reg("a0") struct xfdLinkerInfo * linkerinfo)="\tjsr\t-132(a6)";
#define xfdUnlink(linkerinfo) __xfdUnlink(xfdMasterBase, (linkerinfo))

UWORD __xfdScanData(__reg("a6") struct xfdMasterBase *, __reg("a0") APTR buffer, __reg("d0") ULONG length, __reg("a1") ULONG * result, __reg("d1") ULONG flags, __reg("a2") struct xfdScanHook * scanhook)="\tjsr\t-138(a6)";
#define xfdScanData(buffer, length, result, flags, scanhook) __xfdScanData(xfdMasterBase, (buffer), (length), (result), (flags), (scanhook))

void __xfdFreeScanList(__reg("a6") struct xfdMasterBase *, __reg("a1") struct xfdScanNode * scannode)="\tjsr\t-144(a6)";
#define xfdFreeScanList(scannode) __xfdFreeScanList(xfdMasterBase, (scannode))

ULONG __xfdObjectType(__reg("a6") struct xfdMasterBase *, __reg("a1") APTR object)="\tjsr\t-150(a6)";
#define xfdObjectType(object) __xfdObjectType(xfdMasterBase, (object))

struct xfdScanHook * __xfdInitScanHook(__reg("a6") struct xfdMasterBase *, __reg("a0") BOOL (*entry)(), __reg("a1") APTR data)="\tjsr\t-156(a6)";
#define xfdInitScanHook(entry, data) __xfdInitScanHook(xfdMasterBase, (entry), (data))

#endif /*  _VBCCINLINE_XFDMASTER_H  */
