import dataclasses
import os
import pathlib
import subprocess

from ._utils import find_python_executable


@dataclasses.dataclass()
class _Runnable:
    _root: pathlib.Path

    def run(self, *args: str) -> int:
        raise NotImplementedError()


class _POSIXRunnable(_Runnable):
    def run(self, *args: str) -> int:
        # This should never return.
        python = find_python_executable(self._root)
        os.execlp(python, python, *args)


class _DefaultRunnable(_Runnable):
    def run(self, *args: str) -> int:
        python = find_python_executable(self._root)
        proc = subprocess.Popen([python, *args])

        # This mimics the stdlib implementation of subprocess.call(), but
        # catches KeyboardInterrupt bubbled up from the child process, so
        # the parent Python wrapper can exit cleanly with the correct code.
        try:
            with proc:
                proc.wait()
        except KeyboardInterrupt:
            pass
        finally:
            proc.kill()

        return proc.returncode


def get_runner(root: pathlib.Path) -> _Runnable:
    if os.name == "posix":
        return _POSIXRunnable(root)
    return _DefaultRunnable(root)
