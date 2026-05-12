@echo off
setlocal
if /I "%~1"=="--lock-held" goto :shift_to_main
if not defined AMIGA_BUILD_LOCK_HELD goto :lock_wrap
:main
goto :main_start
:shift_to_main
shift
:main_start
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
set ANCIENT_EXE=ext\tools\ancient\Ancient.exe
set ANCIENT_SRC_DIR=resources\clone_common\ancient
set ANCIENT_BUILD_EXE=%ANCIENT_SRC_DIR%\src\build\Ancient.exe
set CFLAGS=/nologo /W4 /WX /std:c11 /D_CRT_SECURE_NO_WARNINGS /I src
set LDFLAGS=/nologo
if /I "%AMIGA_BUILD_CONFIG%"=="debug" (
    set CFLAGS=%CFLAGS% /Od /Zi
    set LDFLAGS=%LDFLAGS% /DEBUG
) else (
    set CFLAGS=%CFLAGS% /O2 /Oi
)

if not exist %OUTDIR% mkdir %OUTDIR%
if /I "%~1"=="build-ancient-provider" goto :build_ancient_provider
if not exist "%ANCIENT_EXE%" (
    echo Missing Ancient decompression provider: %ANCIENT_EXE%
    exit /b 1
)

cl %CFLAGS% /c /Fo%OUTDIR%\ ^
    src\generated\m68k_asm_tables.c ^
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
    src\m68k_decode_ir.c ^
    src\m68k_fact_ir.c ^
    src\m68k_render_ir.c ^
    src\m68k_render_plan.c ^
    src\m68k_analysis_render_lookup.c ^
    src\m68k_analysis_facts_v2.c ^
    src\m68k_ir.c ^
    src\m68k_ir_codec.c ^
    src\m68k_ir_parse.c ^
    src\m68k_ir_symbol_resolve.c ^
    src\m68k_parse_util.c ^
    src\m68k_diagnostics.c ^
    src\util_arena.c ^
    src\m68k_c_unit_test.c ^
    src\test_m68k_parse_util.c ^
    src\test_m68k_instruction_spec.c ^
    src\test_m68k_ir.c ^
    src\test_m68k_simulator.c ^
    src\test_m68k_render_plan.c ^
    src\test_m68k_diagnostics.c ^
    src\test_platform_decompression.c ^
    src\test_m68k_container_metadata.c ^
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
    src\m68k_symbolic_parse.c ^
    src\m68k_source_text_util.c ^
    src\platform_common.c ^
    src\platform_facts_v2.c ^
    src\platform_name_table.c ^
    src\platform_binary_io.c ^
    src\platform_disk_cli.c ^
    src\platform_disk_lib.c ^
    src\platform_file_cli.c ^
    src\platform_file_lib.c ^
    src\platform_file_core.c ^
    src\platform_file_amiga.c ^
    src\platform_file_atari_st.c ^
    src\platform_file_platform.c ^
    src\platform_file_json.c ^
    src\platform_file_decompression.c ^
    src\json_builder.c ^
    src\m68k_object.c ^
    src\platform_amiga_hunk.c ^
    src\platform_amiga_bootloader_analysis.c ^
    src\platform_amiga_disk.c ^
    src\platform_atari_st.c ^
    src\platform_atari_st_disk.c ^
    src\generated\amiga_os_runtime.c ^
    src\generated\atari_st_os_runtime.c ^
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
    %OUTDIR%\m68k_decode_ir.obj ^
    %OUTDIR%\m68k_fact_ir.obj ^
    %OUTDIR%\m68k_render_ir.obj ^
    %OUTDIR%\m68k_render_plan.obj ^
    %OUTDIR%\m68k_analysis_render_lookup.obj ^
    %OUTDIR%\m68k_analysis_facts_v2.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_simple_source.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_ir_parse.obj ^
    %OUTDIR%\m68k_ir_symbol_resolve.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\m68k_diagnostics.obj ^
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
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_facts_v2.obj ^
    %OUTDIR%\platform_name_table.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\amiga_os_runtime.obj ^
    %OUTDIR%\atari_st_os_runtime.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /OUT:%C_TEST_EXE% ^
    %OUTDIR%\test_m68k_c_main.obj ^
    %OUTDIR%\test_m68k_parse_util.obj ^
    %OUTDIR%\test_m68k_instruction_spec.obj ^
    %OUTDIR%\test_m68k_ir.obj ^
    %OUTDIR%\test_m68k_simulator.obj ^
    %OUTDIR%\test_m68k_render_plan.obj ^
    %OUTDIR%\test_m68k_diagnostics.obj ^
    %OUTDIR%\test_platform_decompression.obj ^
    %OUTDIR%\test_m68k_container_metadata.obj ^
    %OUTDIR%\m68k_c_unit_test.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_decode_ir.obj ^
    %OUTDIR%\m68k_fact_ir.obj ^
    %OUTDIR%\m68k_render_ir.obj ^
    %OUTDIR%\m68k_render_plan.obj ^
    %OUTDIR%\m68k_analysis_render_lookup.obj ^
    %OUTDIR%\m68k_analysis_facts_v2.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_ir_symbol_resolve.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\m68k_source_model.obj ^
    %OUTDIR%\m68k_source_pipeline.obj ^
    %OUTDIR%\m68k_source_instruction_resolve.obj ^
    %OUTDIR%\m68k_source_constant_expr.obj ^
    %OUTDIR%\m68k_source_data.obj ^
    %OUTDIR%\m68k_source_expr.obj ^
    %OUTDIR%\m68k_source_file_emit.obj ^
    %OUTDIR%\m68k_source_file_parse.obj ^
    %OUTDIR%\m68k_source_include.obj ^
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_diagnostics.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\m68k_source_ir_render.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\platform_file_core.obj ^
    %OUTDIR%\platform_file_amiga.obj ^
    %OUTDIR%\platform_file_atari_st.obj ^
    %OUTDIR%\platform_file_platform.obj ^
    %OUTDIR%\platform_file_json.obj ^
    %OUTDIR%\platform_file_decompression.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\amiga_os_runtime.obj ^
    %OUTDIR%\atari_st_os_runtime.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_facts_v2.obj ^
    %OUTDIR%\platform_name_table.obj || exit /b %errorlevel%

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
    %OUTDIR%\m68k_diagnostics.obj ^
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
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_name_table.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\amiga_os_runtime.obj ^
    %OUTDIR%\atari_st_os_runtime.obj ^
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
    %OUTDIR%\m68k_diagnostics.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\amiga_os_runtime.obj ^
    %OUTDIR%\atari_st_os_runtime.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_name_table.obj || exit /b %errorlevel%

link %LDFLAGS% /OUT:%DISK_EXE% ^
    %OUTDIR%\platform_disk_cli.obj ^
    %OUTDIR%\platform_disk_lib.obj ^
    %OUTDIR%\platform_file_lib.obj ^
    %OUTDIR%\m68k_assembler_app.obj ^
    %OUTDIR%\platform_file_core.obj ^
    %OUTDIR%\platform_file_amiga.obj ^
    %OUTDIR%\platform_file_atari_st.obj ^
    %OUTDIR%\platform_file_platform.obj ^
    %OUTDIR%\platform_file_json.obj ^
    %OUTDIR%\platform_file_decompression.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_facts_v2.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_decode_ir.obj ^
    %OUTDIR%\m68k_fact_ir.obj ^
    %OUTDIR%\m68k_render_ir.obj ^
    %OUTDIR%\m68k_render_plan.obj ^
    %OUTDIR%\m68k_analysis_render_lookup.obj ^
    %OUTDIR%\m68k_analysis_facts_v2.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\m68k_source_ir_api_dll.obj ^
    %OUTDIR%\m68k_assembler_api.obj ^
    %OUTDIR%\m68k_corpus_support.obj ^
    %OUTDIR%\m68k_corpus_spec.obj ^
    %OUTDIR%\m68k_simple_source.obj ^
    %OUTDIR%\m68k_ir_parse.obj ^
    %OUTDIR%\m68k_ir_symbol_resolve.obj ^
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
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler_lib.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\platform_name_table.obj ^
    %OUTDIR%\amiga_os_runtime.obj ^
    %OUTDIR%\atari_st_os_runtime.obj ^
    %OUTDIR%\m68k_diagnostics.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_bootloader_analysis.obj ^
    %OUTDIR%\platform_amiga_disk.obj ^
    %OUTDIR%\platform_atari_st_disk.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\amiga_disk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj ^
    %OUTDIR%\atari_st_disk_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /DLL /OUT:%DISK_DLL% ^
    %OUTDIR%\platform_disk_lib.obj ^
    %OUTDIR%\platform_file_lib.obj ^
    %OUTDIR%\m68k_assembler_app.obj ^
    %OUTDIR%\platform_file_core.obj ^
    %OUTDIR%\platform_file_amiga.obj ^
    %OUTDIR%\platform_file_atari_st.obj ^
    %OUTDIR%\platform_file_platform.obj ^
    %OUTDIR%\platform_file_json.obj ^
    %OUTDIR%\platform_file_decompression.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_facts_v2.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_decode_ir.obj ^
    %OUTDIR%\m68k_fact_ir.obj ^
    %OUTDIR%\m68k_render_ir.obj ^
    %OUTDIR%\m68k_render_plan.obj ^
    %OUTDIR%\m68k_analysis_render_lookup.obj ^
    %OUTDIR%\m68k_analysis_facts_v2.obj ^
    %OUTDIR%\m68k_ir.obj ^
    %OUTDIR%\m68k_ir_codec.obj ^
    %OUTDIR%\m68k_parse_util.obj ^
    %OUTDIR%\m68k_instruction_spec.obj ^
    %OUTDIR%\m68k_plain_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\m68k_source_ir_api_dll.obj ^
    %OUTDIR%\m68k_assembler_api.obj ^
    %OUTDIR%\m68k_corpus_support.obj ^
    %OUTDIR%\m68k_corpus_spec.obj ^
    %OUTDIR%\m68k_simple_source.obj ^
    %OUTDIR%\m68k_ir_parse.obj ^
    %OUTDIR%\m68k_ir_symbol_resolve.obj ^
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
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler_lib.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\platform_name_table.obj ^
    %OUTDIR%\amiga_os_runtime.obj ^
    %OUTDIR%\atari_st_os_runtime.obj ^
    %OUTDIR%\m68k_diagnostics.obj ^
    %OUTDIR%\util_arena.obj ^
    %OUTDIR%\json_builder.obj ^
    %OUTDIR%\platform_amiga_bootloader_analysis.obj ^
    %OUTDIR%\platform_amiga_disk.obj ^
    %OUTDIR%\platform_atari_st_disk.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\amiga_disk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj ^
    %OUTDIR%\atari_st_disk_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /OUT:%FILE_EXE% ^
    %OUTDIR%\platform_file_cli.obj ^
    %OUTDIR%\platform_file_lib.obj ^
    %OUTDIR%\m68k_assembler_app.obj ^
    %OUTDIR%\platform_file_core.obj ^
    %OUTDIR%\platform_file_amiga.obj ^
    %OUTDIR%\platform_file_atari_st.obj ^
    %OUTDIR%\platform_file_platform.obj ^
    %OUTDIR%\platform_file_json.obj ^
    %OUTDIR%\platform_file_decompression.obj ^
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
    %OUTDIR%\m68k_diagnostics.obj ^
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
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_facts_v2.obj ^
    %OUTDIR%\platform_name_table.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_decode_ir.obj ^
    %OUTDIR%\m68k_fact_ir.obj ^
    %OUTDIR%\m68k_render_ir.obj ^
    %OUTDIR%\m68k_render_plan.obj ^
    %OUTDIR%\m68k_analysis_render_lookup.obj ^
    %OUTDIR%\m68k_analysis_facts_v2.obj ^
    %OUTDIR%\m68k_disassembler_lib.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\amiga_os_runtime.obj ^
    %OUTDIR%\atari_st_os_runtime.obj ^
    %OUTDIR%\amiga_hunk_file_runtime.obj ^
    %OUTDIR%\atari_st_prg_file_runtime.obj || exit /b %errorlevel%

link %LDFLAGS% /DLL /OUT:%FILE_DLL% ^
    %OUTDIR%\platform_file_lib.obj ^
    %OUTDIR%\m68k_assembler_app.obj ^
    %OUTDIR%\platform_file_core.obj ^
    %OUTDIR%\platform_file_amiga.obj ^
    %OUTDIR%\platform_file_atari_st.obj ^
    %OUTDIR%\platform_file_platform.obj ^
    %OUTDIR%\platform_file_json.obj ^
    %OUTDIR%\platform_file_decompression.obj ^
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
    %OUTDIR%\m68k_diagnostics.obj ^
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
    %OUTDIR%\m68k_symbolic_parse.obj ^
    %OUTDIR%\m68k_source_text_util.obj ^
    %OUTDIR%\platform_common.obj ^
    %OUTDIR%\platform_facts_v2.obj ^
    %OUTDIR%\platform_name_table.obj ^
    %OUTDIR%\platform_binary_io.obj ^
    %OUTDIR%\m68k_disassembler.obj ^
    %OUTDIR%\m68k_decode_ir.obj ^
    %OUTDIR%\m68k_fact_ir.obj ^
    %OUTDIR%\m68k_render_ir.obj ^
    %OUTDIR%\m68k_render_plan.obj ^
    %OUTDIR%\m68k_analysis_render_lookup.obj ^
    %OUTDIR%\m68k_analysis_facts_v2.obj ^
    %OUTDIR%\m68k_disassembler_lib.obj ^
    %OUTDIR%\m68k_simulator.obj ^
    %OUTDIR%\m68k_asm_tables.obj ^
    %OUTDIR%\m68k_assembler.obj ^
    %OUTDIR%\m68k_object.obj ^
    %OUTDIR%\platform_amiga_hunk.obj ^
    %OUTDIR%\platform_atari_st.obj ^
    %OUTDIR%\amiga_os_runtime.obj ^
    %OUTDIR%\atari_st_os_runtime.obj ^
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
if "%CMD%"=="build-ancient-provider" goto :build_ancient_provider

echo unknown command: %CMD% 1>&2
exit /b 2

:build_ancient_provider
if not exist "%ANCIENT_SRC_DIR%\build.bat" (
    echo Missing local Ancient source clone: %ANCIENT_SRC_DIR%
    exit /b 1
)
call "%ANCIENT_SRC_DIR%\build.bat" Release
if errorlevel 1 exit /b %errorlevel%
if not exist "%ANCIENT_BUILD_EXE%" (
    echo Ancient build did not produce %ANCIENT_BUILD_EXE%
    exit /b 1
)
if not exist "ext\tools\ancient" mkdir "ext\tools\ancient"
copy /Y "%ANCIENT_BUILD_EXE%" "%ANCIENT_EXE%" >nul
if errorlevel 1 exit /b %errorlevel%
echo Updated %ANCIENT_EXE%
exit /b 0

:lock_wrap
set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
set "AMIGA_BUILD_LOCK_SCRIPT=%~f0"
set "AMIGA_BUILD_LOCK_ARGS=%*"
"%PYTHON_EXE%" "%~dp0scripts\with_build_lock.py" --batch-env
exit /b %errorlevel%
