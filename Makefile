# Linux host build. Legacy .dll/.exe names preserve Python tool-path contracts;
# these outputs are native ELF files, not Windows binaries.
CC ?= cc
CFLAGS ?= -O2 -g
CPPFLAGS += -Isrc -D_POSIX_C_SOURCE=200809L
CFLAGS += -std=c11 -fPIC -Wall -Wextra
LDLIBS += -lm -lcrypto
BUILD := src/build
MAINS := src/m68k_assembler_main.c src/platform_disk_cli.c src/platform_file_cli.c
CORE := $(filter-out $(MAINS) src/m68k_c_unit_test.c $(wildcard src/test_*.c),$(wildcard src/*.c)) $(wildcard src/generated/*.c)
OBJECTS := $(patsubst src/%.c,$(BUILD)/linux/%.o,$(CORE))
LIBS := m68k_assembler_lib.dll m68k_disassembler_lib.dll platform_file_lib.dll platform_disk_lib.dll
PROGRAMS := m68k_assembler_app.exe platform_file_cli.exe platform_disk_cli.exe m68k_c_unit_tests.exe
.PHONY: all test
all: $(addprefix $(BUILD)/,$(LIBS) $(PROGRAMS))
$(BUILD)/linux/%.o: src/%.c
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@
$(BUILD)/libamiga_backend.so: $(OBJECTS)
	$(CC) -shared -Wl,-z,defs -o $@ $^ $(LDLIBS)
$(addprefix $(BUILD)/,$(LIBS)): $(BUILD)/libamiga_backend.so
	ln -sf libamiga_backend.so $@
$(BUILD)/m68k_assembler_app.exe: $(BUILD)/linux/m68k_assembler_main.o $(BUILD)/libamiga_backend.so
	$(CC) -o $@ $< -L$(BUILD) -lamiga_backend -Wl,-rpath,'$$ORIGIN' $(LDLIBS)
$(BUILD)/platform_file_cli.exe: $(BUILD)/linux/platform_file_cli.o $(BUILD)/libamiga_backend.so
	$(CC) -o $@ $< -L$(BUILD) -lamiga_backend -Wl,-rpath,'$$ORIGIN' $(LDLIBS)
$(BUILD)/platform_disk_cli.exe: $(BUILD)/linux/platform_disk_cli.o $(BUILD)/libamiga_backend.so
	$(CC) -o $@ $< -L$(BUILD) -lamiga_backend -Wl,-rpath,'$$ORIGIN' $(LDLIBS)
TEST_OBJECTS := $(patsubst src/%.c,$(BUILD)/linux/%.o,$(wildcard src/test_*.c) src/m68k_c_unit_test.c)
$(BUILD)/m68k_c_unit_tests.exe: $(TEST_OBJECTS) $(BUILD)/libamiga_backend.so
	$(CC) -o $@ $(TEST_OBJECTS) -L$(BUILD) -lamiga_backend -Wl,-rpath,'$$ORIGIN' $(LDLIBS)
test: all
	$(BUILD)/m68k_c_unit_tests.exe
-include $(OBJECTS:.o=.d) $(TEST_OBJECTS:.o=.d) $(patsubst src/%.c,$(BUILD)/linux/%.d,$(MAINS))
