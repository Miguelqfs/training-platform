import sys

if sys.version_info[:2] != (3, 12):
    raise RuntimeError("Esta aplicação requer Python 3.12.")
