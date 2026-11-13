"""Game/release identities and content-addressed artifact/target bindings.

The catalog owns cross-release relationships. Existing target source histories
remain authoritative and are referenced, not copied. Media paths and recovered
bytes live in ignored workspace state, never in the public catalog.
"""
from __future__ import annotations
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
import tempfile


def digest(data): return hashlib.sha256(data).hexdigest()


def object_keys(value, fields):
    if not isinstance(value,dict) or set(value) != set(fields.split()):
        raise ValueError('invalid game catalog fields')


def identity(value):
    if not isinstance(value,str) or not re.fullmatch('[a-zA-Z0-9][a-zA-Z0-9_-]*',value):
        raise ValueError('invalid catalog identity')
    return value


def sha(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):
        raise ValueError('invalid artifact identity')
    return value


def relative(root, value):
    if not isinstance(value,str): raise ValueError('invalid catalog path')
    path=(root/value).resolve()
    if Path(value).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError('catalog path escapes project')
    return path


def validate(payload, root):
    object_keys(payload,'schema_version id name releases artifacts sources derivations targets correspondences')
    if type(payload['schema_version']) is not int or payload['schema_version'] != 1:
        raise ValueError('unsupported game catalog schema')
    identity(payload['id'])
    if not isinstance(payload['name'],str) or not payload['name']: raise ValueError('invalid game name')
    for key in ('releases','artifacts','sources','derivations','targets'):
        if not isinstance(payload[key],dict): raise ValueError('invalid catalog collection')
    artifacts=payload['artifacts']
    for artifact,record in artifacts.items():
        sha(artifact);object_keys(record,'size role')
        if type(record['size']) is not int or not 0 < record['size'] <= 32*1024*1024 or not isinstance(record['role'],str):
            raise ValueError('invalid artifact extent or role')
    for release,record in payload['releases'].items():
        identity(release);object_keys(record,'platform edition media')
        if record['platform'] not in ('amiga','atari-st') or not isinstance(record['edition'],str) or not isinstance(record['media'],list):
            raise ValueError('invalid release context')
        if any(a not in artifacts for a in record['media']): raise ValueError('unknown release media artifact')
    for artifact,source in payload['sources'].items():
        if artifact not in artifacts or not isinstance(source,dict): raise ValueError('unknown source artifact')
        if source.get('kind') == 'private_media':
            object_keys(source,'kind format')
            if source['format'] not in ('stx','bytes'): raise ValueError('unsupported media source format')
        elif source.get('kind') == 'existing_target':
            object_keys(source,'kind target')
            identity(source['target'])
        else: raise ValueError('unsupported artifact source')
    producers={}
    for name,d in payload['derivations'].items():
        identity(name);object_keys(d,'kind input recipe recipe_sha256 outputs')
        if d['kind'] != 'stx_cpu_recovery' or d['input'] not in artifacts or not isinstance(d['outputs'],dict):
            raise ValueError('unsupported artifact derivation')
        recipe=relative(root,d['recipe'])
        if digest(recipe.read_bytes()) != sha(d['recipe_sha256']): raise ValueError('stale recovery recipe identity')
        plan=json.loads(recipe.read_text())
        expected={a['file']:a['sha256'] for a in plan['actions'] if a.get('op')=='capture'}
        if plan['image_sha256'] != d['input'] or expected != d['outputs']:
            raise ValueError('derivation differs from bound recovery recipe')
        for filename,artifact in d['outputs'].items():
            if artifact not in artifacts: raise ValueError('unknown derived artifact')
            producers.setdefault(artifact,[]).append((name,filename))
    # Reject orphan artifacts and cycles before any materialization or execution.
    def visit(a,stack):
        if a in stack: raise ValueError('artifact derivation cycle')
        if a in payload['sources']: return
        if a not in producers: raise ValueError('artifact has no source or derivation')
        for d,_ in producers[a]: visit(payload['derivations'][d]['input'],stack|{a})
    for a in artifacts: visit(a,set())
    for target,binding in payload['targets'].items():
        identity(target);object_keys(binding,'release artifact context')
        if binding['release'] not in payload['releases'] or binding['artifact'] not in artifacts:
            raise ValueError('unknown target release or artifact')
        context=binding['context']
        if not isinstance(context,dict): raise ValueError('invalid target context')
        if context.get('kind') == 'existing_target':
            object_keys(context,'kind')
            if payload['sources'].get(binding['artifact']) != {'kind':'existing_target','target':target}:
                raise ValueError('existing target binding lacks its authoritative source')
        else:
            object_keys(context,'kind address_model load_address entrypoint code_start_offset phase')
            if context['phase'] not in ('pre_handoff','handoff'): raise ValueError('invalid target phase')
            if context['kind'] != 'raw' or context['address_model'] not in ('runtime_absolute','local_offset'):
                raise ValueError('invalid raw target context')
            for key in ('load_address','entrypoint','code_start_offset'):
                if type(context[key]) is not int or not 0 <= context[key] < 0x1000000: raise ValueError('invalid target address')
            size=artifacts[binding['artifact']]['size']
            if not context['load_address']+context['code_start_offset'] <= context['entrypoint'] < context['load_address']+size:
                raise ValueError('entrypoint outside artifact context')
    if not isinstance(payload['correspondences'],list): raise ValueError('invalid correspondence collection')
    link_ids=set()
    for link in payload['correspondences']:
        object_keys(link,'id kind role left right evidence')
        identity(link['id'])
        if link['id'] in link_ids: raise ValueError('duplicate correspondence identity')
        link_ids.add(link['id'])
        if link['kind'] != 'identical_bytes' or link['role'] not in ('code','data') or not isinstance(link['evidence'],str):
            raise ValueError('unsupported correspondence claim')
        for side in ('left','right'):
            span=link[side];object_keys(span,'target offset size sha256')
            if span['target'] not in payload['targets']: raise ValueError('unknown correspondence target')
            extent=artifacts[payload['targets'][span['target']]['artifact']]['size']
            if type(span['offset']) is not int or type(span['size']) is not int or not 0 <= span['offset'] < span['offset']+span['size'] <= extent:
                raise ValueError('invalid correspondence range')
            sha(span['sha256'])
        if (link['left']['size'],link['left']['sha256']) != (link['right']['size'],link['right']['sha256']):
            raise ValueError('identical correspondence identity differs')
    return payload


@lru_cache(maxsize=64)
def _load(path, modified, size):
    path=Path(path)
    return validate(json.loads(path.read_text()),path.parent.parent)


def load_family(root, family):
    path=root/'games'/(identity(family)+'.json')
    stat=path.stat()
    result=_load(str(path.resolve()),stat.st_mtime_ns,stat.st_size)
    # Recipe files are dependencies even when the catalog file is unchanged.
    for d in result['derivations'].values():
        if digest(relative(root,d['recipe']).read_bytes()) != d['recipe_sha256']:
            raise ValueError('stale recovery recipe identity')
    return result


def binding_revision(family,target):
    b=family['targets'][target]
    producers=[d['recipe_sha256'] for d in family['derivations'].values() if b['artifact'] in d['outputs'].values()]
    return digest(json.dumps(dict(family=family['id'],target=target,binding=b,
        platform=family['releases'][b['release']]['platform'],recipes=sorted(producers)),sort_keys=True,separators=(',',':')).encode())


def target_link(root, target):
    found=[]
    for path in (root/'games').glob('*.json'):
        family=load_family(root,path.stem)
        if target in family['targets']:
            b=family['targets'][target]
            result=dict(game_family=family['id'],release_id=b['release'],artifact_id=b['artifact'])
            if b['context']['kind']=='raw': result['artifact_phase']=b['context']['phase']
            found.append(result)
    if len(found)>1: raise ValueError('target belongs to multiple game families')
    return found[0] if found else {}


def available(root,family_id,artifact,seen=frozenset()):
    if artifact in seen: return False
    family=load_family(root,family_id)
    if artifact not in family['artifacts']: return False
    if (root/'.amiga_reversing'/'artifacts'/artifact).is_file(): return True
    path=root/'.amiga_reversing'/'artifact_sources.json'
    private=json.loads(path.read_text()) if path.exists() else {}
    if artifact in private: return artifact in family['sources'] and Path(private[artifact]['path']).is_file()
    source=family['sources'].get(artifact)
    if source:
        if source['kind']=='private_media': return False
        from .binary_source import resolve_target_binary_source
        from .project_paths import resolve_project_dir
        try:
            binary=resolve_target_binary_source(resolve_project_dir(source['target'],root),root)
            return binary is not None and binary.path.is_file()
        except (FileNotFoundError,ValueError): return False
    inputs=[d['input'] for d in family['derivations'].values() if artifact in d['outputs'].values()]
    return len(inputs)==1 and available(root,family_id,inputs[0],seen|{artifact})


def bind_source(root,family_id,artifact,path,member=None):
    family=load_family(root,family_id)
    if artifact not in family['sources']: raise ValueError('only root sources can be bound privately')
    source=family['sources'][artifact]
    if source.get('format')=='stx':
        from .stx_recovery import read_stx
        data,_=read_stx(path,member)
    else:
        if member is not None or path.stat().st_size>32*1024*1024: raise ValueError('invalid private byte source')
        data=path.read_bytes()
    if len(data)!=family['artifacts'][artifact]['size'] or digest(data)!=artifact:
        raise ValueError('private source differs from declared artifact identity')
    config=root/'.amiga_reversing'/'artifact_sources.json'
    private=json.loads(config.read_text()) if config.exists() else {}
    private[artifact]=dict(path=str(path.resolve()),member=member)
    config.parent.mkdir(parents=True,exist_ok=True)
    config.write_text(json.dumps(private,indent=2)+'\n')
    return artifact


def materialize(root, family_id, artifact, _stack=frozenset()):
    family=load_family(root,family_id)
    if artifact not in family['artifacts']: raise ValueError('unknown artifact')
    if artifact in _stack: raise ValueError('artifact materialization cycle')
    expected=family['artifacts'][artifact]
    cache=root/'.amiga_reversing'/'artifacts'/artifact
    def checked(data):
        if len(data)!=expected['size'] or digest(data)!=artifact: raise ValueError('artifact content identity mismatch')
        return data
    if cache.exists(): checked(cache.read_bytes());return cache
    bindings=root/'.amiga_reversing'/'artifact_sources.json'
    private=json.loads(bindings.read_text()) if bindings.exists() else {}
    if artifact in private:
        if artifact not in family['sources']: raise ValueError('derived artifacts require their declared recipe')
        source=private[artifact]
        object_keys(source,'path member')
        fmt=family['sources'].get(artifact,{}).get('format','bytes')
        if fmt=='stx':
            from .stx_recovery import read_stx
            data,_=read_stx(Path(source['path']),source['member'])
        else:
            if source['member'] is not None: raise ValueError('byte source cannot name an archive member')
            path=Path(source['path'])
            if path.stat().st_size>32*1024*1024: raise ValueError('private byte source exceeds size bound')
            data=path.read_bytes()
        checked(data)
    elif artifact in family['sources']:
        source=family['sources'][artifact]
        if source['kind']=='private_media': raise FileNotFoundError('private artifact source is not configured: '+artifact)
        from .binary_source import resolve_target_binary_source
        from .project_paths import resolve_project_dir
        binary=resolve_target_binary_source(resolve_project_dir(source['target'],root),root)
        if binary is None: raise FileNotFoundError('existing target source is unavailable')
        data=checked(binary.read_bytes())
    else:
        choices=[(d,filename) for d in family['derivations'].values() for filename,a in d['outputs'].items() if a==artifact]
        if len(choices)!=1: raise ValueError('artifact needs an unambiguous materialization derivation')
        d,filename=choices[0]
        parent=materialize(root,family_id,d['input'],_stack|{artifact})
        from .stx_recovery import recover
        _,outputs=recover(parent.read_bytes(),json.loads(relative(root,d['recipe']).read_text()),project_root=root)
        data=checked(outputs[filename])
        # Cache all proven outputs once, never keep re-running the same decoder
        # for sibling source views. Unknown/unlisted captures do not enter it.
        for name,a in d['outputs'].items():
            value=outputs[name]
            if len(value)!=family['artifacts'][a]['size'] or digest(value)!=a:
                raise ValueError('derived sibling identity mismatch')
            _publish(root/'.amiga_reversing'/'artifacts'/a,value)
    _publish(cache,data)
    return cache


def _publish(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data: raise ValueError('artifact cache conflicts with proven bytes')
        return
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as temp:
        temp.write(data);temporary=Path(temp.name)
    try: temporary.replace(path)
    finally: temporary.unlink(missing_ok=True)


def verify_correspondence(root, family_id, link_id):
    family=load_family(root,family_id)
    matches=[link for link in family['correspondences'] if link['id']==link_id]
    if len(matches)!=1: raise ValueError('unknown or ambiguous correspondence')
    link=matches[0];values=[]
    for side in ('left','right'):
        span=link[side];artifact=family['targets'][span['target']]['artifact']
        data=materialize(root,family_id,artifact).read_bytes()[span['offset']:span['offset']+span['size']]
        if digest(data)!=span['sha256']: raise ValueError('stale correspondence bytes')
        values.append(data)
    if values[0]!=values[1]: raise ValueError('correspondence byte mismatch')
    return link


def unique_counterpart(left, offset, size, right):
    """Discover a candidate; exact bytes alone do not transfer semantic facts."""
    if type(offset) is not int or type(size) is not int or not 0 <= offset < offset+size <= len(left):
        raise ValueError('invalid counterpart seed range')
    value=left[offset:offset+size]
    start=right.find(value)
    if start<0: return None
    if right.find(value,start+1)>=0: raise ValueError('ambiguous identical-byte counterpart')
    return dict(offset=start,size=size,sha256=digest(value))
