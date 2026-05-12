#include "m68k_c_unit_test.h"
#include "util_arena.h"

#include <string.h>

typedef struct TestPair {
  uint32_t left;
  uint32_t right;
} TestPair;

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

int m68k_c_util_arena_tests(void) {
  static const M68kCTestCase cases[] = {
    {"builder_appends_and_flattens_growth", test_builder_appends_and_flattens_growth},
    {"builder_zero_length_finalize_is_arena_owned", test_builder_zero_length_finalize_is_arena_owned},
    {"builder_typed_pair_append_uninit", test_builder_typed_pair_append_uninit},
    {"builder_rewind_discards_chunks_and_finalized_storage", test_builder_rewind_discards_chunks_and_finalized_storage},
  };
  return m68k_c_test_run_suite("util_arena", cases, sizeof(cases) / sizeof(cases[0]));
}
