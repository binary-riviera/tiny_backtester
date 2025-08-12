from collections.abc import Callable
from functools import wraps
from tiny_backtester import logger


def log(f: Callable):
    """log entry and exit of method"""

    @wraps(f)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v}" for k, v in kwargs.items()]
        sig = ",".join(args_repr + kwargs_repr)
        logger.debug(f"calling {f.__name__}({sig})")
        value = f(*args, **kwargs)
        logger.debug(f"{f.__name__} returned {repr(value)}")
        return value

    return wrapper_debug
