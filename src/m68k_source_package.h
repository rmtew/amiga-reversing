#ifndef M68K_SOURCE_PACKAGE_H
#define M68K_SOURCE_PACKAGE_H

#include "m68k_object.h"
#include "m68k_render_plan.h"

/* Projects the existing native plan without modifying it or touching files.
 * The caller owns *out_json (free()). Asset paths are package-root relative.
 * Only evidenced bitmap/sample rows are eligible; unsupported layouts stay
 * source. minimum_asset_size must be nonzero. */
int m68k_source_package_json_alloc(const M68kObject *object, const M68kRenderPlan *plan,
  uint32_t minimum_asset_size, char **out_json);

#endif
