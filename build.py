"""Required to build modules developed using Cython.

Used by Poetry to automatically produce setup.py file.
"""

import contextlib
import multiprocessing
from pathlib import Path
from typing import Optional, Union

import numpy
from Cython.Build import cythonize
from setuptools import Extension

PathLike = Union[str, Path]

with contextlib.suppress(RuntimeError):
    multiprocessing.set_start_method("fork")

EXTENSION_KWARGS = {
    "include_dirs": [".", numpy.get_include()],
    "define_macros": [("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
}
CYTHON_DIRECTIVES = {"language_level": 3, "embedsignature": True}


def collect_extensions(
    source_dir: PathLike,
    extension_kwargs: Optional[dict] = None,
) -> list[Extension]:

    if not isinstance(source_dir, Path):
        source_dir = Path(source_dir)

    if extension_kwargs is None:
        extension_kwargs = EXTENSION_KWARGS

    extensions: list[Extension] = []

    for pyx_file in source_dir.rglob("*.pyx"):
        module_path = pyx_file.relative_to(source_dir).with_suffix("")
        module_name = str(module_path).replace("/", ".")

        extension = Extension(name=module_name, sources=[str(pyx_file)], **extension_kwargs)
        extensions.append(extension)

    return extensions


def cythonize_extensions(
    extensions: list[Extension],
    compiler_directives: Optional[dict[str, Union[int, bool]]] = None,
) -> list[Extension]:

    if compiler_directives is None:
        compiler_directives = CYTHON_DIRECTIVES

    try:
        nthreads = multiprocessing.cpu_count()
    except (NotImplementedError, OSError):
        nthreads = 0

    try:
        return cythonize(
            module_list=extensions,
            nthreads=nthreads,
            compiler_directives=compiler_directives,
        )
    except PermissionError:
        # Some restricted environments deny the semaphore/sysconf calls used by
        # ProcessPoolExecutor. Retry sequentially so local builds still work.
        return cythonize(
            module_list=extensions,
            nthreads=0,
            compiler_directives=compiler_directives,
        )


def build(setup_kwargs: dict) -> None:
    """Build Cython extensions.

    Parameters
    ----------
    setup_kwargs
    """
    # source_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    # packages = ["zemax2raysect"]

    # extensions = []
    # for package in packages:
    #     for root, _, files in os.walk(os.path.join(source_path, package)):
    #         for file in files:
    #             _, ext = os.path.splitext(file)
    #             if ext == ".pyx":
    #                 pyx_file = os.path.relpath(os.path.join(root, file), source_path)
    #                 module = os.path.splitext(pyx_file)[0].replace("/", ".")
    #                 extensions.append(
    #                     Extension(
    #                         module,
    #                         [os.path.join(source_path, pyx_file)],
    #                         **extension_kwargs,
    #                     )
    #                 )

    # extensions = cythonize(
    #     extensions,
    #     nthreads=multiprocessing.cpu_count(),
    #     compiler_directives=cython_directives,
    # )

    source_path = Path("src")
    extensions = cythonize_extensions(collect_extensions(source_path))

    if setup_kwargs is not None:
        setup_kwargs.update({"ext_modules": extensions})


if __name__ == "__main__":
    source_path = Path("src")
    extensions = cythonize_extensions(collect_extensions(source_path))
