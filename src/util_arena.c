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

struct Arena {
  ArenaBlock *head;
  ArenaBlock *current;
  size_t default_block_size;
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
  block = arena->current;
  if (block->used + aligned_size > block->capacity) {
    size_t new_block_size = arena->default_block_size;
    ArenaBlock *new_block;
    if (aligned_size > new_block_size) new_block_size = aligned_size;
    new_block = arena_block_create(new_block_size);
    if (new_block == NULL) return NULL;
    block->next = new_block;
    arena->current = new_block;
    block = new_block;
  }
  {
    void *ptr = block->buffer + block->used;
    block->used += aligned_size;
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
}
