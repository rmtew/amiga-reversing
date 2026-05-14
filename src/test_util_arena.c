#include "m68k_c_unit_test.h"
#include "m68k_decode_ir.h"
#include "m68k_fact_ir.h"
#include "m68k_object.h"
#include "platform_binary_io.h"
#include "util_arena.h"

#include <string.h>
#include <windows.h>

typedef struct TestPair {
  uint32_t left;
  uint32_t right;
} TestPair;

typedef struct TestVirtualReservedArena {
  unsigned char *base;
  size_t reserve_size;
  size_t page_size;
  size_t committed;
  size_t used;
  size_t peak_used;
  size_t commit_count;
} TestVirtualReservedArena;

typedef struct TestPoolNode {
  uint32_t left;
  uint32_t right;
  uint32_t next;
  uint32_t flags;
} TestPoolNode;

static size_t test_align_up(size_t value, size_t alignment) {
  return (value + alignment - 1U) & ~(alignment - 1U);
}

static int test_virtual_arena_create(TestVirtualReservedArena *arena, size_t reserve_size) {
  SYSTEM_INFO info;
  memset(arena, 0, sizeof(*arena));
  GetSystemInfo(&info);
  arena->page_size = info.dwPageSize;
  arena->reserve_size = test_align_up(reserve_size, arena->page_size);
  arena->base = (unsigned char *)VirtualAlloc(NULL, arena->reserve_size, MEM_RESERVE, PAGE_READWRITE);
  return arena->base != NULL ? 0 : -1;
}

static void test_virtual_arena_destroy(TestVirtualReservedArena *arena) {
  if (arena == NULL) return;
  if (arena->base != NULL) VirtualFree(arena->base, 0U, MEM_RELEASE);
  memset(arena, 0, sizeof(*arena));
}

static void *test_virtual_arena_alloc(TestVirtualReservedArena *arena, size_t size) {
  size_t aligned_size;
  size_t end;
  size_t next_committed;
  void *ptr;
  if (arena == NULL || arena->base == NULL || size == 0U) return NULL;
  aligned_size = test_align_up(size, sizeof(void *));
  if (aligned_size < size || arena->used > arena->reserve_size - aligned_size) return NULL;
  end = arena->used + aligned_size;
  if (end > arena->committed) {
    next_committed = test_align_up(end, arena->page_size);
    if (next_committed > arena->reserve_size) return NULL;
    if (VirtualAlloc(arena->base + arena->committed, next_committed - arena->committed, MEM_COMMIT,
        PAGE_READWRITE) == NULL) {
      return NULL;
    }
    arena->committed = next_committed;
    arena->commit_count += 1U;
  }
  ptr = arena->base + arena->used;
  arena->used = end;
  if (arena->used > arena->peak_used) arena->peak_used = arena->used;
  return ptr;
}

static void test_virtual_arena_reset(TestVirtualReservedArena *arena) {
  if (arena != NULL) arena->used = 0U;
}

static int test_builder_appends_and_flattens_growth(void) {
  Arena *arena = arena_create(64U);
  ArenaBuilder builder;
  uint32_t values[5] = {1U, 2U, 3U, 4U, 5U};
  uint32_t *out;
  size_t count = 0U;
  M68K_C_ASSERT(arena != NULL);
  M68K_C_ASSERT_INT(1, ARENA_BUILDER_INIT_TYPED(&builder, arena, uint32_t, 2U));
  M68K_C_ASSERT_INT(1, arena_builder_append_many(&builder, values, 5U));
  M68K_C_ASSERT_U32(5U, arena_builder_length(&builder));
  M68K_C_ASSERT_U32(6U, arena_builder_capacity(&builder));
  out = ARENA_BUILDER_FINALIZE_TYPED(&builder, uint32_t, &count);
  M68K_C_ASSERT(out != NULL);
  M68K_C_ASSERT_U32(5U, count);
  M68K_C_ASSERT_U32(1U, out[0]);
  M68K_C_ASSERT_U32(5U, out[4]);
  M68K_C_ASSERT_U32(0U, arena_builder_length(&builder));
  arena_destroy(arena);
  return 0;
}

static int test_builder_zero_length_finalize_is_arena_owned(void) {
  Arena *arena = arena_create(64U);
  ArenaBuilder builder;
  ArenaStats before;
  ArenaStats after;
  void *out;
  size_t count = 99U;
  M68K_C_ASSERT(arena != NULL);
  before = arena_stats(arena);
  M68K_C_ASSERT_INT(1, arena_builder_init(&builder, arena, sizeof(uint32_t), 4U));
  out = arena_builder_finalize(&builder, &count);
  after = arena_stats(arena);
  M68K_C_ASSERT(out != NULL);
  M68K_C_ASSERT_U32(0U, count);
  M68K_C_ASSERT(after.current_used > before.current_used);
  arena_reset(arena);
  M68K_C_ASSERT_U32(0U, arena_stats(arena).current_used);
  arena_destroy(arena);
  return 0;
}

static int test_builder_typed_pair_append_uninit(void) {
  Arena *arena = arena_create(64U);
  ArenaBuilder builder;
  TestPair *slot;
  TestPair *out;
  size_t count = 0U;
  M68K_C_ASSERT(arena != NULL);
  M68K_C_ASSERT_INT(1, ARENA_BUILDER_INIT_TYPED(&builder, arena, TestPair, 1U));
  slot = ARENA_BUILDER_APPEND_TYPED(&builder, TestPair);
  M68K_C_ASSERT(slot != NULL);
  slot->left = 7U;
  slot->right = 9U;
  out = ARENA_BUILDER_FINALIZE_TYPED(&builder, TestPair, &count);
  M68K_C_ASSERT(out != NULL);
  M68K_C_ASSERT_U32(1U, count);
  M68K_C_ASSERT_U32(7U, out[0].left);
  M68K_C_ASSERT_U32(9U, out[0].right);
  arena_destroy(arena);
  return 0;
}

static int test_builder_rewind_discards_chunks_and_finalized_storage(void) {
  Arena *arena = arena_create(64U);
  ArenaBuilder builder;
  ArenaMark mark;
  uint32_t value = 42U;
  uint32_t *out;
  size_t count = 0U;
  M68K_C_ASSERT(arena != NULL);
  mark = arena_mark(arena);
  M68K_C_ASSERT_INT(1, ARENA_BUILDER_INIT_TYPED(&builder, arena, uint32_t, 1U));
  M68K_C_ASSERT_INT(1, arena_builder_append(&builder, &value));
  out = ARENA_BUILDER_FINALIZE_TYPED(&builder, uint32_t, &count);
  M68K_C_ASSERT(out != NULL);
  M68K_C_ASSERT_U32(1U, count);
  arena_rewind(arena, mark);
  M68K_C_ASSERT_U32(0U, arena_stats(arena).current_used);
  arena_destroy(arena);
  return 0;
}

static int test_allocator_heap_allocates_and_frees(void) {
  M68kAllocator allocator = m68k_allocator_heap();
  uint32_t *values = (uint32_t *)m68k_allocator_calloc(allocator, 3U, sizeof(*values));
  M68K_C_ASSERT(values != NULL);
  M68K_C_ASSERT_U32(0U, values[0]);
  values[1] = 42U;
  M68K_C_ASSERT_U32(42U, values[1]);
  m68k_allocator_free(allocator, values);
  return 0;
}

static int test_allocator_arena_uses_arena_storage(void) {
  Arena *arena = arena_create(64U);
  M68kAllocator allocator;
  ArenaStats before;
  ArenaStats after;
  uint32_t *values;
  M68K_C_ASSERT(arena != NULL);
  allocator = m68k_allocator_arena(arena);
  before = arena_stats(arena);
  values = (uint32_t *)m68k_allocator_calloc(allocator, 4U, sizeof(*values));
  after = arena_stats(arena);
  M68K_C_ASSERT(values != NULL);
  M68K_C_ASSERT_U32(0U, values[0]);
  M68K_C_ASSERT(after.current_used > before.current_used);
  m68k_allocator_free(allocator, values);
  M68K_C_ASSERT_U32((uint32_t)after.current_used, (uint32_t)arena_stats(arena).current_used);
  arena_destroy(arena);
  return 0;
}

static int test_allocator_duplicates_memory_and_text(void) {
  M68kAllocator heap = m68k_allocator_heap();
  const unsigned char bytes[] = {1U, 2U, 3U};
  unsigned char *bytes_copy = (unsigned char *)m68k_allocator_memdup(heap, bytes, sizeof(bytes));
  char *text_copy = m68k_allocator_strdup(heap, "allocator text");
  M68K_C_ASSERT(bytes_copy != NULL);
  M68K_C_ASSERT(text_copy != NULL);
  M68K_C_ASSERT(bytes_copy != bytes);
  M68K_C_ASSERT_U32(1U, bytes_copy[0]);
  M68K_C_ASSERT_U32(2U, bytes_copy[1]);
  M68K_C_ASSERT_U32(3U, bytes_copy[2]);
  M68K_C_ASSERT_STR("allocator text", text_copy);
  m68k_allocator_free(heap, text_copy);
  m68k_allocator_free(heap, bytes_copy);
  return 0;
}

static int test_allocator_realloc_copy_preserves_prefix(void) {
  M68kAllocator heap = m68k_allocator_heap();
  unsigned char *bytes = (unsigned char *)m68k_allocator_memdup(heap, "abc", 4U);
  unsigned char *grown;
  unsigned char *shrunk;
  M68K_C_ASSERT(bytes != NULL);
  grown = (unsigned char *)m68k_allocator_realloc_copy(heap, bytes, 4U, 8U);
  M68K_C_ASSERT(grown != NULL);
  M68K_C_ASSERT_U32('a', grown[0]);
  M68K_C_ASSERT_U32('b', grown[1]);
  M68K_C_ASSERT_U32('c', grown[2]);
  M68K_C_ASSERT_U32(0U, grown[3]);
  grown[4] = 'd';
  shrunk = (unsigned char *)m68k_allocator_realloc_copy(heap, grown, 8U, 3U);
  M68K_C_ASSERT(shrunk != NULL);
  M68K_C_ASSERT_U32('a', shrunk[0]);
  M68K_C_ASSERT_U32('b', shrunk[1]);
  M68K_C_ASSERT_U32('c', shrunk[2]);
  m68k_allocator_free(heap, shrunk);
  return 0;
}

static int test_allocator_arena_strdup_uses_arena_storage(void) {
  Arena *arena = arena_create(64U);
  M68kAllocator allocator;
  ArenaStats before;
  ArenaStats after;
  char *text;
  M68K_C_ASSERT(arena != NULL);
  allocator = m68k_allocator_arena(arena);
  before = arena_stats(arena);
  text = m68k_allocator_strdup(allocator, "arena text");
  after = arena_stats(arena);
  M68K_C_ASSERT_STR("arena text", text);
  M68K_C_ASSERT(after.current_used > before.current_used);
  m68k_allocator_free(allocator, text);
  M68K_C_ASSERT_U32((uint32_t)after.current_used, (uint32_t)arena_stats(arena).current_used);
  arena_destroy(arena);
  return 0;
}

static int test_binary_writer_build_uses_allocator(void) {
  M68kBinaryWriter writer;
  Arena *arena = arena_create(64U);
  unsigned char *heap_bytes;
  unsigned char *arena_bytes;
  ArenaStats before;
  ArenaStats after;
  M68K_C_ASSERT(arena != NULL);
  M68K_C_ASSERT_INT(0, m68k_writer_create(&writer));
  M68K_C_ASSERT_INT(0, m68k_writer_u8(&writer, 0x12U));
  M68K_C_ASSERT_INT(0, m68k_writer_u16be(&writer, 0x3456U));
  heap_bytes = m68k_writer_build(&writer);
  before = arena_stats(arena);
  arena_bytes = m68k_writer_build_arena(&writer, arena);
  after = arena_stats(arena);
  M68K_C_ASSERT(heap_bytes != NULL);
  M68K_C_ASSERT(arena_bytes != NULL);
  M68K_C_ASSERT(heap_bytes != arena_bytes);
  M68K_C_ASSERT_U32(0x12U, heap_bytes[0]);
  M68K_C_ASSERT_U32(0x34U, heap_bytes[1]);
  M68K_C_ASSERT_U32(0x56U, heap_bytes[2]);
  M68K_C_ASSERT_U32(0x12U, arena_bytes[0]);
  M68K_C_ASSERT_U32(0x34U, arena_bytes[1]);
  M68K_C_ASSERT_U32(0x56U, arena_bytes[2]);
  M68K_C_ASSERT(after.current_used > before.current_used);
  m68k_allocator_free(m68k_allocator_heap(), heap_bytes);
  m68k_writer_destroy(&writer);
  arena_destroy(arena);
  return 0;
}

static int test_virtual_reserved_arena_prototype_commits_on_demand(void) {
  TestVirtualReservedArena arena;
  unsigned char *first;
  unsigned char *large;
  M68K_C_ASSERT_INT(0, test_virtual_arena_create(&arena, 64U * 1024U));
  first = (unsigned char *)test_virtual_arena_alloc(&arena, 32U);
  M68K_C_ASSERT(first != NULL);
  M68K_C_ASSERT(first == arena.base);
  M68K_C_ASSERT_U32(32U, (uint32_t)arena.used);
  M68K_C_ASSERT(arena.committed >= arena.page_size);
  large = (unsigned char *)test_virtual_arena_alloc(&arena, 5000U);
  M68K_C_ASSERT(large != NULL);
  M68K_C_ASSERT(large == arena.base + 32U);
  M68K_C_ASSERT_U32(5032U, (uint32_t)arena.used);
  M68K_C_ASSERT(arena.committed >= arena.used);
  M68K_C_ASSERT(arena.reserve_size >= 64U * 1024U);
  test_virtual_arena_reset(&arena);
  M68K_C_ASSERT_U32(0U, (uint32_t)arena.used);
  M68K_C_ASSERT_U32(5032U, (uint32_t)arena.peak_used);
  M68K_C_ASSERT(arena.committed >= 5032U);
  test_virtual_arena_destroy(&arena);
  M68K_C_ASSERT(arena.base == NULL);
  return 0;
}

static int test_growable_pool_reuses_fixed_size_nodes(void) {
  Arena *plain_arena = arena_create(64U);
  Arena *pool_arena = arena_create(64U);
  ArenaPool pool;
  ArenaPoolStats pool_stats;
  TestPoolNode *nodes[16];
  ArenaStats plain_stats;
  ArenaStats pool_arena_stats;
  size_t round;
  size_t i;
  M68K_C_ASSERT(plain_arena != NULL);
  M68K_C_ASSERT(pool_arena != NULL);
  M68K_C_ASSERT_INT(1, arena_pool_init(&pool, pool_arena, sizeof(TestPoolNode), 16U));
  for (round = 0U; round < 3U; ++round) {
    for (i = 0U; i < 16U; ++i) {
      TestPoolNode *node = (TestPoolNode *)arena_alloc(plain_arena, sizeof(TestPoolNode));
      M68K_C_ASSERT(node != NULL);
      node->left = (uint32_t)i;
    }
  }
  for (round = 0U; round < 3U; ++round) {
    for (i = 0U; i < 16U; ++i) {
      nodes[i] = (TestPoolNode *)arena_pool_alloc(&pool);
      M68K_C_ASSERT(nodes[i] != NULL);
      nodes[i]->left = (uint32_t)i;
    }
    for (i = 0U; i < 16U; ++i) arena_pool_free(&pool, nodes[i]);
    M68K_C_ASSERT_U32(0U, (uint32_t)arena_pool_stats(&pool).live_slots);
  }
  plain_stats = arena_stats(plain_arena);
  pool_arena_stats = arena_stats(pool_arena);
  pool_stats = arena_pool_stats(&pool);
  M68K_C_ASSERT_U32(768U, (uint32_t)plain_stats.current_used);
  M68K_C_ASSERT_U32(256U, (uint32_t)pool_arena_stats.current_used);
  M68K_C_ASSERT_U32(1U, (uint32_t)pool_stats.chunk_count);
  M68K_C_ASSERT_U32(16U, (uint32_t)pool_stats.allocated_slots);
  M68K_C_ASSERT_U32(16U, (uint32_t)pool_stats.peak_live_slots);
  M68K_C_ASSERT(pool_arena_stats.current_used < plain_stats.current_used);
  arena_destroy(pool_arena);
  arena_destroy(plain_arena);
  return 0;
}

static int test_growable_pool_rejects_invalid_config(void) {
  Arena *arena = arena_create(64U);
  ArenaPool pool;
  M68K_C_ASSERT(arena != NULL);
  M68K_C_ASSERT_INT(0, arena_pool_init(&pool, arena, 0U, 16U));
  M68K_C_ASSERT(pool.arena == NULL);
  M68K_C_ASSERT_INT(0, arena_pool_init(&pool, arena, sizeof(TestPoolNode), 0U));
  M68K_C_ASSERT(pool.arena == NULL);
  M68K_C_ASSERT_INT(0, arena_pool_init(&pool, arena, (size_t)-1, 16U));
  M68K_C_ASSERT(pool.arena == NULL);
  arena_destroy(arena);
  return 0;
}

static int test_decode_ir_result_arrays_use_result_arena(void) {
  uint8_t code[] = {0x4eU, 0x75U};
  M68kObject object;
  M68kSection section;
  M68kObjectAddResult add_result;
  M68kDecodeIR decode;
  const M68kDecodeCandidate *candidate = NULL;
  ArenaStats stats;
  memset(&object, 0, sizeof(object));
  memset(&decode, 0, sizeof(decode));
  M68K_C_ASSERT_INT(0, m68k_object_create(&object));
  memset(&section, 0, sizeof(section));
  section.kind = M68K_SECTION_CODE;
  section.size = sizeof(code);
  section.data_size = sizeof(code);
  add_result = m68k_object_add_section(&object, &section);
  M68K_C_ASSERT(add_result.ok);
  M68K_C_ASSERT_INT(0, m68k_object_set_section_data(&object, add_result.index, code, (uint32_t)sizeof(code)));
  M68K_C_ASSERT_INT(0, m68k_decode_ir_build_object_sections(&decode, &object, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(decode.arena != NULL);
  M68K_C_ASSERT_INT(0, m68k_decode_ir_ensure_candidate_at(&decode, 0U, 0U, M68K_ASM_CPU_68000,
    &candidate, m68k_diag_sink(NULL)));
  M68K_C_ASSERT(candidate != NULL);
  stats = arena_stats(decode.arena);
  M68K_C_ASSERT(stats.current_used > 0U);
  m68k_decode_ir_destroy(&decode);
  M68K_C_ASSERT(decode.arena == NULL);
  M68K_C_ASSERT(decode.sections == NULL);
  m68k_object_destroy(&object);
  return 0;
}

static int test_fact_ir_result_arrays_use_result_arena(void) {
  M68kFactIR facts;
  M68kFact fact;
  ArenaStats stats;
  memset(&facts, 0, sizeof(facts));
  memset(&fact, 0, sizeof(fact));
  m68k_fact_ir_init(&facts);
  M68K_C_ASSERT(facts.arena != NULL);
  fact.kind = M68K_FACT_CODE_START;
  fact.confidence = M68K_FACT_CONFIDENCE_TOOL_INFERRED;
  M68K_C_ASSERT_INT(0, m68k_fact_ir_append(&facts, &fact));
  M68K_C_ASSERT(facts.facts != NULL);
  M68K_C_ASSERT_U32(1U, facts.fact_count);
  M68K_C_ASSERT_U32(1U, facts.code_start_count);
  stats = arena_stats(facts.arena);
  M68K_C_ASSERT(stats.current_used > 0U);
  m68k_fact_ir_destroy(&facts);
  M68K_C_ASSERT(facts.arena == NULL);
  M68K_C_ASSERT(facts.facts == NULL);
  return 0;
}

int m68k_c_util_arena_tests(void) {
  static const M68kCTestCase cases[] = {
    {"builder_appends_and_flattens_growth", test_builder_appends_and_flattens_growth},
    {"builder_zero_length_finalize_is_arena_owned", test_builder_zero_length_finalize_is_arena_owned},
    {"builder_typed_pair_append_uninit", test_builder_typed_pair_append_uninit},
    {"builder_rewind_discards_chunks_and_finalized_storage", test_builder_rewind_discards_chunks_and_finalized_storage},
    {"allocator_heap_allocates_and_frees", test_allocator_heap_allocates_and_frees},
    {"allocator_arena_uses_arena_storage", test_allocator_arena_uses_arena_storage},
    {"allocator_duplicates_memory_and_text", test_allocator_duplicates_memory_and_text},
    {"allocator_realloc_copy_preserves_prefix", test_allocator_realloc_copy_preserves_prefix},
    {"allocator_arena_strdup_uses_arena_storage", test_allocator_arena_strdup_uses_arena_storage},
    {"binary_writer_build_uses_allocator", test_binary_writer_build_uses_allocator},
    {"virtual_reserved_arena_prototype_commits_on_demand", test_virtual_reserved_arena_prototype_commits_on_demand},
    {"growable_pool_reuses_fixed_size_nodes", test_growable_pool_reuses_fixed_size_nodes},
    {"growable_pool_rejects_invalid_config", test_growable_pool_rejects_invalid_config},
    {"decode_ir_result_arrays_use_result_arena", test_decode_ir_result_arrays_use_result_arena},
    {"fact_ir_result_arrays_use_result_arena", test_fact_ir_result_arrays_use_result_arena},
  };
  return m68k_c_test_run_suite("util_arena", cases, sizeof(cases) / sizeof(cases[0]));
}
