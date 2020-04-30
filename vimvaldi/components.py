from typing import *
from dataclasses import dataclass

from enum import Enum, auto

from vimvaldi.commands import *


class Changeable:
    """A class representing something for which it makes sense to be marked changed."""

    changed = False  # set to True if something

    def has_changed(self) -> bool:
        """Return True if the changeable has changed."""
        return self.changed

    def set_changed(self, value: bool):
        """Set the state of this changeable."""
        self.changed = value


class Component(Changeable):
    """A class that is inherited by all of the components."""

    @abstractmethod
    def handle_keypress(self, key: int) -> Optional[Command]:
        """Handles a single keypress. Returns the resulting command."""
        pass

    @abstractmethod
    def handle_command(self, Command) -> Optional[Command]:
        """Handles the given command. Returns the resulting command."""
        pass


@dataclass
class MenuItem:
    """A class for representing an item of a menu."""

    label: str
    action: Command
    tooltip: str


class Menu:
    """A class for working with a menu."""

    def __init__(self, items: Sequence[Optional[MenuItem]]):
        self.index = 0
        self.items = items

    def __move_index(self, delta):
        """Moves the index of the menu by delta positions (ignoring Nulls)."""
        self.index = (self.index + delta) % len(self.items)

        # skip the spacers
        while self.items[self.index] is None:
            self.index = (self.index + (1 if delta > 0 else -1)) % len(self.items)

        # TODO add action to change the status line to the currently selected label

        self.set_changed(True)

    def next(self):
        """Point to the next item in the menu."""
        self.__move_index(1)

    def previous(self):
        """Point to the previous item in the menu."""
        self.__move_index(-1)

    def get_tooltip(self) -> str:
        """Return the tooltip associated with the currently selected menu item."""
        return self.items[self.index].tooltip

    def get_selected(self) -> MenuItem:
        """Return the currently selected MenuItem object."""
        return self.items[self.index]

    def handle_command(self, Command) -> Optional[Command]:
        pass

    def handle_keypress(self, key: int) -> Optional[Command]:
        if key == "j":
            self.next()

        elif key == "k":
            self.previous()

        elif key in (curses.KEY_ENTER, "\n", "\r", "l"):
            return self.items[self.index].action


class LogoDisplay(Component):
    """A very simple for displaying the logo."""

    def __init__(self, window, text: str):
        self.text = text

    def handle_keypress(self, key: int) -> Optional[Command]:
        """Go away from the logo when enter is pressed."""
        if key in (curses.KEY_ENTER, "\n", "\r"):
            return None  # TODO pop logo


class TextDisplay(Component):
    """A class for displaying scrollable text."""

    def __init__(self, text: str):
        self.text = text

        # the current offset of the text display (by lines)
        self.line_offset = 0

    def handle_keypress(self, key: int) -> Optional[Command]:
        if key in ("j", curses.KEY_ENTER, "\n", "\r"):
            self.line_offset += 1
            self.set_changed(True)

        elif key == "k":
            self.line_offset -= 1
            self.set_changed(True)

        elif key == "q":
            return None  # TODO quit


class StatusLine(Component):
    """A class for inputting/displaying information for the app."""

    class Position(Enum):
        LEFT = auto()
        CENTER = auto()
        RIGHT = auto()

    class State(Enum):
        NORMAL = auto()
        INSERT = auto()

    # the current state of the status line
    current_state = State.NORMAL

    def __init__(self, window):
        self.text = ["", "", ""]  # left, center, right text

        # current position of the cursor on the status line
        self.cursor_offset = 0

    def set_text(self, position: int, text: str):
        """Change text at the specified position (left/center/right)."""
        self.text[position] = text

    def clear(self):
        """Clear all text from the StatusLine."""
        self.text = ["", "", ""]

    def handle_keypress(self, key: int) -> Optional[Command]:
        # to simplify the code
        pos = self.cursor_offset

        # backspace: delete previous character
        if key in (curses.KEY_BACKSPACE, "\x7f"):
            # delete when it's not in the first position
            if pos > 0:
                self.text[0] = self.text[0][: pos - 1] + self.text[0][pos:]
                self.cursor_offset -= 1
            else:
                # if there is no text left, transfer focus
                if len(self.text[0]) == 0:
                    self.text[0] = ""
                    # TODO transfer focus

        # delete: delete next character
        elif key == curses.KEY_DC:
            self.text[0] = self.text[0][:pos] + self.text[0][pos + 1 :]

        # escape: clear and transfer focus
        elif type(key) is str and ord(key) == 27:  # esc
            self.clear()
            # TODO transfer focus

        # left: move cursor to the left
        elif key == curses.KEY_LEFT:  # move cursor left
            self.cursor_offset = max(1, pos - 1)

        # right: move cursor to the right
        elif key == curses.KEY_RIGHT:  # move cursor right
            self.cursor_offset = min(len(self.text[0]), pos + 1)

        # ctrl + right: move by words
        elif key == 553:
            space_pos = self.text[0].rfind(" ", 0, self.cursor_offset - 1)
            self.cursor_offset = space_pos + 1 if space_pos != -1 else 1

        # ctrl + left: move by words
        elif key == 568:  # ctrl + right
            space_pos = self.text[0].find(" ", self.cursor_offset + 1)
            self.cursor_offset = space_pos if space_pos != -1 else len(self.text[0])

        # home: move to position 0
        elif key == curses.KEY_HOME:
            self.cursor_offset = 0

        # end: move to the last position
        elif key == curses.KEY_END:
            self.cursor_offset = len(self.text[0])

        # execute the command on enter
        elif key in (curses.KEY_ENTER, "\n", "\r"):
            # TODO transfer focus
            # TODO parse commands

            text = self.text[0]

            self.set_focused(False)
            self.text[0] = ""

            # insert parsing
            if text[0] == ">":
                return ["insert", text[1:]]

            command = text[1:].split()

            # parsing of specific commands
            if command == ["q"]:
                return ["quit"]

            return command

        # else add the character to the first position
        self.text[0] = self.text[0][:pos] + str(key) + self.text[0][pos:]
        self.cursor_offset += len(str(key))
