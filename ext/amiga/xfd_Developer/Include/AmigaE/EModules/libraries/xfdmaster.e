/*
**      $VER: xfdmaster.h 39.5 (06.10.03)
**
**      Copyright © 1994-2003 by Georg Hörmann, Dirk Stöcker
**      All Rights Reserved.
**
**      Translated to E by Sven Steiniger until version 38.4 (02.11.98)
**      Updated by Ronald van Dijk since version 39
*/

OPT MODULE
OPT PREPROCESS
OPT EXPORT

MODULE 'exec/libraries', 'exec/execbase',
       'dos/dosextens'

/*********************
*                    *
*    Library Base    *
*                    *
*********************/

OBJECT xfdMasterBase
  libNode:lib
  xfdm_SegList:LONG                       /* PRIVATE! */
  xfdm_DosBase:PTR TO doslibrary          /* May be used for I/O etc. */
  xfdm_FirstSlave:PTR TO xfdSlave         /* List of available slaves */
  xfdm_FirstForeMan:PTR TO xfdForeMan     /* PRIVATE! */
  xfdm_MinBufferSize:LONG                 /* (V36) Min. BufSize for xfdRecogBuffer() */
  xfdm_MinLinkerSize:LONG                 /* (V36) Min. BufSize for xfdRecogLinker() */
  xfdm_ExecBase:PTR TO execbase           /* (V38.2) Cached for fast access */
ENDOBJECT


CONST XFDM_VERSION              = 39      /* for OpenLibrary() */
#define XFDM_NAME 'xfdmaster.library'

/***************************
*                          *
*    Object Types (V36)    *
*                          *
***************************/

CONST XFDOBJ_BUFFERINFO         = 1       /* xfdBufferInfo structure */
CONST XFDOBJ_SEGMENTINFO        = 2       /* xfdSegmentInfo structure */
CONST XFDOBJ_LINKERINFO         = 3       /* xfdLinkerInfo structure */
CONST XFDOBJ_SCANNODE           = 4       /* (V37) xfdScanNode structure */
CONST XFDOBJ_SCANHOOK           = 5       /* (V37) xfdScanHook structure */
CONST XFDOBJ_MAX                = 5       /* PRIVATE! */

/********************
*                   *
*    Buffer Info    *
*                   *
********************/

OBJECT xfdBufferInfo
  xfdbi_SourceBuffer:PTR TO CHAR          /* Pointer to source buffer */
  xfdbi_SourceBufLen:LONG                 /* Length of source buffer */
  xfdbi_Slave:PTR TO xfdSlave             /* PRIVATE! */
  xfdbi_PackerName:PTR TO CHAR            /* Name of recognized packer */
  xfdbi_PackerFlags:INT                   /* Flags for recognized packer */
  xfdbi_Error:INT                         /* Error return code */
  xfdbi_TargetBuffer:PTR TO CHAR          /* Pointer to target buffer */
  xfdbi_TargetBufMemType:LONG             /* Memtype of target buffer */
  xfdbi_TargetBufLen:LONG                 /* Full length of buffer */
  xfdbi_TargetBufSaveLen:LONG             /* Used length of buffer */
  xfdbi_DecrAddress:LONG                  /* Address to load decrunched file */
  xfdbi_JmpAddress:LONG                   /* Address to jump in file */
  xfdbi_Special:PTR TO CHAR               /* Special decrunch info (eg. password) */
  xfdbi_Flags:INT                         /* (V37) Flags to influence recog/decr */
  xfdbi_Reserved0:INT                     /* (V38) PRIVATE! */
  xfdbi_MinTargetLen:LONG                 /* (V38) Required length of target buffer */
  xfdbi_FinalTargetLen:LONG               /* (V38) Final length of decrunched file */
  xfdbi_UserTargetBuf:PTR TO CHAR         /* (V38) Target buffer allocated by user */
  xfdbi_UserTargetBufLen:LONG             /* (V38) Target buffer length */
  xfdbi_MinSourceLen:LONG                 /* (V39) minimum source length (tested by
  					     master library */
ENDOBJECT

/* Max. length of special info */
#define xfdbi_MaxSpecialLen xfdbi_Error


/*********************
*                    *
*    Segment Info    *
*                    *
*********************/

OBJECT xfdSegmentInfo
  xfdsi_SegList:LONG                      /* BPTR to segment list */
  xfdsi_Slave:PTR TO xfdSlave             /* PRIVATE! */
  xfdsi_PackerName:PTR TO CHAR            /* Name of recognized packer */
  xfdsi_PackerFlags:INT                   /* Flags for recognized packer */
  xfdsi_Error:INT                         /* Error return code */
  xfdsi_Special:PTR TO CHAR               /* Special decrunch info (eg. password) */
  xfdsi_RelMode:INT                       /* (V34) Relocation mode */
  xfdsi_Flags:INT                         /* (V37) Flags to influence recog/decr */
ENDOBJECT

/* Max. length of special info */
#define xfdsi_MaxSpecialLen xfdsi_Error


/**************************
*                         *
*    Linker Info (V36)    *
*                         *
**************************/

OBJECT xfdLinkerInfo
  xfdli_Buffer:PTR TO CHAR                /* Pointer to buffer */
  xfdli_BufLen:LONG                       /* Length of buffer */
  xfdli_LinkerName:PTR TO CHAR            /* Name of recognized linker */
  xfdli_Unlink:PTR TO CHAR                /* PRIVATE! */
  xfdli_Reserved:INT                      /* Set to NULL */
  xfdli_Error:INT                         /* Error return code */
  xfdli_Hunk1:LONG                        /* PRIVATE! */
  xfdli_Hunk2:LONG                        /* PRIVATE! */
  xfdli_Amount1:LONG                      /* PRIVATE! */
  xfdli_Amount2:LONG                      /* PRIVATE! */
  xfdli_Save1:PTR TO CHAR                 /* Pointer to first unlinked file */
  xfdli_Save2:PTR TO CHAR                 /* Pointer to second unlinked file */
  xfdli_SaveLen1:LONG                     /* Length of first unlinked file */
  xfdli_SaveLen2:LONG                     /* Length of second unlinked file */
ENDOBJECT

/************************
*                       *
*    Scan Node (V37)    *
*                       *
************************/

OBJECT xfdScanNode
  xfdsn_Next:PTR TO xfdScanNode           /* Pointer to next xfdScanNode or NULL */
  xfdsn_Save:PTR TO CHAR                  /* Pointer to data */
  xfdsn_SaveLen:LONG                      /* Length of data */
  xfdsn_PackerName:PTR TO CHAR            /* Name of recognized packer */
  xfdsn_PackerFlags:INT                   /* Flags for recognized packer */
ENDOBJECT

/************************
*                       *
*    Scan Hook (V37)    *
*                       *
************************/

OBJECT xfdScanHook
  xfdsh_Entry:LONG                        /* Entrypoint of hook code (BOOL (*)()) */
  xfdsh_Data:PTR TO CHAR                  /* Private data of hook */
  xfdsh_ToDo:LONG                         /* Bytes still to scan (READ ONLY) */
  xfdsh_ScanNode:LONG                     /* Found data right now (or NULL) (READ ONLY) */
ENDOBJECT

/********************
*                   *
*    Error Codes    *
*                   *
********************/

CONST XFDERR_OK                 = $0000   /* No errors */

CONST XFDERR_NOMEMORY           = $0001   /* Error allocating memory */
CONST XFDERR_NOSLAVE            = $0002   /* No slave entry in info structure */
CONST XFDERR_NOTSUPPORTED       = $0003   /* Slave doesn't support called function */
CONST XFDERR_UNKNOWN            = $0004   /* Unknown file */
CONST XFDERR_NOSOURCE           = $0005   /* No sourcebuffer/seglist specified */
CONST XFDERR_WRONGPASSWORD      = $0006   /* Wrong password for decrunching */
CONST XFDERR_BADHUNK            = $0007   /* Bad hunk structure */
CONST XFDERR_CORRUPTEDDATA      = $0008   /* Crunched data is corrupted */
CONST XFDERR_MISSINGRESOURCE    = $0009   /* (V34) Missing resource (eg. library) */
CONST XFDERR_WRONGKEY           = $000a   /* (V35) Wrong 16/32 bit key */
CONST XFDERR_BETTERCPU          = $000b   /* (V37) Better CPU required */
CONST XFDERR_HOOKBREAK          = $000c   /* (V37) Hook caused break */
CONST XFDERR_DOSERROR           = $000d   /* (V37) Dos error */
CONST XFDERR_NOTARGET           = $000e   /* (V38) No user target given */
CONST XFDERR_TARGETTOOSMALL     = $000f   /* (V38) User target is too small */
CONST XFDERR_TARGETNOTSUPPORTED = $0010   /* (V38) User target not supported */

CONST XFDERR_UNDEFINEDHUNK      = $1000   /* (V34) Undefined hunk type */
CONST XFDERR_NOHUNKHEADER       = $1001   /* (V34) File is not executable */
CONST XFDERR_BADEXTTYPE         = $1002   /* (V34) Bad hunk_ext type */
CONST XFDERR_BUFFERTRUNCATED    = $1003   /* (V34) Unexpected end of file */
CONST XFDERR_WRONGHUNKAMOUNT    = $1004   /* (V34) Wrong amount of hunks */
CONST XFDERR_NOOVERLAYS         = $1005   /* (V36) Overlays not allowed */

CONST XFDERR_UNSUPPORTEDHUNK    = $2000   /* (V34) Hunk type not supported */
CONST XFDERR_BADRELMODE         = $2001   /* (V34) Unknown XFDREL_#? mode */

/*******************************
*                              *
*    Relocation Modes (V34)    *
*                              *
*******************************/

CONST XFDREL_DEFAULT            = $0000   /* Use memory types given by hunk_header */
CONST XFDREL_FORCECHIP          = $0001   /* Force all hunks to chip ram */
CONST XFDREL_FORCEFAST          = $0002   /* Force all hunks to fast ram */

/*************************************
*                                    *
*    Values for xfd??_PackerFlags    *
*                                    *
*************************************/

/* Bit numbers */
CONST XFDPFB_RELOC              = 0       /* Relocatible file packer */
CONST XFDPFB_ADDR               = 1       /* Absolute address file packer */
CONST XFDPFB_DATA               = 2       /* Data file packer */

CONST XFDPFB_PASSWORD           = 4       /* Packer requires password */
CONST XFDPFB_RELMODE            = 5       /* (V34) Decruncher supports xfdsi_RelMode */
CONST XFDPFB_KEY16              = 6       /* (V35) Packer requires 16 bit key */
CONST XFDPFB_KEY32              = 7       /* (V35) Packer requires 32 bit key */

CONST XFDPFB_RECOGLEN           = 8       /* (V38) slave recognizes target lengths */
CONST XFDPFB_USERTARGET         = 9       /* (V38) slave supports user target buffer */

CONST XFDPFB_EXTERN             = 15      /* (V37) PRIVATE */

/* Bit masks */
CONST XFDPFF_RELOC              = $0001   /* (1<<XFDPFB_RELOC) */
CONST XFDPFF_ADDR               = $0002   /* (1<<XFDPFB_ADDR) */
CONST XFDPFF_DATA               = $0004   /* (1<<XFDPFB_DATA) */

CONST XFDPFF_PASSWORD           = $0010   /* (1<<XFDPFB_PASSWORD) */
CONST XFDPFF_RELMODE            = $0020   /* (1<<XFDPFB_RELMODE) */
CONST XFDPFF_KEY16              = $0040   /* (1<<XFDPFB_KEY16) */
CONST XFDPFF_KEY32              = $0080   /* (1<<XFDPFB_KEY32) */

CONST XFDPFF_RECOGLEN           = $0100   /* (1<<XFDPFB_RECOGLEN) */
CONST XFDPFF_USERTARGET         = $0200   /* (1<<XFDPFB_USERTARGET) */

CONST XFDPFF_EXTERN             = $8000   /* (1<<XFDPFB_EXTERN) */

/************************************
*                                   *
*    Values for xfd??_Flags (V37)   *
*                                   *
************************************/

/* Bit numbers */
CONST XFDFB_RECOGEXTERN         = 0       /* xfdRecog#?() uses external slaves */
CONST XFDFB_RECOGTARGETLEN      = 1       /* (V38) xfdRecogBuffer() uses only slaves
                                             that recognize target lengths */
CONST XFDFB_RECOGUSERTARGET     = 2       /* (V38) xfdRecogBuffer() uses only slaves
                                             that support user targets */
CONST XFDFB_USERTARGET          = 3       /* (V38) xfdbi_DecrunchBuffer() decrunchs
                                             to given xfdbi_UserTarget */
CONST XFDFB_MASTERALLOC         = 4       /* (V39) master allocated decrunch buffer */

/* Bit masks */
CONST XFDFF_RECOGEXTERN         = $0001   /* (1<<XFDFB_RECOGEXTERN) */
CONST XFDFF_RECOGTARGETLEN      = $0002   /* (1<<XFDFB_RECOGTARGETLEN) */
CONST XFDFF_RECOGUSERTARGET     = $0004   /* (1<<XFDFB_RECOGUSERTARGET) */
CONST XFDFF_USERTARGET          = $0008   /* (1<<XFDFB_USERTARGET) */
CONST XFDFF_MASTERALLOC         = $0010   /* (1<<XFDFB_MASTERALLOC) */

/****************************************************
*                                                   *
*    Flags for xfdTestHunkStructureFlags() (V36)    *
*                                                   *
****************************************************/

/* Bit numbers */
CONST XFDTHB_NOOVERLAYS         = 0       /* Abort on hunk_overlay */

/* Bit masks */
CONST XFDTHF_NOOVERLAYS         = $0001   /* (1<<XFDTHB_NOOVERLAYS) */

/****************************************
*                                       *
*    Flags for xfdStripHunks() (V36)    *
*                                       *
****************************************/

/* Bit numbers */
CONST XFDSHB_NAME               = 0       /* Strip hunk_name */
CONST XFDSHB_SYMBOL             = 1       /* Strip hunk_symbol */
CONST XFDSHB_DEBUG              = 2       /* Strip hunk_debug */

/* Bit masks */
CONST XFDSHF_NAME               = $0001   /* (1<<XFDSHB_NAME) */
CONST XFDSHF_SYMBOL             = $0002   /* (1<<XFDSHB_SYMBOL) */
CONST XFDSHF_DEBUG              = $0004   /* (1<<XFDSHB_DEBUG) */

/**************************************
*                                     *
*    Flags for xfdScanData() (V37)    *
*                                     *
**************************************/

/* Bit numbers */
CONST XFDSDB_USEEXTERN          = 0       /* Use external slaves for scanning */
CONST XFDSDB_SCANODD            = 1       /* Scan at odd addresses too */

/* Bit masks */
CONST XFDSDF_USEEXTERN          = $0001   /* (1<<XFDSDB_USEEXTERN) */
CONST XFDSDF_SCANODD            = $0002   /* (1<<XFDSDB_SCANODD) */

/****************
*               *
*    Foreman    *
*               *
****************/

OBJECT xfdForeMan
  xfdf_Security:LONG                      /* moveq #-1,d0 ; rts */
  xfdf_ID:LONG                            /* Set to XFDF_ID */
  xfdf_Version:INT                        /* Set to XFDF_VERSION */
  xfdf_Reserved:INT                       /* Not used by now, set to NULL */
  xfdf_Next:LONG                          /* PRIVATE! */
  xfdf_SegList:LONG                       /* PRIVATE! */
  xfdf_FirstSlave:PTR TO xfdSlave         /* First slave (see below) */
ENDOBJECT

CONST XFDF_ID                   = "XFDF"
CONST XFDF_VERSION              = 1

/**************
*             *
*    Slave    *
*             *
**************/

OBJECT xfdSlave
  xfds_Next:PTR TO xfdSlave               /* Next slave (or NULL) */
  xfds_Version:INT                        /* Set to XFDS_VERSION */
  xfds_MasterVersion:INT                  /* Minimum XFDM_VERSION required */
  xfds_PackerName:PTR TO CHAR             /* Name of packer ('\0' terminated) */
  xfds_PackerFlags:INT                    /* Flags for packer */
  xfds_MaxSpecialLen:INT                  /* Max. length of special info (eg. password) */
  xfds_RecogBuffer:LONG                   /* buffer recognition code (or NULL) (BOOL (*)())*/
  xfds_DecrunchBuffer:LONG                /* buffer decrunch code (or NULL) (BOOL (*)())*/
  xfds_RecogSegment:LONG                  /* segment recognition code (or NULL) (BOOL (*)())*/
  xfds_DecrunchSegment:LONG               /* segment decrunch code (or NULL) (BOOL (*)())*/
  xfds_SlaveID:INT                        /* (V36) Slave ID (only internal slaves) */
  xfds_ReplaceID:INT                      /* (V36) ID of slave to be replaced */
  xfds_MinBufferSize:LONG                 /* (V36) Min. BufSize for RecogBufferXYZ() */
ENDOBJECT

/* (V37) XFDPFB_DATA: Scan code (or NULL) */
#define xfds_ScanData xfds_RecogSegment         

/* (V37) XFDPFB_DATA: Verify code (or NULL) */
#define xfds_VerifyData xfds_DecrunchSegment    

CONST XFDS_VERSION              = 2



/*********************************************
*                                            *
*    Additional Recognition Results (V38)    *
*                                            *
*********************************************/

OBJECT xfdRecogResult
  xfdrr_MinTargetLen:LONG                 /* Min. required length of target buffer */
  xfdrr_FinalTargetLen:LONG               /* Final length of decrunched file */
  xfdrr_MinSourceLen:LONG                 /* (V39) minimum size of source file */
ENDOBJECT

/*********************************
*                                *
*    Internal Slave IDs (V36)    *
*                                *
*********************************/

CONST XFDID_BASE                        = $8000

CONST XFDID_PowerPacker23               = XFDID_BASE+$0001
CONST XFDID_PowerPacker30               = XFDID_BASE+$0003
CONST XFDID_PowerPacker30Enc            = XFDID_BASE+$0005
CONST XFDID_PowerPacker30Ovl            = XFDID_BASE+$0007
CONST XFDID_PowerPacker40               = XFDID_BASE+$0009
CONST XFDID_PowerPacker40Lib            = XFDID_BASE+$000a
CONST XFDID_PowerPacker40Enc            = XFDID_BASE+$000b
CONST XFDID_PowerPacker40LibEnc         = XFDID_BASE+$000c
CONST XFDID_PowerPacker40Ovl            = XFDID_BASE+$000d
CONST XFDID_PowerPacker40LibOvl         = XFDID_BASE+$000e
CONST XFDID_PowerPackerData             = XFDID_BASE+$000f
CONST XFDID_PowerPackerDataEnc          = XFDID_BASE+$0010
CONST XFDID_ByteKiller13                = XFDID_BASE+$0011
CONST XFDID_ByteKiller20                = XFDID_BASE+$0012
CONST XFDID_ByteKiller30                = XFDID_BASE+$0013
CONST XFDID_ByteKillerPro10             = XFDID_BASE+$0014
CONST XFDID_ByteKillerPro10Pro          = XFDID_BASE+$0015
CONST XFDID_DragPack10                  = XFDID_BASE+$0016
CONST XFDID_TNMCruncher11               = XFDID_BASE+$0017
CONST XFDID_HQCCruncher20               = XFDID_BASE+$0018
CONST XFDID_RSICruncher14               = XFDID_BASE+$0019
CONST XFDID_ANCCruncher                 = XFDID_BASE+$001a
CONST XFDID_ReloKit10                   = XFDID_BASE+$001b
CONST XFDID_HighPressureCruncher        = XFDID_BASE+$001c
CONST XFDID_STPackedSong                = XFDID_BASE+$001d
CONST XFDID_TSKCruncher                 = XFDID_BASE+$001e
CONST XFDID_LightPack15                 = XFDID_BASE+$001f
CONST XFDID_CrunchMaster10              = XFDID_BASE+$0020
CONST XFDID_HQCCompressor100            = XFDID_BASE+$0021
CONST XFDID_FlashSpeed10                = XFDID_BASE+$0022
CONST XFDID_CrunchManiaData             = XFDID_BASE+$0023
CONST XFDID_CrunchManiaDataEnc          = XFDID_BASE+$0024
CONST XFDID_CrunchManiaLib              = XFDID_BASE+$0025
CONST XFDID_CrunchManiaNormal           = XFDID_BASE+$0026
CONST XFDID_CrunchManiaSimple           = XFDID_BASE+$0027
CONST XFDID_CrunchManiaAddr             = XFDID_BASE+$0028
CONST XFDID_DefJamCruncher32            = XFDID_BASE+$0029
CONST XFDID_DefJamCruncher32Pro         = XFDID_BASE+$002a
CONST XFDID_TetraPack102                = XFDID_BASE+$002b
CONST XFDID_TetraPack11                 = XFDID_BASE+$002c
CONST XFDID_TetraPack21                 = XFDID_BASE+$002d
CONST XFDID_TetraPack21Pro              = XFDID_BASE+$002e
CONST XFDID_TetraPack22                 = XFDID_BASE+$002f
CONST XFDID_TetraPack22Pro              = XFDID_BASE+$0030
CONST XFDID_DoubleAction10              = XFDID_BASE+$0031
CONST XFDID_DragPack252Data             = XFDID_BASE+$0032
CONST XFDID_DragPack252                 = XFDID_BASE+$0033
CONST XFDID_FCG10                       = XFDID_BASE+$0034
CONST XFDID_Freeway07                   = XFDID_BASE+$0035
CONST XFDID_IAMPacker10ATM5Data         = XFDID_BASE+$0036
CONST XFDID_IAMPacker10ATM5             = XFDID_BASE+$0037
CONST XFDID_IAMPacker10ICEData          = XFDID_BASE+$0038
CONST XFDID_IAMPacker10ICE              = XFDID_BASE+$0039
CONST XFDID_Imploder                    = XFDID_BASE+$003a
CONST XFDID_ImploderLib                 = XFDID_BASE+$003b
CONST XFDID_ImploderOvl                 = XFDID_BASE+$003c
CONST XFDID_FileImploder                = XFDID_BASE+$003d
CONST XFDID_MasterCruncher30Addr        = XFDID_BASE+$003f
CONST XFDID_MasterCruncher30            = XFDID_BASE+$0040
CONST XFDID_MaxPacker12                 = XFDID_BASE+$0041
CONST XFDID_PackIt10Data                = XFDID_BASE+$0042
CONST XFDID_PackIt10                    = XFDID_BASE+$0043
CONST XFDID_PMCNormal                   = XFDID_BASE+$0044
CONST XFDID_PMCSample                   = XFDID_BASE+$0045
CONST XFDID_XPKPacked                   = XFDID_BASE+$0046
CONST XFDID_XPKCrypted                  = XFDID_BASE+$0047
CONST XFDID_TimeCruncher17              = XFDID_BASE+$0048
CONST XFDID_TFACruncher154              = XFDID_BASE+$0049
CONST XFDID_TurtleSmasher13             = XFDID_BASE+$004a
CONST XFDID_MegaCruncher10              = XFDID_BASE+$004b
CONST XFDID_MegaCruncher12              = XFDID_BASE+$004c
CONST XFDID_ProPack                     = XFDID_BASE+$004d
CONST XFDID_ProPackData                 = XFDID_BASE+$004e
CONST XFDID_ProPackDataKey              = XFDID_BASE+$004f
CONST XFDID_STCruncher10                = XFDID_BASE+$0050
CONST XFDID_STCruncher10Data            = XFDID_BASE+$0051
CONST XFDID_SpikeCruncher               = XFDID_BASE+$0052
CONST XFDID_SyncroPacker46              = XFDID_BASE+$0053
CONST XFDID_SyncroPacker46Pro           = XFDID_BASE+$0054
CONST XFDID_TitanicsCruncher11          = XFDID_BASE+$0055
CONST XFDID_TitanicsCruncher12          = XFDID_BASE+$0056
CONST XFDID_TryItCruncher101            = XFDID_BASE+$0057
CONST XFDID_TurboSqueezer61             = XFDID_BASE+$0058
CONST XFDID_TurboSqueezer80             = XFDID_BASE+$0059
CONST XFDID_TurtleSmasher200            = XFDID_BASE+$005a
CONST XFDID_TurtleSmasher200Data        = XFDID_BASE+$005b
CONST XFDID_StoneCracker270             = XFDID_BASE+$005c
CONST XFDID_StoneCracker270Pro          = XFDID_BASE+$005d
CONST XFDID_StoneCracker292             = XFDID_BASE+$005e
CONST XFDID_StoneCracker299             = XFDID_BASE+$005f
CONST XFDID_StoneCracker299d            = XFDID_BASE+$0060
CONST XFDID_StoneCracker300             = XFDID_BASE+$0061
CONST XFDID_StoneCracker300Data         = XFDID_BASE+$0062
CONST XFDID_StoneCracker310             = XFDID_BASE+$0063
CONST XFDID_StoneCracker310Data         = XFDID_BASE+$0064
CONST XFDID_StoneCracker311             = XFDID_BASE+$0065
CONST XFDID_StoneCracker400             = XFDID_BASE+$0066
CONST XFDID_StoneCracker400Data         = XFDID_BASE+$0067
CONST XFDID_StoneCracker401             = XFDID_BASE+$0068
CONST XFDID_StoneCracker401Data         = XFDID_BASE+$0069
CONST XFDID_StoneCracker401Addr         = XFDID_BASE+$006a
CONST XFDID_StoneCracker401BetaAddr     = XFDID_BASE+$006b
CONST XFDID_StoneCracker403Data         = XFDID_BASE+$006c
CONST XFDID_StoneCracker404             = XFDID_BASE+$006d
CONST XFDID_StoneCracker404Data         = XFDID_BASE+$006e
CONST XFDID_StoneCracker404Addr         = XFDID_BASE+$006f
CONST XFDID_ChryseisCruncher09          = XFDID_BASE+$0070
CONST XFDID_QuickPowerPacker10          = XFDID_BASE+$0071
CONST XFDID_GNUPacker12                 = XFDID_BASE+$0072
CONST XFDID_GNUPacker12Seg              = XFDID_BASE+$0073
CONST XFDID_GNUPacker12Data             = XFDID_BASE+$0074
CONST XFDID_TrashEliminator10           = XFDID_BASE+$0075
CONST XFDID_MasterCruncher30Data        = XFDID_BASE+$0076
CONST XFDID_SuperCruncher27             = XFDID_BASE+$0077
CONST XFDID_UltimatePacker11            = XFDID_BASE+$0078
CONST XFDID_ProPackOld                  = XFDID_BASE+$0079
CONST XFDID_SACFPQCruncher              = XFDID_BASE+$007a /* disabled */
CONST XFDID_PowerPackerPatch10          = XFDID_BASE+$007b
CONST XFDID_CFP135                      = XFDID_BASE+$007c
CONST XFDID_BOND                        = XFDID_BASE+$007d
CONST XFDID_PowerPackerLoadSeg          = XFDID_BASE+$007e
CONST XFDID_StoneCracker299b            = XFDID_BASE+$007f
CONST XFDID_CrunchyDat10                = XFDID_BASE+$0080
CONST XFDID_PowerPacker20               = XFDID_BASE+$0081
CONST XFDID_StoneCracker403             = XFDID_BASE+$0082
CONST XFDID_PKProtector200              = XFDID_BASE+$0083
CONST XFDID_PPbk                        = XFDID_BASE+$0084
CONST XFDID_StoneCracker292Data         = XFDID_BASE+$0085
CONST XFDID_MegaCruncherObj             = XFDID_BASE+$0086
CONST XFDID_DeluxeCruncher1             = XFDID_BASE+$0087
CONST XFDID_DeluxeCruncher3             = XFDID_BASE+$0088
CONST XFDID_ByteKiller97                = XFDID_BASE+$0089
CONST XFDID_TurboSqueezer51             = XFDID_BASE+$008A
CONST XFDID_SubPacker10                 = XFDID_BASE+$008B
CONST XFDID_StoneCracker404Lib          = XFDID_BASE+$008C
CONST XFDID_ISC_Pass1                   = XFDID_BASE+$008D
CONST XFDID_ISC_Pass2                   = XFDID_BASE+$008E
CONST XFDID_ISC_Pass3                   = XFDID_BASE+$008F
CONST XFDID_PCompressFALH               = XFDID_BASE+$0090
CONST XFDID_PCompressHILH               = XFDID_BASE+$0091
CONST XFDID_SMF                         = XFDID_BASE+$0092
CONST XFDID_DefJamCruncher32T           = XFDID_BASE+$0093
