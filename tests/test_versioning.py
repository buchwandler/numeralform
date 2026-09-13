from __future__ import annotations

import numeralform
from numeralform.__about__ import __version__ as fallback_version


def test_source_fallback_version_is_neutral() -> None:
    assert fallback_version == "0+unknown"
    assert fallback_version != "0.1.4"
    assert numeralform.__version__
