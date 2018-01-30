from typing import TypeVar, Optional, Callable, Any


A = TypeVar('A')
B = TypeVar('B')


def not_none(x: Any) -> bool:
    return x is not None


def fmap(f: Callable[[A], B]) -> Callable[[Optional[A]], Optional[B]]:
    """Lift a function into the Optional functor.

    Args:
        f: A function from A to B.

    Returns:
        A function from Optional[A] to Optional[B].
    """
    def _fmap(m: Optional[A]) -> Optional[B]:
        return (
            f(m) if m is not None else
            None
        )
    return _fmap
