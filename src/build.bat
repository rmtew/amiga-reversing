@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b %errorlevel%

set OUTDIR=src\build
set EXE=%OUTDIR%\m68k_assembler_app.exe
set C_TEST_EXE=%OUTDIR%\m68k_c_unit_tests.exe
set ASM_DLL=%OUTDIR%\m68k_assembler_lib.dll
set DISASM_DLL=%OUTDIR%\m68k_disassembler_lib.dll
set DISK_EXE=%OUTDIR%\platform_disk_cli.exe
set DISK_DLL=%OUTDIR%\platform_disk_lib.dll
set FILE_EXE=%OUTDIR%\platform_file_cli.exe
set FILE_DLL=%OUTDIR%\platform_file_lib.dll
set CFLAGS=/nologo /W4 /WX /std:c11 /D_CRT_SECURE_NO_WARNINGS /I src
set LDFLAGS=/nologo

if not exist %OUTDIR% mkdir %OUTDIR%

cl %CFLAGS% /c /Fo%OUTDIR%\ ^
    src\m68k_asm_tables.c ^
    src\m68k_assembler.c ^
    src\m68k_assembler_api.c ^
    src\m68k_source_ir_api.c ^
    src\m68k_assembler_app.c ^
    src\m68k_assembler_main.c ^
    src\m68k_assembler_verify.c ^
    src\m68k_corpus_support.c ^
    src\m68k_corpus_spec.c ^
    src\m68k_instruction_spec.c ^
    src\m68k_plain_parse.c ^
    src\m68k_simple_source.c ^
    src\m68k_disassembler.c ^
    src\m68k_disassembler_lib.c ^
    src\m68k_simulator.c ^
    src\m68k_ir.c ^
    src\m68k_ir_codec.c ^
    src\m68k_ir_parse.c ^
    src\m68k_ir_symbol_resolve.c ^
    src\m68k_parse_util.c ^
    src\util_arena.c ^
    src\m68k_c_unit_test.c ^
    src\test_m68k_parse_util.c ^
    src\test_m68k_instruction_spec.c ^
    src\test_m68k_ir.c ^
    src\test_m68k_c_main.c ^
    src\m68k_source_ir_render.c ^
    src\m68k_source_model.c ^
    src\m68k_source_pipeline.c ^
    src\m68k_source_instruction_resolve.c ^
    src\m68k_source_constant_expr.c ^
    src\m68k_source_data.c ^
    src\m68k_source_expr.c ^
    src\m68k_source_file_emit.c ^
    src\m68k_source_file_parse.c ^
    src\m68k_source_include.c ^
    src\m68k_source_resolve_rewrite.c ^
    src\m68k_source_rewrite.c ^
    src\m68k_symbolic_parse.c ^
    src\m68k_source_text_util.c ^
    src\platform_common.c ^
    src\platform_binary_io.c ^
    src\platform_disk_cli.c ^
    src\platform_disk_lib.c ^
    src\platform_file_cli.c ^
    src\platform_file_lib.c ^
    src\json_builder.c ^
    src\m68k_object.c ^
    src\platform_amiga_hunk.c ^
    src\platform_amiga_disk.c ^
    src\platform_atari_st.c ^
    src\platform_atari_st_disk.c ^
    src\generated\amiga_hunk_file_runtime.c ^
    src\generated\amiga_disk_file_runtime.c ^
    src\generated\atari_st_prg_file_runtime.c ^
    src\generated\atari_st_disk_file_runtime.c || exit /b %errorlevel%

cl %CFLAGS% /DM68K_ASSEMBLER_BUILD_DLL /c /Fo%OUTDIR%\m68k_source_ir_api_dll.obj src\m68k_source_ir_api.c || exit /b %errorlevel%

link %LDFLAGS% /OUT:%EXE% ^
    %OUTDIR%\m68k_assembler_main.obj ^
    %OUTDIR%\m68k_assembler_app.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_assembler_api.obj ^
    %OUTDIR%\m68k_source_ir_api.obj ^
    %OUTDIR%\m68k_assembler_verify.obj ^
    %OUTDIR%\m68k_corpus_support.obj ^
    %OUTDIR%\m68k_corpus_spec.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_simple_source.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_ir_parse.obj ^
    %OUTDIR%\m68k_ir_symbol_resolve.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\m68k_source_ir_render.obj ^
    %OUTDIR%\m68k_source_model.obj ^
    %OUTDIR%\m68k_source_pipeline.obj ^
    %OUTDIR%\m68k_source_instruction_resolve.obj ^
    %OUTDIR%\m68k_source_constant_expr.obj ^
    %OUTDIR%\m68k_source_data.obj ^
    %OUTDIR%\m68k_source_expr.obj ^
    %OUTDIR%\m68k_source_file_emit.obj ^
    %OUTDIR%\m68k_source_file_parse.obj ^
    %OUTDIR%\m68k_source_include.obj ^
    %OUTDIR%\m68k_source_resolve_rewrite.obj ^
    %OUTDIR%\m68k_source_rewrite.obj ^
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /OUT:%C_TEST_EXE% ^
    %OUTDIR%\test_m68k_c_main.obj ^
    %OUTDIR%\test_m68k_parse_util.obj ^
    %OUTDIR%\test_m68k_instruction_spec.obj ^
    %OUTDIR%\test_m68k_ir.obj ^
    %OUTDIR%\m68k_c_unit_test.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\platform_common.obj || exit /b %errorlevel%

link %LDFLAGS% /DLL /OUT:%ASM_DLL% /EXPORT:m68k_source_ir_parse_file /EXPORT:m68k_source_ir_render_with_policy /EXPORT:m68k_source_ir_free /EXPORT:m68k_free_text ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_assembler_api.obj ^
    %OUTDIR%\m68k_source_ir_api_dll.obj ^
    %OUTDIR%\m68k_assembler_verify.obj ^
    %OUTDIR%\m68k_corpus_support.obj ^
    %OUTDIR%\m68k_corpus_spec.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_simple_source.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_ir_parse.obj ^
    %OUTDIR%\m68k_ir_symbol_resolve.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\m68k_source_ir_render.obj ^
    %OUTDIR%\m68k_source_model.obj ^
    %OUTDIR%\m68k_source_pipeline.obj ^
    %OUTDIR%\m68k_source_instruction_resolve.obj ^
    %OUTDIR%\m68k_source_constant_expr.obj ^
    %OUTDIR%\m68k_source_data.obj ^
    %OUTDIR%\m68k_source_expr.obj ^
    %OUTDIR%\m68k_source_file_emit.obj ^
    %OUTDIR%\m68k_source_file_parse.obj ^
    %OUTDIR%\m68k_source_include.obj ^
    %OUTDIR%\m68k_source_resolve_rewrite.obj ^
    %OUTDIR%\m68k_source_rewrite.obj ^
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /DLL /OUT:%DISASM_DLL% ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_disassembler_lib.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj || exit /b %errorlevel%

link %LDFLAGS% /OUT:%DISK_EXE% ^
    %OUTDIR%\platform_disk_cli.obj ^
    %OUTDIR%\platform_disk_lib.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_disk.obj ^
    %OUTDIR%\platform_atari_st_disk.obj ^
    %OUTDIR%\amiga_disk_file_runtime.obj ^
    %OUTDIR%\atari_st_disk_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /DLL /OUT:%DISK_DLL% ^
    %OUTDIR%\platform_disk_lib.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_disk.obj ^
    %OUTDIR%\platform_atari_st_disk.obj ^
    %OUTDIR%\amiga_disk_file_runtime.obj ^
    %OUTDIR%\atari_st_disk_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /OUT:%FILE_EXE% ^
    %OUTDIR%\platform_file_cli.obj ^
    %OUTDIR%\platform_file_lib.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\m68k_source_ir_api_dll.obj ^
    %OUTDIR%\m68k_assembler_api.obj ^
    %OUTDIR%\m68k_corpus_support.obj ^
    %OUTDIR%\m68k_corpus_spec.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_simple_source.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_ir_parse.obj ^
    %OUTDIR%\m68k_ir_symbol_resolve.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\m68k_source_ir_render.obj ^
    %OUTDIR%\m68k_source_model.obj ^
    %OUTDIR%\m68k_source_pipeline.obj ^
    %OUTDIR%\m68k_source_instruction_resolve.obj ^
    %OUTDIR%\m68k_source_constant_expr.obj ^
    %OUTDIR%\m68k_source_data.obj ^
    %OUTDIR%\m68k_source_expr.obj ^
    %OUTDIR%\m68k_source_file_emit.obj ^
    %OUTDIR%\m68k_source_file_parse.obj ^
    %OUTDIR%\m68k_source_include.obj ^
    %OUTDIR%\m68k_source_resolve_rewrite.obj ^
    %OUTDIR%\m68k_source_rewrite.obj ^
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_disassembler_lib.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /DLL /OUT:%FILE_DLL% /EXPORT:platform_file_analyze_path_json ^
    %OUTDIR%\platform_file_lib.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\m68k_source_ir_api_dll.obj ^
    %OUTDIR%\m68k_assembler_api.obj ^
    %OUTDIR%\m68k_corpus_support.obj ^
    %OUTDIR%\m68k_corpus_spec.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_simple_source.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_ir_parse.obj ^
    %OUTDIR%\m68k_ir_symbol_resolve.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\m68k_source_ir_render.obj ^
    %OUTDIR%\m68k_source_model.obj ^
    %OUTDIR%\m68k_source_pipeline.obj ^
    %OUTDIR%\m68k_source_instruction_resolve.obj ^
    %OUTDIR%\m68k_source_constant_expr.obj ^
    %OUTDIR%\m68k_source_data.obj ^
    %OUTDIR%\m68k_source_expr.obj ^
    %OUTDIR%\m68k_source_file_emit.obj ^
    %OUTDIR%\m68k_source_file_parse.obj ^
    %OUTDIR%\m68k_source_include.obj ^
    %OUTDIR%\m68k_source_resolve_rewrite.obj ^
    %OUTDIR%\m68k_source_rewrite.obj ^
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_disassembler_lib.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj || exit /b %errorlevel%

if "%1"=="" exit /b 0
set CMD=%1

if "%CMD%"=="verify-corpus" (
    %EXE% verify src\tests\generated\all_cases.txt src\tests\generated\all_cases.bin
    exit /b %errorlevel%
)
if "%CMD%"=="verify-manifest" (
    %EXE% %*
    exit /b %errorlevel%
)
if "%CMD%"=="assemble-case" (
    %EXE% %*
    exit /b %errorlevel%
)
if "%CMD%"=="assemble-manifest" (
    %EXE% %*
    exit /b %errorlevel%
)
if "%CMD%"=="assemble-line" (
    %EXE% %*
    exit /b %errorlevel%
)
if "%CMD%"=="assemble-file" (
    %EXE% %*
    exit /b %errorlevel%
)
if "%CMD%"=="assemble-platform-file" (
    %EXE% %*
    exit /b %errorlevel%
)
if "%CMD%"=="inspect-disk" (
    %DISK_EXE% %*
    exit /b %errorlevel%
)
if "%CMD%"=="inspect-file" (
    %FILE_EXE% %*
    exit /b %errorlevel%
)
if "%CMD%"=="disassemble-file" (
    %FILE_EXE% %*
    exit /b %errorlevel%
)

echo unknown command: %CMD% 1>&2
exit /b 2
