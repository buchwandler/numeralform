from __future__ import annotations

import subprocess
import sys


def test_import_does_not_load_external_oracles():
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import numeralform; "
                "assert 'icu' not in sys.modules; "
                "assert 'num2words' not in sys.modules"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
