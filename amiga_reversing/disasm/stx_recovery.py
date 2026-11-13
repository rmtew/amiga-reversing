"""Source-bound STX sector assembly and bounded original-instruction recipes.

Recipes describe an investigated loader. They are not automatic loader discovery
or an FDC model. Original media and recovered bytes are supplied at runtime.
"""
from __future__ import annotations
import ctypes as C
import hashlib
import json
from pathlib import Path
import zipfile
from .c_backend import PROJECT_ROOT, _platform_disk_dll
from .mapped_execution import Diags, assemble_stx_sectors
from .mapped_recipe import integer, keys

MAX_BYTES = 32*1024*1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_stx(path: Path, member: str | None = None) -> tuple[bytes, dict]:
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            candidates = [m for m in archive.infolist() if not m.is_dir() and m.filename.lower().endswith('.stx')
                          and (member is None or m.filename == member)]
            if len(candidates) != 1 or candidates[0].file_size > MAX_BYTES:
                raise ValueError('select one STX member within the image size bound')
            data = archive.read(candidates[0])
            origin = dict(container=str(path.resolve()),member=candidates[0].filename)
    else:
        if member is not None or path.stat().st_size > MAX_BYTES:
            raise ValueError('invalid raw STX input selection')
        data = path.read_bytes()
        origin = dict(path=str(path.resolve()))
    if len(data) > MAX_BYTES:
        raise ValueError('STX exceeds image size bound')
    return data,origin


def inspect_stx(data: bytes, project_root: Path = PROJECT_ROOT) -> dict:
    class Text(C.Structure):
        _fields_ = [('text',C.c_void_p),('diagnostics',Diags)]
    dll = _platform_disk_dll(project_root)
    dll.platform_disk_inspect_buffer_json.argtypes = [C.c_char_p,C.c_void_p,C.c_size_t]
    dll.platform_disk_inspect_buffer_json.restype = Text
    raw = C.create_string_buffer(data)
    result = dll.platform_disk_inspect_buffer_json(b'atari-st-disk',raw,len(data))
    try:
        if result.diagnostics.error():
            raise ValueError(result.diagnostics.error())
        if not result.text:
            raise ValueError('native STX inventory returned no metadata')
        report = json.loads(C.string_at(result.text))
        if report.get('format_kind') != 'stx':
            raise ValueError('recovery requires an STX image')
        return report
    finally:
        dll.platform_disk_free_text(result.text)


def recover(data: bytes, plan: dict, *, project_root: Path = PROJECT_ROOT, register_seed: int = 0) -> tuple[dict,dict[str,bytes]]:
    keys(plan,'schema_version kind image_sha256 memory_size evidence inputs actions')
    if type(plan['schema_version']) is not int or plan['schema_version'] != 1 or plan['kind'] != 'stx_cpu_recovery' or plan['image_sha256'] != digest(data):
        raise ValueError('STX recovery input identity mismatch')
    if not isinstance(plan['evidence'],str) or not isinstance(plan['inputs'],list) or not isinstance(plan['actions'],list):
        raise ValueError('invalid recovery recipe collections')
    if len(plan['inputs']) > 32 or len(plan['actions']) > 256:
        raise ValueError('recovery recipe exceeds operation bound')
    inspection = inspect_stx(data,project_root)
    inputs, origins = {}, {}
    for item in plan['inputs']:
        keys(item,'id track_start track_count side sector_ids id_track id_head id_sizes')
        name = item['id']
        if not isinstance(name,str) or not name or name in inputs:
            raise ValueError('duplicate or invalid recovery input identity')
        start = integer(item['track_start'],127); count = integer(item['track_count'],128)
        side = integer(item['side'],1); c = integer(item['id_track'],255); h = integer(item['id_head'],255)
        if count == 0 or start+count > 128 or not isinstance(item['sector_ids'],list) or not isinstance(item['id_sizes'],list):
            raise ValueError('invalid physical sector run')
        if not 0 < len(item['sector_ids']) == len(item['id_sizes']) <= 256:
            raise ValueError('invalid sector identity list')
        pairs, mapping, output_offset = [], [], 0
        for cylinder in range(start,start+count):
            matches = [t for t in inspection['tracks'] if (t['track'],t['side']) == (cylinder,side)]
            if len(matches) != 1:
                raise ValueError('missing or ambiguous physical track')
            t = matches[0]
            for r,n in zip(item['sector_ids'],item['id_sizes'],strict=True):
                r = integer(r,255); n = integer(n,255)
                sectors = [s for s in t['sectors'] if (s['id_track'],s['id_head'],s['id_sector'],s['id_size']) == (c,h,r,n)]
                if len(sectors) != 1:
                    raise ValueError('missing or ambiguous exact sector identity')
                s = sectors[0]
                pairs.append((t['index'],s['index']))
                mapping.append(dict(output_offset=output_offset,image_offset=s['offset'],size=s['size'],
                                    track_index=t['index'],sector_index=s['index'],physical=[cylinder,side],chrn=[c,h,r,n]))
                output_offset += s['size']
        value = assemble_stx_sectors(data,pairs,MAX_BYTES,project_root)
        if len(value) != output_offset:
            raise ValueError('native sector assembly differs from inventory extent')
        inputs[name] = value
        origins[name] = dict(size=len(value),sha256=digest(value),source_ranges=mapping)
    from .mapped_recipe import execute_actions
    runs, captures, outputs = execute_actions(plan['actions'], plan['memory_size'], inputs,
        project_root=project_root, register_seed=register_seed)
    return dict(schema_version=1,kind='stx_cpu_recovery_result',image_sha256=digest(data),
                recipe_sha256=digest(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()),
                inputs=origins,runs=runs,captures=captures,
                scope='Mapped CPU decoder slices and static loader read schedule; not a chipset boot or FDC proof'),outputs
