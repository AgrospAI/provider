import requests
import pytest

from ocean_provider.file_types import definitions as defs


@pytest.mark.parametrize(
    "header, expected",
    [
        # RFC 5987 encoded filename (UTF-8 percent-encoding)
        ("attachment; filename*=UTF-8''%e2%82%ac%20rates.pdf", "€ rates.pdf"),
        # Legacy MIME Q encoding
        ('attachment; filename="=?UTF-8?Q?caf=C3=A9.txt?="', "café.txt"),
        # Simple filename
        ('attachment; filename="example.txt"', "example.txt"),
        # Empty or missing header falls back
        ("", "downloaded_file"),
        (None, "downloaded_file"),
    ],
)
def test_decode_content_disposition_filename(header, expected):
    # Call the instance method directly via the class, passing None as self
    result = defs.EndUrlType._decode_content_disposition_filename(None, header)
    assert result == expected


def test_rfc5987_with_different_encoding_label():
    # Some servers may provide lowercase or different label casings
    header = "inline; filename*=utf-8''hello%20world.txt"
    result = defs.EndUrlType._decode_content_disposition_filename(None, header)
    assert result == "hello world.txt"
