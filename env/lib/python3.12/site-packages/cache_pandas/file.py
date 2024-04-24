from __future__ import annotations

import functools
import logging
import os
import pathlib
import sys
import time
from typing import Callable, Optional, Union

if sys.version_info < (3, 10):  # pragma: no cover
    from typing_extensions import ParamSpec, TypeAlias  # pylint: disable=only-importing-modules-is-allowed
else:  # pragma: no cover
    from typing import ParamSpec, TypeAlias

import pandas as pd

PathLike: TypeAlias = Union[str, pathlib.Path]
P = ParamSpec("P")


class FileNeedsRefresh(FileNotFoundError):
    """File exists, but needs to be refreshed."""

    pass


def cache_to_csv(
        filepath: PathLike, refresh_time: Optional[float] = None, create_dirs: bool = True
) -> Callable[[Callable[P, pd.DataFrame]], Callable[P, pd.DataFrame]]:
    """Decorator-factory that generates a decorator that caches a pandas DataFrame to a csv file for faster retrieval
    in the future.

    Retrieves the cached file, or if that file doesn't exist/needs to be refreshed, calls the function and caches its
    result.

    Args:
        filepath: Filepath to save the cached CSV.
        refresh_time: Time seconds. If the file has not been updated in longer than refresh_time, generate the file
            anew. If `None`, the file will never be regenerated if a cached version exists.
        create_dirs: Whether to create necessary directories containing the given filepath.

    Returns:
        Decorator that caches a pandas DataFrame to a csv file for faster retrieval in the future.
    """

    def cache_decorator(func: Callable[P, pd.DataFrame]) -> Callable[P, pd.DataFrame]:
        """Function decorator that caches its function's returned DataFrame to file."""

        @functools.wraps(func)
        def retrieve_or_cache(*args: P.args, **kwargs: P.kwargs) -> pd.DataFrame:
            """Retrieves the cached file, or if it doesn't exist/needs to be refreshed, calls the function and caches
            its result.
            """
            try:
                if refresh_time is not None and os.path.getmtime(filepath) + int(refresh_time) < time.time():
                    logging.info(f"File {filepath}n is too old.")
                    raise FileNeedsRefresh(f"{filepath} is too old and needs to be refreshed")
                dataframe: pd.DataFrame = pd.read_csv(filepath, index_col=0)
            except FileNotFoundError:
                if create_dirs:
                    pathlib.Path(filepath).parent.mkdir(exist_ok=True, parents=True)
                dataframe = func(*args, **kwargs)
                dataframe.to_csv(filepath)
            return dataframe

        return retrieve_or_cache

    return cache_decorator
