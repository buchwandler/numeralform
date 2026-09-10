from __future__ import annotations

from .run import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print(f"BENCHMARK ERROR: {exc}")
        raise SystemExit(2) from exc
