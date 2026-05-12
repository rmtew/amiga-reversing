#include "util_arena.h"

#include <stdlib.h>
#include <string.h>

#define ARENA_ALIGNMENT sizeof(void*)
#define ARENA_MIN_BLOCK_SIZE 4096U

#if defined(_DEBUG)
#define ARENA_DEBUG_POISON_BYTE 0xDD
#endif

typedef struct ArenaBlock {
  char *buffer;
  size_t capacity;
  size_t used;
  struct ArenaBlock *next;
} ArenaBlock;

struct ArenaBuilderChunk {
  struct ArenaBuilderChunk *next;
  size_t used;
  size_t capacity;
  unsigned char data[1];
};

struct Arena {
  ArenaBlock *head;
  ArenaBlock *current;
  size_t default_block_size;
  size_t current_used;
  size_t peak_used;
  size_t current_block_count;
  size_t total_block_count;
};

static size_t arena_align_up(size_t size) {
  return (size + ARENA_ALIGNMENT - 1U) & ~(ARENA_ALIGNMENT - 1U);
}

static ArenaBlock *arena_block_create(size_t capacity) {
  ArenaBlock *block = (ArenaBlock *)malloc(sizeof(*block));
  if (block == NULL) return NULL;
  block->buffer = (char *)malloc(capacity);
  if (block->buffer == NULL) {
    free(block);
    return NULL;
  }
  block->capacity = capacity;
  block->used = 0U;
  block->next = NULL;
  return block;
}

static void arena_block_chain_destroy(ArenaBlock *block) {
  while (block != NULL) {
    ArenaBlock *next = block->next;
#if defined(_DEBUG)
    memset(block->buffer, ARENA_DEBUG_POISON_BYTE, block->capacity);
#endif
    free(block->buffer);
    free(block);
    block = next;
  }
}

static void arena_poison_range(ArenaBlock *block, size_t start, size_t end) {
#if defined(_DEBUG)
  if (block == NULL || start >= end || start >= block->capacity) return;
  if (end > block->capacity) end = block->capacity;
  memset(block->buffer + start, ARENA_DEBUG_POISON_BYTE, end - start);
#else
  (void)block;
  (void)start;
  (void)end;
#endif
}

static void arena_refresh_current_stats(Arena *arena) {
  ArenaBlock *block;
  size_t used = 0U;
  size_t block_count = 0U;
  if (arena == NULL) return;
  for (block = arena->head; block != NULL; block = block->next) {
    used += block->used;
    ++block_count;
  }
  arena->current_used = used;
  arena->current_block_count = block_count;
}

Arena *arena_create(size_t initial_capacity) {
  Arena *arena;
  ArenaBlock *block;
  if (initial_capacity < ARENA_MIN_BLOCK_SIZE) initial_capacity = ARENA_MIN_BLOCK_SIZE;
  arena = (Arena *)malloc(sizeof(*arena));
  if (arena == NULL) return NULL;
  block = arena_block_create(initial_capacity);
  if (block == NULL) {
    free(arena);
    return NULL;
  }
  arena->head = block;
  arena->current = block;
  arena->default_block_size = initial_capacity;
  arena->current_used = 0U;
  arena->peak_used = 0U;
  arena->current_block_count = 1U;
  arena->total_block_count = 1U;
  return arena;
}

void arena_destroy(Arena *arena) {
  if (arena == NULL) return;
  arena_block_chain_destroy(arena->head);
  free(arena);
}

void *arena_alloc(Arena *arena, size_t size) {
  ArenaBlock *block;
  size_t aligned_size;
  if (arena == NULL || size == 0U) return NULL;
  aligned_size = arena_align_up(size);
  if (aligned_size < size) return NULL;
  block = arena->current;
  if (aligned_size > block->capacity - block->used) {
    size_t new_block_size = arena->default_block_size;
    ArenaBlock *new_block;
    if (aligned_size > new_block_size) new_block_size = aligned_size;
    new_block = arena_block_create(new_block_size);
    if (new_block == NULL) return NULL;
    block->next = new_block;
    arena->current = new_block;
    arena->current_block_count += 1U;
    arena->total_block_count += 1U;
    block = new_block;
  }
  {
    void *ptr = block->buffer + block->used;
    block->used += aligned_size;
    arena->current_used += aligned_size;
    if (arena->current_used > arena->peak_used) arena->peak_used = arena->current_used;
    return ptr;
  }
}

void *arena_calloc(Arena *arena, size_t count, size_t size) {
  size_t total;
  void *ptr;
  if (count != 0U && size > ((size_t)-1) / count) return NULL;
  total = count * size;
  ptr = arena_alloc(arena, total);
  if (ptr != NULL) memset(ptr, 0, total);
  return ptr;
}

void *arena_memdup(Arena *arena, const void *data, size_t size) {
  void *copy;
  if (arena == NULL) return NULL;
  if (size == 0U) return arena_alloc(arena, 1U);
  if (data == NULL) return NULL;
  copy = arena_alloc(arena, size);
  if (copy == NULL) return NULL;
  memcpy(copy, data, size);
  return copy;
}

void *arena_realloc_copy(Arena *arena, const void *old_data, size_t old_size, size_t new_size) {
  void *copy;
  size_t bytes_to_copy;
  if (arena == NULL || new_size == 0U) return NULL;
  copy = arena_alloc(arena, new_size);
  if (copy == NULL) return NULL;
  if (old_data == NULL || old_size == 0U) return copy;
  bytes_to_copy = old_size < new_size ? old_size : new_size;
  memcpy(copy, old_data, bytes_to_copy);
  return copy;
}

char *arena_strndup(Arena *arena, const char *text, size_t length) {
  char *copy;
  if (arena == NULL || text == NULL) return NULL;
  if (length == (size_t)-1) return NULL;
  copy = (char *)arena_alloc(arena, length + 1U);
  if (copy == NULL) return NULL;
  memcpy(copy, text, length);
  copy[length] = '\0';
  return copy;
}

char *arena_strdup(Arena *arena, const char *text) {
  if (text == NULL) return NULL;
  return arena_strndup(arena, text, strlen(text));
}

ArenaMark arena_mark(Arena *arena) {
  ArenaMark mark;
  mark.block = NULL;
  mark.used = 0U;
  if (arena == NULL || arena->current == NULL) return mark;
  mark.block = arena->current;
  mark.used = arena->current->used;
  return mark;
}

void arena_rewind(Arena *arena, ArenaMark mark) {
  ArenaBlock *block;
  if (arena == NULL || arena->head == NULL) return;
  if (mark.block == NULL) {
    arena_reset(arena);
    return;
  }
  for (block = arena->head; block != NULL; block = block->next) {
    if (block == (ArenaBlock *)mark.block) {
      ArenaBlock *tail = block->next;
      if (mark.used > block->capacity) mark.used = block->capacity;
      arena_poison_range(block, mark.used, block->used);
      block->used = mark.used;
      block->next = NULL;
      arena->current = block;
      arena_block_chain_destroy(tail);
      arena_refresh_current_stats(arena);
      return;
    }
  }
}

void arena_reset(Arena *arena) {
  if (arena == NULL) return;
  arena_poison_range(arena->head, 0U, arena->head->used);
  arena_block_chain_destroy(arena->head->next);
  arena->head->next = NULL;
  arena->head->used = 0U;
  arena->current = arena->head;
  arena->current_used = 0U;
  arena->current_block_count = 1U;
}

ArenaStats arena_stats(const Arena *arena) {
  ArenaStats stats;
  memset(&stats, 0, sizeof(stats));
  if (arena == NULL) return stats;
  stats.current_used = arena->current_used;
  stats.peak_used = arena->peak_used;
  stats.current_block_count = arena->current_block_count;
  stats.total_block_count = arena->total_block_count;
  return stats;
}

static ArenaBuilderChunk *arena_builder_chunk_create(
    Arena *arena, size_t item_size, size_t item_capacity) {
  ArenaBuilderChunk *chunk;
  size_t header_size = offsetof(ArenaBuilderChunk, data);
  size_t data_size;
  size_t total_size;
  if (arena == NULL || item_size == 0U || item_capacity == 0U) return NULL;
  if (item_capacity > ((size_t)-1) / item_size) return NULL;
  data_size = item_capacity * item_size;
  if (data_size > ((size_t)-1) - header_size) return NULL;
  total_size = header_size + data_size;
  chunk = (ArenaBuilderChunk *)arena_alloc(arena, total_size);
  if (chunk == NULL) return NULL;
  chunk->next = NULL;
  chunk->used = 0U;
  chunk->capacity = item_capacity;
  return chunk;
}

int arena_builder_init(ArenaBuilder *builder, Arena *arena, size_t item_size, size_t chunk_capacity) {
  if (builder == NULL || arena == NULL || item_size == 0U) return 0;
  if (chunk_capacity == 0U) chunk_capacity = 16U;
  builder->arena = arena;
  builder->head = NULL;
  builder->tail = NULL;
  builder->item_size = item_size;
  builder->length = 0U;
  builder->chunk_capacity = chunk_capacity;
  return 1;
}

size_t arena_builder_length(const ArenaBuilder *builder) {
  return builder != NULL ? builder->length : 0U;
}

size_t arena_builder_capacity(const ArenaBuilder *builder) {
  size_t capacity = 0U;
  ArenaBuilderChunk *chunk;
  if (builder == NULL) return 0U;
  for (chunk = builder->head; chunk != NULL; chunk = chunk->next) capacity += chunk->capacity;
  return capacity;
}

void *arena_builder_append_uninit(ArenaBuilder *builder) {
  ArenaBuilderChunk *chunk;
  void *slot;
  if (builder == NULL || builder->arena == NULL || builder->item_size == 0U) return NULL;
  chunk = builder->tail;
  if (chunk == NULL || chunk->used == chunk->capacity) {
    chunk = arena_builder_chunk_create(builder->arena, builder->item_size, builder->chunk_capacity);
    if (chunk == NULL) return NULL;
    if (builder->tail != NULL) {
      builder->tail->next = chunk;
    } else {
      builder->head = chunk;
    }
    builder->tail = chunk;
  }
  slot = chunk->data + (chunk->used * builder->item_size);
  chunk->used += 1U;
  builder->length += 1U;
  return slot;
}

int arena_builder_append(ArenaBuilder *builder, const void *item) {
  void *slot;
  if (item == NULL) return 0;
  slot = arena_builder_append_uninit(builder);
  if (slot == NULL) return 0;
  memcpy(slot, item, builder->item_size);
  return 1;
}

int arena_builder_append_many(ArenaBuilder *builder, const void *items, size_t count) {
  const unsigned char *cursor = (const unsigned char *)items;
  size_t index;
  if (count == 0U) return builder != NULL;
  if (builder == NULL || items == NULL) return 0;
  for (index = 0U; index < count; ++index) {
    if (!arena_builder_append(builder, cursor + (index * builder->item_size))) return 0;
  }
  return 1;
}

void *arena_builder_finalize(ArenaBuilder *builder, size_t *out_count) {
  unsigned char *items;
  unsigned char *cursor;
  ArenaBuilderChunk *chunk;
  size_t total_size;
  if (out_count != NULL) *out_count = 0U;
  if (builder == NULL || builder->arena == NULL || builder->item_size == 0U) return NULL;
  if (out_count != NULL) *out_count = builder->length;
  if (builder->length == 0U) {
    items = (unsigned char *)arena_alloc(builder->arena, 1U);
  } else {
    if (builder->length > ((size_t)-1) / builder->item_size) return NULL;
    total_size = builder->length * builder->item_size;
    items = (unsigned char *)arena_alloc(builder->arena, total_size);
  }
  if (items == NULL) return NULL;
  cursor = items;
  for (chunk = builder->head; chunk != NULL; chunk = chunk->next) {
    size_t bytes = chunk->used * builder->item_size;
    memcpy(cursor, chunk->data, bytes);
    cursor += bytes;
  }
  builder->head = NULL;
  builder->tail = NULL;
  builder->length = 0U;
  return items;
}
