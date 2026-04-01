OUTDIR=src\\build
CC=cl
CFLAGS=/nologo /W4 /WX /std:c11 /D_CRT_SECURE_NO_WARNINGS /I src
LDFLAGS=/nologo

OBJS=$(OUTDIR)\\m68k_asm_tables.obj $(OUTDIR)\\m68k_assembler.obj $(OUTDIR)\\m68k_source_ir_api.obj
EXE=$(OUTDIR)\\m68k_assembler_app.exe

all: $(EXE)

$(OUTDIR):
	if not exist $(OUTDIR) mkdir $(OUTDIR)

$(OUTDIR)\\m68k_asm_tables.obj: src\\m68k_asm_tables.c src\\m68k_asm_tables.h $(OUTDIR)
	$(CC) $(CFLAGS) /c /Fo$@ src\\m68k_asm_tables.c

$(OUTDIR)\\m68k_assembler.obj: src\\m68k_assembler.c src\\m68k_assembler.h src\\m68k_asm_tables.h $(OUTDIR)
	$(CC) $(CFLAGS) /c /Fo$@ src\\m68k_assembler.c

$(OUTDIR)\\m68k_source_ir_api.obj: src\\m68k_source_ir_api.c src\\m68k_assembler.h src\\m68k_asm_tables.h $(OUTDIR)
	$(CC) $(CFLAGS) /c /Fo$@ src\\m68k_source_ir_api.c

$(EXE): $(OBJS)
	link $(LDFLAGS) /OUT:$(EXE) $(OBJS)

verify-corpus: $(EXE)
	$(EXE) verify src\\tests\\generated\\all_cases.txt src\\tests\\generated\\all_cases.bin

clean:
	if exist $(OUTDIR) rmdir /s /q $(OUTDIR)
