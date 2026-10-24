"""Translate observation coordinates from an admitted native layout, not placement.

Original-address reads and abandoned-range guards are different domains. Active
RAM may reuse an abandoned image address; exclude that declared RAM explicitly
without claiming that the remaining guards cover every instruction or DMA fetch.
"""

def observed_address(plan,address,size=1):
    if type(address) is not int or type(size) is not int or size<=0:
        raise ValueError('Observation requires an explicit nonempty extent')
    intersect=[];complete=[]
    for region in plan['regions']:
        start=region['original_address'];end=start+region['size']
        if address<end and start<address+size:
            delta=region['runtime_address']-start;intersect.append(delta)
            if start<=address and address+size<=end:complete.append(delta)
    if not intersect:return address
    if not complete or len(set(intersect))!=1:
        raise ValueError('Observation crosses incomplete or conflicting native mappings')
    return address+complete[0]


def abandoned_ranges(plan,address,size):
    """Subtract currently live native roots; overlapping reuse is not watched."""
    spans=[(address,address+size)]
    for region in plan['regions']:
        if region.get('parent_region_id'):continue
        start=region['runtime_address'];end=start+region['size'];remaining=[]
        for lo,hi in spans:
            if end<=lo or start>=hi:remaining.append((lo,hi));continue
            if lo<start:remaining.append((lo,start))
            if end<hi:remaining.append((end,hi))
        spans=remaining
    return [(lo,hi-lo) for lo,hi in spans]
