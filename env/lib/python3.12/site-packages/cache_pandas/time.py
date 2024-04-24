import functools
import sys
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Protocol, cast

import pandas as pd

if sys.version_info < (3, 10):  # pragma: no cover
    from typing_extensions import ParamSpec, TypeAlias
else:  # pragma: no cover
    from typing import ParamSpec, TypeAlias

P = ParamSpec("P")

PandasFunc: TypeAlias = Callable[P, pd.DataFrame]


class LRUCacheWrapper(Protocol[P]):
    lifetime: timedelta
    expiration: datetime

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> pd.DataFrame: pass

    def cache_clear(self): pass


def timed_lru_cache(
        seconds: Optional[int] = None, maxsize: Optional[int] = None, typed: bool = True
) -> Callable[[PandasFunc], PandasFunc]:
    """Decorator-factory that generates a decorator that caches a pandas DataFrame in memory (with some expiration time)
    for faster retrieval in the future.

    Args:
        seconds: Number of seconds to retain the cache.
        maxsize: Maximum number of items to store in the cache.
        typed: Whether arguments of different types will be cached separately.

    Returns:
        Decorator that caches a pandas DataFrame in memory (with an expiration time).
    """

    def cache_decorator(func: PandasFunc) -> PandasFunc:
        """Function decorator that caches its function's returned DataFrame to memory."""
        lru_func = cast(LRUCacheWrapper, functools.lru_cache(maxsize=maxsize, typed=typed)(func))

        if seconds is None:
            return lru_func

        lru_func.lifetime = timedelta(seconds=seconds)
        lru_func.expiration = datetime.now(timezone.utc) + lru_func.lifetime

        @functools.wraps(func)
        def retrieve_or_cache(*args: P.args, **kwargs: P.kwargs) -> pd.DataFrame:
            """Retrieves the cached DataFrame, or if it doesn't exist/needs to be refreshed, calls the function and
            caches its result.
            """
            if datetime.now(timezone.utc) >= lru_func.expiration:
                lru_func.cache_clear()
                lru_func.expiration = datetime.now(timezone.utc) + lru_func.lifetime

            return lru_func(*args, **kwargs)

        return cast(PandasFunc, retrieve_or_cache)

    return cache_decorator
