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
    return cata(f, lambda: None)


def cata(exists: Callable[[A], B], absent: Callable[[], B]) -> Callable[[Optional[A]], B]:
    """Construct a catamorphism over Optional.

    Args:
        exists: A function from A to B invoked in the case an Optional is populated.
        exists: A callable that produces a B, invoked in the case an Optional is not populated.

    Returns:
        A function from Optional[A] to B.
    """
    def _cata(m: Optional[A]) -> B:
        return (
            exists(m) if m is not None else
            absent()
        )
    return _cata
