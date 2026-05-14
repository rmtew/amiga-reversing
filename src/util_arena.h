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
  size_t current_capacity;
  size_t peak_capacity;
  size_t current_block_count;
  size_t total_block_count;
} ArenaStats;

typedef struct ArenaBuilderChunk ArenaBuilderChunk;
typedef struct ArenaPoolFreeNode ArenaPoolFreeNode;

typedef struct ArenaBuilder {
  Arena *arena;
  ArenaBuilderChunk *head;
  ArenaBuilderChunk *tail;
  size_t item_size;
  size_t length;
  size_t chunk_capacity;
} ArenaBuilder;

typedef struct ArenaPool {
  Arena *arena;
  ArenaPoolFreeNode *free_list;
  size_t object_size;
  size_t objects_per_chunk;
  size_t chunk_count;
  size_t allocated_slots;
  size_t live_slots;
  size_t peak_live_slots;
} ArenaPool;

typedef struct ArenaPoolStats {
  size_t chunk_count;
  size_t allocated_slots;
  size_t live_slots;
  size_t peak_live_slots;
} ArenaPoolStats;

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

int arena_builder_init(ArenaBuilder *builder, Arena *arena, size_t item_size, size_t chunk_capacity);
size_t arena_builder_length(const ArenaBuilder *builder);
size_t arena_builder_capacity(const ArenaBuilder *builder);
void *arena_builder_append_uninit(ArenaBuilder *builder);
int arena_builder_append(ArenaBuilder *builder, const void *item);
int arena_builder_append_many(ArenaBuilder *builder, const void *items, size_t count);
void *arena_builder_finalize(ArenaBuilder *builder, size_t *out_count);

int arena_pool_init(ArenaPool *pool, Arena *arena, size_t object_size, size_t objects_per_chunk);
void *arena_pool_alloc(ArenaPool *pool);
void arena_pool_free(ArenaPool *pool, void *ptr);
ArenaPoolStats arena_pool_stats(const ArenaPool *pool);

#define ARENA_BUILDER_INIT_TYPED(builder, arena, type, chunk_capacity) \
  arena_builder_init((builder), (arena), sizeof(type), (chunk_capacity))
#define ARENA_BUILDER_APPEND_TYPED(builder, type) \
  ((type *)arena_builder_append_uninit((builder)))
#define ARENA_BUILDER_FINALIZE_TYPED(builder, type, out_count) \
  ((type *)arena_builder_finalize((builder), (out_count)))

#endif
