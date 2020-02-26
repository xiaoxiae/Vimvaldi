from __future__ import annotations
from dataclasses import dataclass
from typing import *
from copy import deepcopy

from collections import namedtuple
from util import *
from math import log

# DEBUG
import logging

logging.basicConfig(filename="vimvaldi.log", level=logging.DEBUG)


class Notation:
    """A class for storing musical notation symbols used in the program."""

    Clef = namedtuple("Clef", ["TREBLE", "ALTO", "BASS"])("𝄞", "𝄡", "𝄢")
    Accidental = namedtuple("Accidental", ["FLAT", "NATURAL", "SHARP"],)("♭", "♮", "♯")

    Dynamics = namedtuple(
        "Dynamics", ["PIANO", "MEZZO", "FORTE", "CRESCENDO", "DECRESCENDO"],
    )("𝆏", "𝆐", "𝆑", "𝆒", "𝆓",)

    class Time:
        COMMON = "𝄴"

        @classmethod
        def from_fraction(cls, num: int, den: int) -> str:
            return f"{num}/{den}"


class NoteLike:
    """A class representing a thing with Rest and Note-like attributes (duration, dot,
    could have a crescendo/...)."""

    def __init__(
        self, duration, symbols, dotted=False, crescendo=False, decrescendo=False
    ):
        self.duration = duration
        self.symbols = symbols

        self.dotted = dotted
        self.crescendo = crescendo
        self.decrescendo = decrescendo

    def get_duration(self, ignore_dot=False):
        """The duration of the note-like object (including the dot)."""
        return self.duration * (1 if not self.dotted or ignore_dot else (2 / 3))

    def __str__(self):
        """The string representation of the note-like object."""
        return self.symbols[int(log(self.get_duration(ignore_dot=True), 2))]


@dataclass
class Note(NoteLike):
    """A class for interpreting a note."""

    def __init__(self, duration, pitch, dotted=False, flat=False, sharp=False):
        super().__init__(
            duration,
            namedtuple(
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
            )("𝅝", "𝅗𝅥", "𝅘𝅥", "𝅘𝅥𝅮", "𝅘𝅥𝅯", "𝅘𝅥𝅰", "𝅘𝅥𝅱"),
            dotted=dotted,
        )

        self.pitch = pitch

        self.flat = flat
        self.sharp = sharp

    @classmethod
    def from_identifier(cls, identifier: str) -> Union[Note, None]:
        """Returns a Note object initialized from an identifier in the following form:

                               [<duration>]<pitch>[is/es][<octave>][.]

        - duration -- the duration of the note (1 is whole, 2 is half...); defaults to 4
        - pitch -- the pitch of the note (c/d/e/f/g/a/h)
        - octave -- the octave of the node; defaults to 1
        """

        # get duration
        duration, identifier = pop_number(identifier)
        if duration == 0:
            duration = 4
        elif not is_power_of_2(duration) and duration > 64:
            return

        # get pitch
        pitch, identifier = pop_char(identifier)
        if pitch not in "cdefgah":
            return

        # check for flats/sharps
        flat, sharp = False, False
        if identifier[:2] in ("is", "es"):
            flat = identifier[0] == "i"
            sharp = identifier[0] == "e"
            identifier = identifier[2:]

        octave, identifier = pop_number(identifier)
        if octave == 0:
            octave = 1

        return Note(duration, (pitch, octave), flat=flat, sharp=sharp)


@dataclass
class Rest(NoteLike):
    """A class for working with rests."""

    def __init__(self, duration, dotted=False):
        super().__init__(
            duration,
            namedtuple(
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
            )("𝄻", "𝄼", "𝄽", "𝄾", "𝄿", "𝅀", "𝅁"),
            dotted=dotted,
        )

    @classmethod
    def from_identifier(cls, identifier: str) -> Union[Rest, None]:
        """Returns a Note object initialized from an identifier in the following form:

                               [<duration>]r[.]

        - duration -- the duration of the note (1 is whole, 2 is half...)
        """
        # get duration
        duration, identifier = pop_number(identifier)
        if duration == 0:
            duration = 4
        elif not is_power_of_2(duration) and duration > 64:
            return

        # check for the r symbol
        r, identifier = pop_char(identifier)
        if r != "r":
            return

        return Rest(duration, dotted=pop_char(identifier)[0] == ".")


class Score:
    """A class for storing the state of the score (and methods to operate on it)."""

    def __init__(self, clef=Notation.Clef.TREBLE, time: Time = Notation.Time.COMMON):
        """Initialize the Score."""
        self.clef = clef
        self.time = time

        self.notes: List[Union[Note, Rest]] = []

        self.position = 0

    def __getitem__(self, i) -> Union[Note, Rest, None]:
        """Returns the i-th item from the Score."""
        return self.notes[i]

    def __len__(self) -> int:
        return len(self.notes)

    def next(self):
        """Point to the next item in the menu."""
        if self.position != len(self.notes):
            self.position += 1

    def split(self, item, duration) -> List[type(item)]:
        """Takes an item and 1/duration that the item should fit and returns a list of
        items that evenly fit this duration."""
        d = 1
        items = []

        while duration > 0:
            if d <= duration:
                i = deepcopy(item)
                i.duration = int(1 / d)
                items.append(i)
                duration -= d

            d /= 2

        return items

    def previous(self):
        """Point to the previous item in the menu."""
        if self.position != 0:
            self.position -= 1

    def remove(self) -> bool:
        """Replace the next non-rest string with a rest. If there are rests of length 1
        one after another, remove them all."""
        total = 0

        for i in range(self.position, len(self.notes)):
            # if it's not a rest, replace it and return
            if type(self.notes[i]) is not Rest:
                self.notes[i] = Rest(self.notes[i].get_duration())
                return

            total += 1 / self.notes[i].get_duration()

            if total == 1:
                # pop all of the rests that add up to 1
                for _ in range(self.position, i + 1):
                    self.notes.pop(self.position)

                return

    def insert(self, string) -> bool:
        """Add an item to the score, returning True if something was added."""
        for c in [Note, Rest]:
            item = c.from_identifier(string)

            if item is not None:
                # if we're not adding to the end of the note editor, add padding rests
                if self.position != len(self.notes):
                    # TODO
                    return

                remaining_duration = sum(1 / n.get_duration() for n in self.notes) % 1

                # if the rest/note fits in the current bar, simply add it
                if remaining_duration + 1 / item.get_duration() <= 1:
                    self.notes.insert(self.position, item)
                    self.position += 1

                else:
                    # duration before and after the bar
                    before_duration = 1 - remaining_duration
                    after_duration = 1 / item.get_duration() - (1 - remaining_duration)

                    # split into multiple items
                    before_items = self.split(item, before_duration)
                    after_items = self.split(item, after_duration)

                    # add the items to the note sheet
                    self.notes = (
                        self.notes[: self.position]
                        + before_items
                        + after_items
                        + self.notes[self.position :]
                    )

                    self.position += len(before_items) + len(after_items)

                return True

        return False
