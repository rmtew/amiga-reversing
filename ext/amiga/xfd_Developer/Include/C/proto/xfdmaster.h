#ifndef _PROTO_XFDMASTER_H
#define _PROTO_XFDMASTER_H

#ifndef EXEC_TYPES_H
#include <exec/types.h>
#endif
#ifndef CLIB_XFDMASTER_PROTOS_H
#include <clib/xfdmaster_protos.h>
#endif

#ifndef __NOLIBBASE__
extern struct xfdMasterBase *xfdMasterBase;
#endif

#ifdef __GNUC__
#include <inline/xfdmaster.h>
#elif defined(__VBCC__)
#ifndef __PPC__
#include <inline/xfdmaster_protos.h>
#endif
#else
#include <pragma/xfdmaster_lib.h>
#endif

#endif	/*  _PROTO_XFDMASTER_H  */
