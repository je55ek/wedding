from typing import TypeVar, Callable, Sequence
from toolz.functoolz import curry
from functools import reduce


A = TypeVar('A')
B = TypeVar('B')


@curry
def foldl(initial: A,
          accumulate: Callable[[A], Callable[[B], A]],
          bs: Sequence[B]) -> A:
    return reduce(lambda a, b: accumulate(a)(b), bs, initial)


@curry
def foldr(accumulate: Callable[[B], Callable[[A], A]],
          bs: Sequence[B],
          final: A) -> A:
    result = final
    for b in reversed(bs):
        result = accumulate(b)(result)
    return result
