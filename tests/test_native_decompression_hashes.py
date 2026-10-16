"""Native source-range and provider hashes are byte identities on this host."""
import hashlib
import shutil

import pytest

from amiga_reversing.disasm.c_backend import identify_packed_range_with_c_backend


@pytest.mark.parametrize('size', [1, 8192, 17003])
def test_native_identification_hashes_the_requested_range_and_provider(tmp_path, size):
    # An existing harmless executable supplies identity metadata. This test does
    # not claim Ancient codec interoperability or install an external provider.
    provider = shutil.which('false')
    if provider is None:
        pytest.skip('This POSIX provider-identity fixture requires the system false utility')
    payload = bytes((i % 251 for i in range(size)))
    path = tmp_path/'input with spaces.bin'
    path.write_bytes(b'PREFIX'+payload+b'SUFFIX')
    report = identify_packed_range_with_c_backend(path, 6, size, provider_path=provider)
    result = report['packed_payloads'][0]
    assert report['status'] == 'ok' and result['found'] is False
    assert result['source_offset'] == 6 and result['packed_size'] == size
    assert result['source_sha256'] == hashlib.sha256(payload).hexdigest()
    with open(provider, 'rb') as binary:
        assert result['provider_sha256'] == hashlib.sha256(binary.read()).hexdigest()
