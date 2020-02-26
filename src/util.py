from typing import *


def center_coordinate(a: int, b: int) -> int:
    """Return the starting coordinate of an object of size b centered in an object 
    of size a."""
    return (a // 2) - (b // 2) - b % 2


def is_power_of_2(number: int):
    """Return True if the input _positive_ number is a power of 2."""
    while number != 1:
        if number % 2 != 0:
            return False
        number //= 2

    return True


def pop_number(string: str) -> Tuple[int, str]:
    """Pops a number from the beginning of the string."""
    number = 0
    while len(string) > 0 and string[0].isdigit():
        number = number * 10 + int(string[0])
        string = string[1:]

    return number, string


def pop_char(string: str) -> Tuple[int, str]:
    """Pops a number from the beginning of the string."""
    if len(string) == 0:
        return "", ""
    else:
        return string[0], string[1:]
