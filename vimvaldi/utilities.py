"""A set of utility functions used throughout the project."""

from typing import *
import curses


def center_coordinate(a: int, b: int) -> int:
    """Return the starting coordinate of an object of size b centered in an object 
    of size a."""
    return (a // 2) - (b // 2) - b % 2


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


def draw_vertical_bar(window, x: int, y_s: int, y_e: int):
    """Draw the vertial bar on the window (with underlines!)."""
    for i in range(y_s, y_e):
        window.addstr(i, x, "|", curses.A_UNDERLINE)