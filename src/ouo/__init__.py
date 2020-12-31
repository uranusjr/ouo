"""Run pip outside of environment."""

import os
import pathlib
import sys


__version__ = "0.0.1"


def main() -> int:
    from . import _fetch, _proc

    try:
        root = pathlib.Path(os.environ["VIRTUAL_ENV"])
    except KeyError:
        print("Environment variable VIRTUAL_ENV not found", file=sys.stderr)
        return -1
    if not root.is_dir():
        print("Environment variable VIRTUAL_ENV not valid", file=sys.stderr)
        return -1
    runner = _proc.get_runner(root)
    pip_wheel = _fetch.Fetcher.default(root).ensure_pip()
    return runner.run("{}/pip".format(pip_wheel.path), *sys.argv[1:])
