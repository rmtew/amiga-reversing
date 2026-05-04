#ifndef _INCLUDE_PRAGMA_XFDMASTER_LIB_H
#define _INCLUDE_PRAGMA_XFDMASTER_LIB_H

#ifndef CLIB_XFDMASTER_PROTOS_H
#include <clib/xfdmaster_protos.h>
#endif

#if defined(AZTEC_C) || defined(__MAXON__) || defined(__STORM__)
#pragma amicall(xfdMasterBase,0x01e,xfdAllocBufferInfo())
#pragma amicall(xfdMasterBase,0x024,xfdFreeBufferInfo(a1))
#pragma amicall(xfdMasterBase,0x02a,xfdAllocSegmentInfo())
#pragma amicall(xfdMasterBase,0x030,xfdFreeSegmentInfo(a1))
#pragma amicall(xfdMasterBase,0x036,xfdRecogBuffer(a0))
#pragma amicall(xfdMasterBase,0x03c,xfdDecrunchBuffer(a0))
#pragma amicall(xfdMasterBase,0x042,xfdRecogSegment(a0))
#pragma amicall(xfdMasterBase,0x048,xfdDecrunchSegment(a0))
#pragma amicall(xfdMasterBase,0x04e,xfdGetErrorText(d0))
#pragma amicall(xfdMasterBase,0x054,xfdTestHunkStructure(a0,d0))
#pragma amicall(xfdMasterBase,0x05a,xfdTestHunkStructureNew(a0,d0))
#pragma amicall(xfdMasterBase,0x060,xfdRelocate(a0,d0,a1,d1))
#pragma amicall(xfdMasterBase,0x066,xfdTestHunkStructureFlags(a0,d0,d1))
#pragma amicall(xfdMasterBase,0x06c,xfdStripHunks(a0,d0,a1,d1))
#pragma amicall(xfdMasterBase,0x072,xfdAllocObject(d0))
#pragma amicall(xfdMasterBase,0x078,xfdFreeObject(a1))
#pragma amicall(xfdMasterBase,0x07e,xfdRecogLinker(a0))
#pragma amicall(xfdMasterBase,0x084,xfdUnlink(a0))
#pragma amicall(xfdMasterBase,0x08a,xfdScanData(a0,d0,a1,d1,a2))
#pragma amicall(xfdMasterBase,0x090,xfdFreeScanList(a1))
#pragma amicall(xfdMasterBase,0x096,xfdObjectType(a1))
#pragma amicall(xfdMasterBase,0x09c,xfdInitScanHook(a0,a1))
#endif
#if defined(_DCC) || defined(__SASC)
#pragma  libcall xfdMasterBase xfdAllocBufferInfo     01e 00
#pragma  libcall xfdMasterBase xfdFreeBufferInfo      024 901
#pragma  libcall xfdMasterBase xfdAllocSegmentInfo    02a 00
#pragma  libcall xfdMasterBase xfdFreeSegmentInfo     030 901
#pragma  libcall xfdMasterBase xfdRecogBuffer         036 801
#pragma  libcall xfdMasterBase xfdDecrunchBuffer      03c 801
#pragma  libcall xfdMasterBase xfdRecogSegment        042 801
#pragma  libcall xfdMasterBase xfdDecrunchSegment     048 801
#pragma  libcall xfdMasterBase xfdGetErrorText        04e 001
#pragma  libcall xfdMasterBase xfdTestHunkStructure   054 0802
#pragma  libcall xfdMasterBase xfdTestHunkStructureNew 05a 0802
#pragma  libcall xfdMasterBase xfdRelocate            060 190804
#pragma  libcall xfdMasterBase xfdTestHunkStructureFlags 066 10803
#pragma  libcall xfdMasterBase xfdStripHunks          06c 190804
#pragma  libcall xfdMasterBase xfdAllocObject         072 001
#pragma  libcall xfdMasterBase xfdFreeObject          078 901
#pragma  libcall xfdMasterBase xfdRecogLinker         07e 801
#pragma  libcall xfdMasterBase xfdUnlink              084 801
#pragma  libcall xfdMasterBase xfdScanData            08a a190805
#pragma  libcall xfdMasterBase xfdFreeScanList        090 901
#pragma  libcall xfdMasterBase xfdObjectType          096 901
#pragma  libcall xfdMasterBase xfdInitScanHook        09c 9802
#endif

#endif	/*  _INCLUDE_PRAGMA_XFDMASTER_LIB_H  */
