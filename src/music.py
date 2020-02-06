from __future__ import annotations
from dataclasses import dataclass
from typing import *

from collections import namedtuple
from util import *
from math import log

# DEBUG
import logging

logging.basicConfig(filename="vimvaldi.log", level=logging.DEBUG)


class Notation:
    """A class for storing musical notation symbols used in the program."""

    Clef = namedtuple("Clef", ["TREBLE", "ALTO", "BASS"])("𝄞", "𝄡", "𝄢")

    Note = namedtuple(
        "Note",
        [
            "WHOLE",
            "HALF",
            "QUARTER",
            "EIGHT",
            "SIXTEENTH",
            "THIRTY_SECOND",
            "SIXTY_FOURTH",
        ],
    )("𝅝", "𝅗𝅥", "𝅘𝅥", "𝅘𝅥𝅮", "𝅘𝅥𝅯", "𝅘𝅥𝅰", "𝅘𝅥𝅱")

    Rest = namedtuple(
        "Rest",
        [
            "WHOLE",
            "HALF",
            "QUARTER",
            "EIGHT",
            "SIXTEENTH",
            "THIRTY_SECOND",
            "SIXTY_FOURTH",
        ],
    )("𝄻", "𝄼", "𝄽", "𝄾", "𝄿", "𝅀", "𝅁")

    Accidental = namedtuple("Accidental", ["FLAT", "NATURAL", "SHARP"],)("♭", "♮", "♯")

    Dynamics = namedtuple(
        "Dynamics", ["PIANO", "MEZZO", "FORTE", "CRESCENDO", "DECRESCENDO"],
    )("𝆏", "𝆐", "𝆑", "𝆒", "𝆓",)

    class Time:
        COMMON = "𝄴"

        @classmethod
        def from_fraction(cls, num: int, den: int) -> str:
            return f"{num}/{den}"


@dataclass
class Note:
    """A class for interpreting a note."""

    pitch: Tuple[str, int]
    duration: int

    @classmethod
    def from_identifier(cls, identifier: str) -> Union[Note, None]:
        """Returns a Note object initialized from an identifier in the following form:

                               [<duration>][<pitch>][.]

        The arguments mean the following (+ is optional, - is mandatory):
        + duration -- the duration of the note (1 is whole, 2 is half...)
        - pitch -- the pitch of the note (c/d/e/f/g/a/h), with a few possible additions:
            + is/es for sharps and flats
            + ''' or ',' may be added (even repeatedly), indicating the octave
            + . for a dotted note

        Returns None if the parsing of the identifier was unsuccessful.
        """

        # parse the number
        number, i = 0, 0
        while i < len(identifier) and identifier[i].isdigit():
            number = number * 10 + int(identifier[i])
            i += 1

        # set number default pitch to a quarter note
        if number == 0:
            number = 4

        if i == len(identifier) - 1:
            return None

    def __str__(self):
        pass


@dataclass
class Notes:
    """A class for working with multiple notes."""

    notes: Sequence[Note]


@dataclass
class Rest:
    """A class for working with rests."""

    duration: int

    @classmethod
    def from_identifier(cls, identifier: str) -> Union[Rest, None]:
        """Returns a Rest object initialized from an identifier."""
        # check for rest symbol and 0-length rest
        if identifier[-1] != "r" or identifier[0] == "0":
            return

        # parse the number
        duration, i = 0, 0
        while identifier[i].isdigit():
            duration = duration * 10 + int(identifier[i])
            i += 1

        # set duration default pitch to a quarter rest
        if duration == 0:
            duration = 1

        # restrict it to power of 2
        if i != len(identifier) - 1 or not is_power_of_2(duration) or duration > 64:
            return

        return Rest(duration)

    def __str__(self):
        return Notation.Rest[int(log(self.duration, 2))]


class Score:
    """A class for storing the state of the score (and methods to operate on it)."""

    def __init__(self, clef=Notation.Clef.TREBLE, time: Time = Notation.Time.COMMON):
        """Initialize the Score."""
        self.clef = clef
        self.time = time

        self.notes: List[Union[Note, Notes, Rest]] = []

        self.position = 0

    def __getitem__(self, i) -> Union[Note, Notes, Rest, None]:
        """Returns the i-th item from the Score."""
        return self.notes[i]

    def __len__(self) -> int:
        return len(self.notes)

    def insert(self, string) -> bool:
        """Add an item to the score, returning True if something was added."""
        # try to parse each of the
        for c in [Note, Rest]:
            item = c.from_identifier(string)

            if item is not None:
                self.notes.insert(self.position, item)
                self.position += 1

                return True

        return False
