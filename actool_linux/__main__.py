"""Allow ``python3 -m actool_linux`` to invoke the CLI."""
from actool_linux.tools.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
