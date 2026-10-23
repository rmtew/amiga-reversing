#include "m68k_runtime_map.h"
#include <stdlib.h>
#include <string.h>
#include <limits.h>

typedef struct MapKey { uint32_t section; int64_t delta; } MapKey;
typedef struct MapEvent { uint64_t address; size_t key; int change; } MapEvent;
static int key_compare(const void *ap,const void *bp) {
  const MapKey *a=ap,*b=bp;
  if(a->section!=b->section) return a->section<b->section ? -1 : 1;
  return (a->delta>b->delta)-(a->delta<b->delta);
}
static int event_compare(const void *ap,const void *bp) {
  const MapEvent *a=ap,*b=bp;
  if(a->address!=b->address) return a->address<b->address ? -1 : 1;
  if(a->key!=b->key) return a->key<b->key ? -1 : 1;
  return a->change-b->change;
}
void m68k_runtime_map_destroy(M68kRuntimeMap *map) {
  if(map) {free(map->segments);memset(map,0,sizeof(*map));}
}
int m68k_runtime_map_build(M68kRuntimeMap *map,const M68kRuntimeMapSpan *spans,size_t n) {
  MapKey *keys=NULL;MapEvent *events=NULL;size_t *counts=NULL,*tree=NULL;
  M68kRuntimeMap next={0};size_t unique=0,leaves=1,i,j;
  if(!map || (n && !spans) || n>SIZE_MAX/(2*sizeof(MapEvent)) ||
      n>SIZE_MAX/(2*sizeof(M68kRuntimeMapSegment))) return -1;
  if(!n) {m68k_runtime_map_destroy(map);return 0;}
  keys=calloc(n,sizeof(*keys));events=calloc(2*n,sizeof(*events));
  next.segments=calloc(2*n,sizeof(*next.segments));
  if(!keys || !events || !next.segments) goto fail;
  for(i=0;i<n;i++) {
    if(!spans[i].size || (uint64_t)spans[i].address+spans[i].size>UINT64_C(0x100000000) ||
        (uint64_t)spans[i].source_offset+spans[i].size>UINT64_C(0x100000000)) goto fail;
    keys[i]=(MapKey){spans[i].section,(int64_t)spans[i].source_offset-spans[i].address};
  }
  qsort(keys,n,sizeof(*keys),key_compare);
  for(i=0;i<n;i++) if(!unique || key_compare(&keys[i],&keys[unique-1])) keys[unique++]=keys[i];
  while(leaves<unique) {if(leaves>SIZE_MAX/2) goto fail;leaves*=2;}
  if(leaves>SIZE_MAX/(2*sizeof(*tree))) goto fail;
  counts=calloc(unique,sizeof(*counts));tree=calloc(2*leaves,sizeof(*tree));
  if(!counts || !tree) goto fail;
  for(i=0;i<n;i++) {
    MapKey key={spans[i].section,(int64_t)spans[i].source_offset-spans[i].address};
    MapKey *found=bsearch(&key,keys,unique,sizeof(*keys),key_compare);
    if(!found) goto fail;
    size_t k=(size_t)(found-keys);
    events[2*i]=(MapEvent){spans[i].address,k,1};
    events[2*i+1]=(MapEvent){(uint64_t)spans[i].address+spans[i].size,k,-1};
  }
  qsort(events,2*n,sizeof(*events),event_compare);
  for(i=0;i<2*n;i=j) {
    for(j=i;j<2*n && events[j].address==events[i].address;j++) {
      size_t k=events[j].key,p=leaves+k;
      if(events[j].change<0) {if(!counts[k]) goto fail;counts[k]--;}
      else counts[k]++;
      tree[p]=counts[k]!=0;
      while(p>1) {p/=2;tree[p]=tree[2*p]+tree[2*p+1];}
    }
    if(j==2*n || !tree[1]) continue;
    M68kRuntimeMapSegment segment={events[i].address,events[j].address,0,0,-1};
    if(tree[1]==1) {
      size_t p=1;
      while(p<leaves) p=tree[2*p] ? 2*p : 2*p+1;
      segment.source_delta=keys[p-leaves].delta;segment.section=keys[p-leaves].section;segment.status=1;
    }
    if(next.count) {
      M68kRuntimeMapSegment *last=&next.segments[next.count-1];
      if(last->end==segment.start && last->status==segment.status &&
          last->section==segment.section && last->source_delta==segment.source_delta) {
        last->end=segment.end;continue;
      }
    }
    next.segments[next.count++]=segment;
  }
  free(keys);free(events);free(counts);free(tree);
  m68k_runtime_map_destroy(map);*map=next;return 0;
fail:
  free(keys);free(events);free(counts);free(tree);m68k_runtime_map_destroy(&next);return -1;
}
int m68k_runtime_map_resolve(const M68kRuntimeMap *map,uint32_t address,uint32_t size,
    uint32_t *section,uint32_t *source_offset,size_t *steps) {
  size_t lo=0,hi;uint64_t cursor=address,end=(uint64_t)address+size;
  if(steps) *steps=0;
  if(section) *section=0;
  if(source_offset) *source_offset=0;
  if(!map || !size || end>UINT64_C(0x100000000)) return -1;
  hi=map->count;
  while(lo<hi) {
    size_t mid=lo+(hi-lo)/2;
    if(steps) (*steps)++;
    if(map->segments[mid].end<=address) lo=mid+1;else hi=mid;
  }
  if(lo==map->count || map->segments[lo].start>address) return 0;
  const M68kRuntimeMapSegment *first=&map->segments[lo];
  if(first->status!=1) return -1;
  for(size_t i=lo;cursor<end;i++) {
    if(steps) (*steps)++;
    if(i==map->count || map->segments[i].start>cursor) return 0;
    const M68kRuntimeMapSegment *s=&map->segments[i];
    if(s->status!=1 || s->section!=first->section || s->source_delta!=first->source_delta) return -1;
    cursor=s->end;
  }
  if(section) *section=first->section;
  if(source_offset) *source_offset=(uint32_t)((int64_t)address+first->source_delta);
  return 1;
}
