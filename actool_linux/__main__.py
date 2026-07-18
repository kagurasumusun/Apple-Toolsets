"""Allow ``python3 -m actool_linux`` to invoke the CLI."""
from .stable.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
