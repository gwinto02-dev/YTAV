import time
import functools
from typing import Callable, Type, Tuple
from src.utils.logger import logger

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying a function with exponential backoff.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.warning(f"Function '{func.__name__}' failed after {max_attempts} attempts: {e}")
                        raise e
                    logger.debug(f"Attempt {attempt} for '{func.__name__}' failed ({e}). Retrying in {current_delay:.1f}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            if last_exception:
                raise last_exception
        return wrapper
    return decorator
