import dataclasses
import email.message
import pathlib
import subprocess
import sys

import packaging.utils
import packaging.specifiers

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata


@dataclasses.dataclass()
class Wheel:
    path: pathlib.Path
    name: str
    version: packaging.version.Version


def _read_metadata(wheel: Wheel) -> email.message.Message:
    distributions = importlib_metadata.distributions(
        name=wheel.name,
        path=[str(wheel.path)],
    )
    # The pip wheel must return at least one distribution instance.
    return next(iter(distributions)).metadata


def is_python_compatible(python: str, wheel: Wheel) -> bool:
    requires_python = _read_metadata(wheel)["Requires-Python"]
    if not requires_python:
        return True
    spec = packaging.specifiers.SpecifierSet(requires_python)
    code = "import sys; print('{}.{}'.format(*sys.version_info))"
    output = subprocess.check_output([python, "-c", code], encoding="ascii")
    return spec.contains(output.strip(), prereleases=True)
