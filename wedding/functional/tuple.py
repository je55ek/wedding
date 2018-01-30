from typing import Tuple, TypeVar


A = TypeVar('A')
B = TypeVar('B')


def fst(t: Tuple[A, B]) -> A:
    return t[0]


def snd(t: Tuple[A, B]) -> B:
    return t[1]
