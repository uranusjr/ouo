import appdirs
import contextlib
import dataclasses
import functools
import logging
import operator
import pathlib
import subprocess
import tempfile
import typing

import packaging.version
import packaging_dists

from ._meta import Wheel, is_python_compatible
from ._utils import find_python_executable


logger = logging.getLogger(__name__)


def _get_pip_wheel_directory() -> pathlib.Path:
    return pathlib.Path(appdirs.user_data_dir("ouo"), "pip-wheels")


@dataclasses.dataclass()
class Fetcher:
    """Manage pip wheels in a directory.

    This class takes two arguments

    * ``directory`` specifies where pip wheels it should be managing are in.
    * ``python`` specifies the Python command used to run pip with.

    Users can call ``ensure_pip()`` to get a ``PipWheel`` instance that
    represents the best locally available pip wheel. If no such wheels are
    available, a pip wheel will be downloaded automatically.

    A ``upgrade_pip()`` method is also available to explicitly fetch the latest
    pip wheel with ``pip download``.
    """

    _directory: pathlib.Path
    _python: str

    @classmethod
    def default(cls, root: pathlib.Path) -> "Fetcher":
        return cls(_get_pip_wheel_directory(), find_python_executable(root))

    def _iter_pip_wheels(self) -> typing.Iterator[Wheel]:
        if not self._directory.is_dir():
            return
        for path in self._directory.iterdir():
            if path.suffix != ".whl":
                continue
            try:
                dist = packaging_dists.parse(path.name)
            except packaging_dists.InvalidDistribution:
                continue
            if not isinstance(dist.version, packaging.version.Version):
                continue
            wheel = Wheel(path, dist.project, dist.version)
            if not is_python_compatible(self._python, wheel):
                continue
            yield wheel

    def _find_best_pip(self) -> typing.Optional[Wheel]:
        """Find the best pip wheel locally available.

        The implementation intentionally evaluates all wheel file names with
        ``sorted()`` eagerly, and filter out incompatible ones afterwards.
        This is because the Compatibility check require reading the wheel
        file's content, and is more expensive than listing the directory.
        """
        wheels = sorted(
            self._iter_pip_wheels(),
            key=operator.attrgetter("version"),
            reverse=True,
        )
        if not wheels:
            return None
        iterator = filter(
            functools.partial(is_python_compatible, self._python),
            wheels,
        )
        return next(iterator, None)

    @contextlib.contextmanager
    def _venv_pip(self) -> typing.Iterator[typing.Iterable[str]]:
        with tempfile.TemporaryDirectory() as td:
            subprocess.run([self._python, "-m", "venv", td], check=True)
            python = find_python_executable(td)
            yield (python, "-m", "pip")

    @contextlib.contextmanager
    def _best_pip(self, w: Wheel) -> typing.Iterator[typing.Iterable[str]]:
        yield (self._python, "{}/pip".format(w.path))

    def upgrade_pip(self):
        pip_wheel = self._find_best_pip()
        if pip_wheel:
            logger.info("Downloading pip wheel...")
            manager = self._best_pip(pip_wheel)
        else:
            logger.info("Populating pip with a fresh virtual environment...")
            manager = self._venv_pip()
        self._directory.mkdir(parents=True, exist_ok=True)
        with manager as command:
            args = [
                *command,
                "download",
                "pip",
                "--only-binary=pip",
                "--disable-pip-version-check",
            ]
            subprocess.run(args, check=True, cwd=self._directory)

    def ensure_pip(self) -> Wheel:
        pip_wheel = self._find_best_pip()
        if pip_wheel:
            return pip_wheel
        self.upgrade_pip()
        pip_wheel = self._find_best_pip()
        if not pip_wheel:
            raise RuntimeError("pip wheel not found")
        return pip_wheel
