from typing import List


class Notation:
    """A class for storing musical notation symbols used in the program."""

    class Clef:
        TREBLE = "𝄞"
        ALTO = "𝄡"
        BASS = "𝄢"

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
