#ifndef UTIL_ARENA_H
#define UTIL_ARENA_H

#include <stddef.h>

typedef struct Arena Arena;
typedef struct ArenaMark {
  void *block;
  size_t used;
} ArenaMark;

typedef struct ArenaStats {
  size_t current_used;
  size_t peak_used;
  size_t current_block_count;
  size_t total_block_count;
} ArenaStats;

Arena *arena_create(size_t initial_capacity);
void arena_destroy(Arena *arena);
void *arena_alloc(Arena *arena, size_t size);
void *arena_calloc(Arena *arena, size_t count, size_t size);
void *arena_memdup(Arena *arena, const void *data, size_t size);
void *arena_realloc_copy(Arena *arena, const void *old_data, size_t old_size, size_t new_size);
char *arena_strdup(Arena *arena, const char *text);
char *arena_strndup(Arena *arena, const char *text, size_t length);
ArenaMark arena_mark(Arena *arena);
void arena_rewind(Arena *arena, ArenaMark mark);
void arena_reset(Arena *arena);
ArenaStats arena_stats(const Arena *arena);

#endif
