import pathlib
import typing


def find_python_executable(root: typing.Union[pathlib.Path, str]) -> str:
    for rel in ("bin/python", "Scripts/python.exe"):
        p = pathlib.Path(root, rel)
        if p.is_file():
            return str(p)
    raise RuntimeError("Python executable not found")
