"""Small shared evidence seams for CPU calls and chipset transfer contracts.

This module does not store contracts, facts or review decisions. Callers supply
the canonical contract identity and persist results through restoration receipts.
Architectural CPU effects and physical bus transfers remain different streams.
"""
from __future__ import annotations

import hashlib
import json
from itertools import zip_longest

OUTCOMES = frozenset({
    'pass', 'mismatch', 'missing_prerequisite', 'timeout_not_observed_within_bounds',
    'unsupported', 'incomplete_truncated', 'stale', 'accepted_deviation',
})
IDENTITIES = frozenset({'original', 'candidate', 'fixture', 'contract', 'backend', 'profile'})
CONTRACT_PREFIX = 'BOUNDED_BEHAVIOUR_V1 '


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def canonical_contract(target_id, contract_id):
    """Read a bounded contract from active canonical function-summary notes.

    MAL owns the summary and DJ owns review. No fixture/result can author either.
    The existing note field carries the explicit bounded predicate without
    inventing a universal ABI or a second target metadata schema.
    """
    from .effective_metadata import effective_target_metadata
    from .project_paths import resolve_project_paths
    from .target_metadata import target_metadata_json_payload
    from .manual_actions import load_manual_projection
    from .decision_journal import read_decision_journal, project_decision_journal
    paths = resolve_project_paths(target_id)
    metadata = effective_target_metadata(paths.target_dir)
    summaries = target_metadata_json_payload(metadata).get('function_summaries', []) if metadata else []
    matches = []
    for summary in summaries:
        note = summary.get('note', '')
        if note.startswith(CONTRACT_PREFIX):
            try:
                contract = json.loads(note[len(CONTRACT_PREFIX):])
            except (ValueError, TypeError) as exc:
                raise BehaviourError('unsupported', 'Malformed canonical behaviour contract') from exc
            if not isinstance(contract,dict):
                raise BehaviourError('unsupported', 'Canonical behaviour contract must be an object')
            if contract.get('contract_id') == contract_id:
                if summary.get('callable_kind') != 'direct' or contract.get('entry_source') != summary.get('entry_offset'):
                    raise BehaviourError('unsupported', 'Contract entry differs from canonical summary')
                matches.append((summary,contract))
    if len(matches) != 1:
        raise BehaviourError('missing_prerequisite', 'One active canonical function-summary contract is required', contract_id=contract_id)
    summary, contract = matches[0]
    projection = load_manual_projection(paths.target_dir, binary_source=paths.binary_source)
    path = paths.target_dir/'manual_actions.jsonl'
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    actions = [r for r in records if r.get('action_id') in projection.active_action_ids
               and r.get('function_summary',{}).get('function_summary_id') == summary['function_summary_id']]
    if len(actions) != 1:
        raise BehaviourError('missing_prerequisite', 'Contract requires one active Manual Action identity')
    action_id = actions[0]['action_id'];journal=read_decision_journal(paths.target_dir)
    if not journal['valid']:
        raise BehaviourError('incomplete_truncated', 'Decision Journal is invalid')
    projected = project_decision_journal(journal['records'])
    accepted = [r for r in projected['accepted_facts'] if r.get('fact_type') == 'restoration_interpretation'
                and r.get('selected_identity',{}).get('subject_id') == action_id]
    return dict(contract=contract, contract_sha256=digest(summary), function_summary_id=summary['function_summary_id'],
                action_id=action_id, review_status='accepted' if len(accepted)==1 else 'unassessed',
                decision_id=accepted[0].get('decision_id') if len(accepted)==1 else None)


class BehaviourError(ValueError):
    def __init__(self, status, reason, **context):
        if status not in OUTCOMES or status == 'pass':
            raise ValueError('Invalid behavioural failure outcome')
        self.result = dict(status=status, reason=reason, **context)
        super().__init__(reason)


def admit_identities(expected, current):
    if set(expected) != IDENTITIES or set(current) != IDENTITIES:
        return dict(status='missing_prerequisite', reason='Six evidence identities are required')
    for key in sorted(IDENTITIES):
        for source in (expected, current):
            v = source[key]
            if not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v):
                return dict(status='missing_prerequisite', reason='Invalid evidence identity', identity=key)
        if expected[key] != current[key]:
            return dict(status='stale', reason='Bound assumption changed', identity=key,
                        expected=expected[key], actual=current[key])
    return dict(status='pass')


def compare_ordered(expected, actual, *, complete=True):
    """No sorting, deduplication, final-state substitution or skipped pass."""
    if complete is not True:
        return dict(status='incomplete_truncated', reason='Ordered stream is incomplete')
    if not isinstance(expected,(list,tuple)) or not isinstance(actual,(list,tuple)):
        return dict(status='unsupported',reason='Ordered event sequences are required')
    sentinel = object()
    for index, (a, b) in enumerate(zip_longest(expected, actual, fillvalue=sentinel)):
        if a != b:
            return dict(status='mismatch', first_divergence=index,
                        expected=None if a is sentinel else a,
                        actual=None if b is sentinel else b)
    return dict(status='pass', events_compared=len(expected), stream_sha256=digest(expected))


class MemoryEvidence:
    """Sparse knownness over a local shadow. Unknown zero/image bytes stay unknown.

    A write establishes later knownness, but its prior value is absent unless
    known. Writable ranges are a bounded call contract, never allocation proof.
    """
    def __init__(self, memory, known, writable, *, event_limit=2048):
        self.memory = memory
        self.known = dict(known)
        self.writable = tuple(writable)
        self.events = []
        self.event_limit = event_limit
        self.pc = None

    def access(self, kind, address, width, value):
        if type(address) is not int or type(width) is not int or width < 1 or not 0 <= address <= len(self.memory)-width:
            raise BehaviourError('unsupported', 'Access exceeds local shadow', address=address, width=width)
        if len(self.events) >= self.event_limit:
            raise BehaviourError('incomplete_truncated', 'Architectural event budget exhausted')
        if kind not in (0, 1, 2):
            raise BehaviourError('unsupported', 'Unknown architectural event kind')
        if kind != 1:
            missing = next((a for a in range(address, address+width) if a not in self.known), None)
            if missing is not None:
                raise BehaviourError('missing_prerequisite', 'Required memory is unknown',
                                     pc=self.pc, address=missing, width=width, kind=kind)
        elif not any(a <= address and address+width <= b for a, b in self.writable):
            raise BehaviourError('mismatch', 'Write outside bounded contract', pc=self.pc,
                                 address=address, width=width, value=value)
        event = dict(kind=('read', 'write', 'fetch')[kind], pc=self.pc,
                     address=address, width=width)
        if kind != 2:
            event['value'] = value
        if kind == 1:
            event['before'] = (int.from_bytes(self.memory[address:address+width], 'big')
                               if all(a in self.known for a in range(address,address+width)) else None)
            for a in range(address, address+width):
                self.known[a] = 'written_in_call'
        self.events.append(event)


def fixture_manifest(memory, known, *, donor_sha256, modeled_inputs, registers):
    """Publish extents/hashes, not captured bytes or proprietary guest images."""
    ranges = []
    for address in sorted(known):
        origin = known[address]
        if ranges and ranges[-1]['end'] == address and ranges[-1]['origin'] == origin:
            ranges[-1]['end'] += 1
        else:
            ranges.append(dict(start=address, end=address+1, origin=origin))
    for item in ranges:
        item['sha256'] = hashlib.sha256(memory[item['start']:item['end']]).hexdigest()
    return dict(schema_version=1, donor_sha256=donor_sha256, registers=registers,
                known_ranges=ranges, modeled_inputs=modeled_inputs,
                otherwise='unknown; backing image/zero values are not evidence')


def check_producer_consumer(events, *, start, end, complete=True, read_stride=4, read_offset=2):
    """Check a bounded physical transfer stream, without seeded scratch values."""
    if complete is not True:
        return dict(status='incomplete_truncated', reason='Physical transfer stream is incomplete')
    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= 0x1000000
            or type(read_stride) is not int or not 1 <= read_stride <= 4096
            or type(read_offset) is not int or not 0 <= read_offset < read_stride
            or not isinstance(events,list)):
        return dict(status='unsupported',reason='Invalid bounded transfer contract')
    if len(events)>4096:
        return dict(status='incomplete_truncated',reason='Transfer verification budget exhausted')
    if not events:
        return dict(status='timeout_not_observed_within_bounds', reason='No transfers in the window')
    written = {}
    counts = dict(read=0, write=0)
    for index, event in enumerate(events):
        if (not isinstance(event,dict) or event.get('engine') != 'blitter'
                or type(event.get('size')) is not int or event['size'] != 2
                or type(event.get('address')) is not int or event.get('access') not in counts):
            return dict(status='unsupported', first_divergence=index, reason='Requires blitter WORD transfers')
        address, access = event['address'], event['access']
        if not start <= address <= end-2:
            return dict(status='mismatch', first_divergence=index, reason='Transfer outside scratch contract', actual=event)
        try:
            value = int(event['data'],16)
        except (KeyError,ValueError,TypeError):
            return dict(status='unsupported',first_divergence=index,reason='Malformed transfer value')
        if not 0 <= value <= 65535:
            return dict(status='unsupported', first_divergence=index, reason='Transfer value exceeds WORD')
        raw = value.to_bytes(2, 'big')
        if access == 'read':
            if (address-start-read_offset) % read_stride:
                return dict(status='mismatch', first_divergence=index, reason='Wrong selected scratch WORD', actual=event)
            if any(written.get(address+i) != b for i, b in enumerate(raw)):
                return dict(status='mismatch', first_divergence=index, reason='Read lacks matching preceding producer', actual=event)
        else:
            written.update((address+i, b) for i, b in enumerate(raw))
        counts[access] += 1
    if not all(counts.values()):
        return dict(status='incomplete_truncated', reason='Producer and consumer are both required', counts=counts)
    return dict(status='pass', counts=counts, events_checked=len(events),
                stream_sha256=digest(events), observed_byte_extent=[min(written), max(written)+1],
                scope='Only the supplied ordered window; no initial seed, allocation or all-callers lifetime proof')
