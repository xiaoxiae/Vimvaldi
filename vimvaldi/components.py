"""The module containing all of the components logic."""

from __future__ import annotations

import curses
import logging  # DEBUG; TO BE REMOVED
import os
import sys
from abc import ABC, abstractmethod
from typing import *
from signal import signal, SIGINT

import abjad

from vimvaldi.commands import *


# TODO remove -- just for debug
logging.basicConfig(filename="vimvaldi.log", level=logging.DEBUG)
print = logging.info

# catch SIGINT and prevent it from terminating the script
signal(SIGINT, lambda _, __: None)


class Changeable:
    """A class representing something for which it makes sense to be marked changed."""

    changed = True

    def has_changed(self) -> bool:
        """Return True if the changeable has changed."""
        return self.changed

    def set_changed(self, value: bool):
        """Set the state of this changeable."""
        self.changed = value


class Component(ABC, Changeable):
    """A class that is inherited by all of the components."""

    @abstractmethod
    def handle_keypress(self, key: str) -> List[Command]:
        """Handles a single keypress. Returns the resulting command."""
        pass

    @abstractmethod
    def handle_command(self, command) -> List[Command]:
        """Handles the given command. Returns the resulting command."""
        pass


@dataclass
class MenuItem:
    """A class for representing an item of a menu."""

    label: str
    commands: List[Command]
    tooltip: str


class Menu(Component):
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

    def update_status_line(self) -> List[Command]:
        """Return the command necessary for the status line to change label."""
        return [
            ClearStatusLineCommand(),
            SetStatusLineTextCommand(self.get_selected().tooltip, Position.CENTER),
        ]

    def handle_command(self, command) -> List[Command]:
        """React to Quit command by quitting."""
        if isinstance(command, QuitCommand):
            return [PopComponentCommand()]
        return []

    def handle_keypress(self, key: str) -> List[Command]:
        if key == "j":
            self.next()
            return self.update_status_line()

        elif key == "k":
            self.previous()
            return self.update_status_line()

        elif key in (curses.KEY_ENTER, "\n", "\r", "l"):
            return self.get_selected().commands

        elif key == ":":
            return [
                ToggleFocusCommand(),
                SetStatusLineStateCommand(State.NORMAL),
            ]

        return []


class LogoDisplay(Component):
    """A very simple for displaying the logo."""

    def __init__(self, text: str):
        self.text = text

    def handle_keypress(self, key: str) -> List[Command]:
        """Go away from the logo when enter is pressed."""
        if key in (curses.KEY_ENTER, "\n", "\r"):
            return [PopComponentCommand()]

        return []

    def handle_command(self, command) -> List[Command]:
        """React to Quit command by quitting."""
        if isinstance(command, QuitCommand):
            return [PopComponentCommand()]
        return []


class TextDisplay(Component):
    """A class for displaying scrollable text."""

    def __init__(self, text: str):
        self.text = text

        # the current offset of the text display (by lines)
        self.line_offset = 0

    def handle_command(self, command) -> List[Command]:
        """React to Quit command by quitting."""
        if isinstance(command, QuitCommand):
            return [PopComponentCommand()]
        return []

    def handle_keypress(self, key: str) -> List[Command]:
        if key in ("j", curses.KEY_ENTER, "\n", "\r"):
            self.line_offset += 1
            self.set_changed(True)

        elif key == "k":
            self.line_offset -= 1
            self.set_changed(True)

        elif key == "q":
            return [PopComponentCommand()]

        return []


class StatusLine(Component):
    """A class for inputting/displaying information for the app."""

    # the current state of the status line
    current_state = State.NORMAL

    def __init__(self):
        self.text = ["", "", ""]  # left, center, right text

        # current position of the cursor on the status line
        self.cursor_offset = 0

    def set_text(self, position: Position, text: str):
        """Change text at the specified position (left/center/right). Also, if the
        position is left, move the cursor to the very end (done when adding a partial
        command, for example)."""
        self.text[position.value] = text
        self.set_changed(True)

        if position == Position.LEFT:
            self.cursor_offset = len(self.text[position.value])

    def clear_text(self, position: Position):
        self.text[position.value] = ""

        if position.value == 0:
            self.cursor_offset = 0

        self.set_changed(True)

    def clear(self):
        """Clear all text from the StatusLine."""
        for pos in Position:
            self.clear_text(pos)

    def handle_command(self, command) -> List[Command]:
        if isinstance(command, SetStatusLineTextCommand):
            self.set_text(command.position, command.text)
        elif isinstance(command, ClearStatusLineCommand):
            self.clear()
        elif isinstance(command, SetStatusLineStateCommand):
            self.current_state = command.state

        return []

    def handle_keypress(self, key: str) -> List[Command]:
        self.set_changed(True)

        # to simplify the code
        pos = self.cursor_offset

        # backspace: delete previous character
        if key in (curses.KEY_BACKSPACE, "\b", chr(127)):
            # delete when it's not in the first position
            if pos > 0:
                self.text[0] = self.text[0][: pos - 1] + self.text[0][pos:]
                self.cursor_offset -= 1

            # if there is no text left, transfer focus
            else:
                if len(self.text[0]) == 0:
                    self.clear_text(Position.LEFT)
                    return [ToggleFocusCommand()]

        # delete: delete next character
        elif key == curses.KEY_DC:
            self.text[0] = self.text[0][:pos] + self.text[0][pos + 1 :]

        # escape: clear and transfer focus
        elif type(key) is str and ord(key) == 27:  # esc
            self.clear()
            return [ToggleFocusCommand()]

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
            # always toggle focus
            commands = [ToggleFocusCommand()]

            # get and clear the text
            text = self.text[0]
            self.clear_text(Position.LEFT)

            # send an insert command if the mode is insert
            if self.current_state is State.INSERT:
                commands.append(InsertCommand(text))

            # else parse the various : commands
            elif self.current_state is State.NORMAL:
                command = text.strip()
                command_parts = command.split()

                edit_commands = []

                # help and info screens from anywhere
                if command in ("help", "info"):
                    commands.append(PushComponentCommand(command))

                if len(command_parts) != 0:
                    if command in ("q", "quit"):
                        commands += [QuitCommand()]

                    if command in ("q!", "quit!"):
                        commands += [QuitCommand(forced=True)]

                    # whatever is left after anything after w is stripped
                    possible_path = command[len(command_parts[0]) :].strip()

                    if command_parts[0] in ("w", "write"):
                        commands += [SaveCommand(path=possible_path)]

                    if command_parts[0] in ("w!", "write!"):
                        commands += [SaveCommand(forced=True, path=possible_path)]

                    if command_parts[0] in ("o", "open"):
                        commands += [OpenCommand(path=possible_path)]

                    if command_parts[0] in ("o!", "open!"):
                        commands += [OpenCommand(forced=True, path=possible_path)]

                    if command_parts[0] == "wq":
                        commands += [SaveCommand(path=possible_path), QuitCommand()]

                    if command_parts[0] == "wq!":
                        commands += [
                            SaveCommand(forced=True, path=possible_path),
                            QuitCommand(),
                        ]

            return commands

        else:
            # else add the character to the first position
            self.text[0] = self.text[0][:pos] + str(key) + self.text[0][pos:]
            self.cursor_offset += len(str(key))

        return []


class Editor(Component):
    """A class for working with the notesheet."""

    def __init__(self):
        # internal note representation (with some defaults)
        self.score = abjad.Score(simultaneous=False)

        self.key = abjad.KeySignature("c", "major")
        self.clef = abjad.Clef("treble")
        self.time = abjad.TimeSignature((4, 4))

        self.position = 0  # position within the container

        self.save_file = None  # the file to which to save
        self.changed_since_saving = False

    def get_score(self) -> abjad.Container:
        """Return the abjad container that stores the notes."""
        return self.score

    def handle_keypress(self, key: str) -> List[Command]:
        if key == ":":
            return [
                ToggleFocusCommand(),
                SetStatusLineStateCommand(State.NORMAL),
            ]
        elif key == "i":
            return [
                ToggleFocusCommand(),
                SetStatusLineStateCommand(State.INSERT),
            ]

        return []

    def __valid_save_path(self, path: str) -> List[Command]:
        """Checks, whether we can save to this path -- if it either doesn't exist or
        it matches the self.save_file path. Returns the appropriate commands if it
        doesn't."""
        if os.path.isfile(path) and path != self.save_file:
            return [
                SetStatusLineTextCommand("The file already exists.", Position.CENTER)
            ]

        return []

    def handle_command(self, command) -> List[Command]:
        # attempt to parse the insert command
        if isinstance(command, InsertCommand):
            text = command.text

            if len(text) == 0:
                return []

            try:
                if text[0] == "r":
                    obj = abjad.Rest(text)
                elif text[0] == "<":
                    obj = abjad.Chord(text)
                else:
                    obj = abjad.Note(text)

                self.score.insert(self.position, obj)
                self.position += 1
                self.changed_since_saving = True

            except Exception as e:
                return [
                    SetStatusLineTextCommand(
                        "The string could not be parsed.", Position.CENTER,
                    )
                ]

        elif isinstance(command, SaveCommand):
            path = command.path  # the path to save file to
            previous_save_file = self.save_file

            commands = []

            if path is None or len(path) == 0:
                if self.save_file is None:
                    return [SetStatusLineTextCommand("No file name.", Position.CENTER,)]
                else:
                    path = self.save_file

                    file_status = self.__valid_save_path(path)
                    if len(file_status) != 0 and not command.forced:
                        return file_status
            else:
                file_status = self.__valid_save_path(path)
                if len(file_status) != 0 and not command.forced:
                    return file_status

                self.save_file = path
                commands += self.get_file_name_commands()

            try:
                with open(self.save_file, "w") as f:
                    sys.stdout = f
                    abjad.f(self.score)
                    self.changed_since_saving = False

            except Exception as e:
                # restore the previous file name if something went amiss
                self.save_file = previous_save_file

                # TODO: BETTER EXCEPTIONS
                return commands + [
                    SetStatusLineTextCommand("Error writing file.", Position.CENTER,)
                ]

            return commands + [SetStatusLineTextCommand("Saved.", Position.CENTER,)]

        elif isinstance(command, QuitCommand):
            # if we haven't done anything, simply pop the editor
            if not self.changed_since_saving:
                return [PopComponentCommand()]

            # else warn that we can't just pop the editor
            else:
                if command.forced:
                    return [PopComponentCommand()]
                else:
                    return [
                        SetStatusLineTextCommand(
                            "Unsaved changes. Save with :w or use :q!.",
                            Position.CENTER,
                        )
                    ]

        return []

    def get_file_name_commands(self) -> List[Command]:
        """Return the appropriate command for changing the label of the status line."""
        if self.save_file is None:
            return [SetStatusLineTextCommand("[no file]", Position.RIGHT,)]
        else:
            return [SetStatusLineTextCommand(f"[{self.save_file}]", Position.RIGHT,)]
