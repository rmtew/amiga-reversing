#ifndef _INLINE_XFDMASTER_H
#define _INLINE_XFDMASTER_H

#ifndef __INLINE_MACROS_H
#include <inline/macros.h>
#endif

#ifndef XFDMASTER_BASE_NAME
#define XFDMASTER_BASE_NAME xfdMasterBase
#endif

#define xfdAllocBufferInfo() \
	LP0(0x1e, struct xfdBufferInfo *, xfdAllocBufferInfo, \
	, XFDMASTER_BASE_NAME)

#define xfdFreeBufferInfo(bufferinfo) \
	LP1NR(0x24, xfdFreeBufferInfo, struct xfdBufferInfo *, bufferinfo, a1, \
	, XFDMASTER_BASE_NAME)

#define xfdAllocSegmentInfo() \
	LP0(0x2a, struct xfdSegmentInfo *, xfdAllocSegmentInfo, \
	, XFDMASTER_BASE_NAME)

#define xfdFreeSegmentInfo(segmentinfo) \
	LP1NR(0x30, xfdFreeSegmentInfo, struct xfdSegmentInfo *, segmentinfo, a1, \
	, XFDMASTER_BASE_NAME)

#define xfdRecogBuffer(bufferinfo) \
	LP1(0x36, BOOL, xfdRecogBuffer, struct xfdBufferInfo *, bufferinfo, a0, \
	, XFDMASTER_BASE_NAME)

#define xfdDecrunchBuffer(bufferinfo) \
	LP1(0x3c, BOOL, xfdDecrunchBuffer, struct xfdBufferInfo *, bufferinfo, a0, \
	, XFDMASTER_BASE_NAME)

#define xfdRecogSegment(segmentinfo) \
	LP1(0x42, BOOL, xfdRecogSegment, struct xfdSegmentInfo *, segmentinfo, a0, \
	, XFDMASTER_BASE_NAME)

#define xfdDecrunchSegment(segmentinfo) \
	LP1(0x48, BOOL, xfdDecrunchSegment, struct xfdSegmentInfo *, segmentinfo, a0, \
	, XFDMASTER_BASE_NAME)

#define xfdGetErrorText(error) \
	LP1(0x4e, STRPTR, xfdGetErrorText, ULONG, error, d0, \
	, XFDMASTER_BASE_NAME)

#define xfdTestHunkStructure(buffer, length) \
	LP2(0x54, BOOL, xfdTestHunkStructure, APTR, buffer, a0, ULONG, length, d0, \
	, XFDMASTER_BASE_NAME)

#define xfdTestHunkStructureNew(buffer, length) \
	LP2(0x5a, UWORD, xfdTestHunkStructureNew, APTR, buffer, a0, ULONG, length, d0, \
	, XFDMASTER_BASE_NAME)

#define xfdRelocate(buffer, length, result, mode) \
	LP4(0x60, UWORD, xfdRelocate, APTR, buffer, a0, ULONG, length, d0, ULONG *, result, a1, ULONG, mode, d1, \
	, XFDMASTER_BASE_NAME)

#define xfdTestHunkStructureFlags(buffer, length, flags) \
	LP3(0x66, UWORD, xfdTestHunkStructureFlags, APTR, buffer, a0, ULONG, length, d0, ULONG, flags, d1, \
	, XFDMASTER_BASE_NAME)

#define xfdStripHunks(buffer, length, result, flags) \
	LP4(0x6c, UWORD, xfdStripHunks, APTR, buffer, a0, ULONG, length, d0, ULONG *, result, a1, ULONG, flags, d1, \
	, XFDMASTER_BASE_NAME)

#define xfdAllocObject(objecttype) \
	LP1(0x72, APTR, xfdAllocObject, ULONG, objecttype, d0, \
	, XFDMASTER_BASE_NAME)

#define xfdFreeObject(object) \
	LP1NR(0x78, xfdFreeObject, APTR, object, a1, \
	, XFDMASTER_BASE_NAME)

#define xfdRecogLinker(linkerinfo) \
	LP1(0x7e, BOOL, xfdRecogLinker, struct xfdLinkerInfo *, linkerinfo, a0, \
	, XFDMASTER_BASE_NAME)

#define xfdUnlink(linkerinfo) \
	LP1(0x84, BOOL, xfdUnlink, struct xfdLinkerInfo *, linkerinfo, a0, \
	, XFDMASTER_BASE_NAME)

#define xfdScanData(buffer, length, result, flags, scanhook) \
	LP5(0x8a, UWORD, xfdScanData, APTR, buffer, a0, ULONG, length, d0, ULONG *, result, a1, ULONG, flags, d1, struct xfdScanHook *, scanhook, a2, \
	, XFDMASTER_BASE_NAME)

#define xfdFreeScanList(scannode) \
	LP1NR(0x90, xfdFreeScanList, struct xfdScanNode *, scannode, a1, \
	, XFDMASTER_BASE_NAME)

#define xfdObjectType(object) \
	LP1(0x96, ULONG, xfdObjectType, APTR, object, a1, \
	, XFDMASTER_BASE_NAME)

#define xfdInitScanHook(entry, data) \
	LP2FP(0x9c, struct xfdScanHook *, xfdInitScanHook, __fpt, entry, a0, APTR, data, a1, \
	, XFDMASTER_BASE_NAME, BOOL (*__fpt)())

#endif /*  _INLINE_XFDMASTER_H  */
