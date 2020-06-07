"""A module for storing musical-related classes."""

import abjad


def from_duration(cls, duration: abjad.utilities.Duration) -> str:
    """Return the note/rest string corresponding with the given duration."""
    return {
        1: cls.WHOLE,
        1 / 2: cls.HALF,
        1 / 4: cls.QUARTER,
        1 / 8: cls.EIGHT,
        1 / 16: cls.SIXTEENTH,
        1 / 32: cls.THIRTY_SECOND,
        1 / 64: cls.SIXTY_FOURTH,
    }[float(duration)]


class Notation:
    """A class for storing musical notation symbols used in the program."""

    class Clef:
        TREBLE = "𝄞"
        ALTO = "𝄡"
        BASS = "𝄢"

    class Accidental:
        FLAT = "♭"
        NATURAL = "♮"
        SHARP = "♯"

    class Dynamics:
        PIANO = "𝆏"
        MEZZO = "𝆐"
        FORTE = "𝆑"
        CRESCENDO = "𝆒"
        DECRESCENDO = "𝆓"

    class Time:
        COMMON = "𝄴"

    class Note:
        WHOLE = "𝅝"
        HALF = "𝅗𝅥"
        QUARTER = "𝅘𝅥"
        EIGHT = "𝅘𝅥𝅮"
        SIXTEENTH = "𝅘𝅥𝅯"
        THIRTY_SECOND = "𝅘𝅥𝅰"
        SIXTY_FOURTH = "𝅘𝅥𝅱"

        @classmethod
        def from_duration(cls, duration: abjad.Duration) -> str:
            return from_duration(cls, duration)

    class Rest:
        WHOLE = "𝄻"
        HALF = "𝄼"
        QUARTER = "𝄽"
        EIGHT = "𝄾"
        SIXTEENTH = "𝄿"
        THIRTY_SECOND = "𝅀"
        SIXTY_FOURTH = "𝅁"

        @classmethod
        def from_duration(cls, duration: abjad.Duration) -> str:
            return from_duration(cls, duration)

    class Bar:
        SINGLE = "𝄀"
        DOUBLE = "𝄁"
        FINAL = "𝄂"

    class Coda:
        LEFT_REPEAT = "𝄆"
        RIGHT_REPEAT = "𝄇"
        DA_CAPO = "𝄊"
        CODA = "𝄌"
