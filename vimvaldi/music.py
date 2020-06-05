"""A module for storing musical-related classes."""


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

    class Rest:
        WHOLE = "𝄻"
        HALF = "𝄼"
        QUARTER = "𝄽"
        EIGHT = "𝄾"
        SIXTEENTH = "𝄿"
        THIRTY_SECOND = "𝅀"
        SIXTY_FOURTH = "𝅁"

    class Bar:
        SINGLE = "𝄀"
        DOUBLE = "𝄁"
        FINAL = "𝄂"

    class Coda:
        LEFT_REPEAT = "𝄆"
        RIGHT_REPEAT = "𝄇"
        DA_CAPO = "𝄊"
        CODA = "𝄌"
