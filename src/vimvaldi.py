# cleaner code!
from typing import *
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum

# terminal interaction
import curses

# utility functions
import util
import sys
import re


class Drawable(ABC):
    """A class to be extended by things that write on the courses windows."""

    def __init__(self, window):
        self.window = window
        self.changed = True

    def get_changed(self) -> bool:
        """Return True if the component needs to be redrawn."""
        return self.changed or self.window.is_wintouched()

    def set_changed(self, value):
        """Set, whether the component has changed since last redraw or not."""
        self.changed = value

    def refresh(self):
        """Is called to possibly redraw of this Drawable (if anything changed)."""
        if not self.get_changed():
            return

        self.window.erase()
        self.draw()

        self.set_changed(False)
        self.window.refresh()

    @abstractmethod
    def draw():
        """Does the actual drawing; is called after refresh() handles checking for 
        changes and erases the window."""
        pass

    @abstractmethod
    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        """Handles a single keypress. Possibly returns the command (list of params)."""
        pass


class Controllable(Drawable, ABC):
    """A class extending Drawable that uses StatusLine to execute commands. Is
    essentially the stuff you see in the main screen."""

    def __init__(self, window, status_line):
        super().__init__(window)

        self.status_line = status_line


@dataclass
class MenuItem:
    """A class for representing an item of a menu."""

    label: str
    action: List[str]
    tooltip: str


class Menu(Controllable):
    """A class for representing and working with a menu."""

    def __init__(self, window, status_line, items: Sequence[MenuItem]):
        super().__init__(window, status_line)

        self.index = 0
        self.items = items

        self.title = (
            " __  __                  \n"
            "|  \/  | ___ _ __  _   _ \n"
            "| |\/| |/ _ \ '_ \| | | |\n"
            "| |  | |  __/ | | | |_| |\n"
            "|_|  |_|\___|_| |_|\__,_|"
        ).split("\n")

    def __move_index(self, delta):
        """Moves the index of the menu by delta positions (ignoring spacers)."""
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

    def is_selected(self, item: MenuItem) -> bool:
        """Returns True if the specified item matches the currently selected one."""
        return self.items[self.index] is item

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        command = self.status_line.handle_keypress(key)

        if self.status_line.is_focused() or command != None:
            return command

        if key == "j":
            self.next()

        elif key == "k":
            self.previous()

        elif key in (curses.KEY_ENTER, "\n", "\r", "l"):
            return self.items[self.index].action

    def draw(self):
        height, width = self.window.getmaxyx()

        y_off = util.center_coordinate(height, len(self.title) + 1 + len(self.items))

        # draw the title of the menu
        for i, line in enumerate(self.title):
            x_off = util.center_coordinate(width, len(line))
            self.window.addstr(y_off + i, x_off, line)

        # draw the menu itself
        for i, item in enumerate(self.items):
            # ignore spacers
            if item is None:
                continue

            if self.is_selected(item):
                label = f"> {item.label} <"
            else:
                label = item.label

            x_off = util.center_coordinate(width, len(label))
            self.window.addstr(y_off + len(self.title) + 2 + i, x_off, label)

        # display the tooltip of the current item
        if not self.status_line.is_focused():
            self.status_line.set_text(self.status_line.CENTER, self.get_tooltip())
            self.status_line.set_changed(True)


class LogoDisplay(Controllable):
    """A very simple class for displaying the logo."""

    def __init__(self, window, status_line, text: Sequence[str]):
        super(LogoDisplay, self).__init__(window, status_line)

        self.text = text

    def draw(self):
        """Draws the centered program logo on the main window."""
        self.window.clear()

        height, width = self.window.getmaxyx()

        for y, line in enumerate(self.text):
            for x, char in enumerate(line):
                self.window.addstr(
                    y + (height - len(self.text)) // 2,
                    x + (width - len(line)) // 2,
                    char,
                    curses.color_pair(16 if char != "*" else 35),
                )

        self.status_line.clear()

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        if key in (curses.KEY_ENTER, "\n", "\r"):
            return ["change_state", "menu"]


class TextDisplay(Controllable):
    """A class for working with a (scrollable) text display."""

    def __init__(self, window, status_line, text: Sequence[str]):
        super(TextDisplay, self).__init__(window, status_line)

        self.text = text

        self.line_offset = 0
        self.side_offsets = [3, 1]  # left/right offset, top/bottom offset

    def __get_content_space(self) -> Tuple[int, int]:
        """Get the width and the height of the area that we can print on."""
        height, width = self.window.getmaxyx()
        return width - 2 * self.side_offsets[0], height - 2 * self.side_offsets[1]

    def draw(self):
        width, height = self.__get_content_space()

        # wrap the lines first (adding them to a list)
        wrapped: List[Tuple[str, indent_level]] = []
        for line in self.text:
            if line == "":
                wrapped.append(("", 0))

            # count the heading level (for coloring)
            heading_level = 0
            while heading_level < len(line) and line[heading_level] == "#":
                heading_level += 1

            while line != "":
                previous_space = -1  # the index of the last space seen
                i, char_count = 0, 0  # index in line + the number of actual chars

                # count the number of actual characters, until the width
                while i < len(line) and char_count < width:
                    if line[i] not in {"*", "/", "_"}:
                        if line[i] == " ":
                            previous_space = i

                        elif line[i] == "\\":
                            i += 1

                        char_count += 1
                    i += 1

                # if a space was found, wrap on it; else split on the word
                # TODO: possibly split on other non-alpha characters
                if previous_space != -1 and char_count == width:
                    i = previous_space

                wrapped.append((line[:i], heading_level))
                line = line[i:].strip()

        # restrict the offset to valid values
        self.line_offset = max(0, min(self.line_offset, len(wrapped) - height))

        # 'flags' for displaying characters
        flags = {
            "*": [False, curses.A_BOLD],
            "/": [False, curses.A_ITALIC],
            "_": [False, curses.A_UNDERLINE],
            "~": [False, 0],  # special case for underline
        }

        y = 0
        for line, h_level in wrapped[self.line_offset : height + self.line_offset]:
            x = 0

            j = 0
            while x + j < len(line):
                # possibly toggle flags
                if line[x + j] in flags:
                    flags[line[x + j]][0] = not flags[line[x + j]][0]
                    j += 1

                else:
                    if line[x + j] == "\\":
                        j += 1

                    # evaluate flags
                    evaluated_flags = 0
                    for flag in flags:
                        evaluated_flags |= 0 if not flags[flag][0] else flags[flag][1]

                    # special case for strikethrough, since it's unicode
                    char = (line[x + j] + "\u0336") if flags["~"][0] else line[x + j]

                    # place the char on the screen
                    self.window.addstr(
                        self.side_offsets[1] + y,
                        self.side_offsets[0] + x,
                        char,
                        evaluated_flags
                        | (curses.color_pair(h_level + 34) if h_level != 0 else 0),
                    )

                    x += 1

            h_level = 0
            y += 1

        self.status_line.clear()

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        command = self.status_line.handle_keypress(key)

        if self.status_line.is_focused() or command != None:
            return command

        if key in ("j", curses.KEY_ENTER, "\n", "\r"):
            self.line_offset += 1
            self.set_changed(True)

        if key == "k":
            self.line_offset -= 1
            self.set_changed(True)

        if key == "q":
            return ["quit"]

        height = self.__get_content_space()[1]

        if key == chr(4):  # ^D
            self.line_offset += height // 3
            self.set_changed(True)

        if key == chr(21):  # ^U
            self.line_offset -= height // 3
            self.set_changed(True)


class StatusLine(Drawable):
    """A class for displaying information about the state of the program/parsing the 
    commands specified by the user."""

    LEFT = 0
    CENTER = 1
    RIGHT = 2

    def __init__(self, window):
        super(StatusLine, self).__init__(window)

        self.text = ["", "", ""]  # left, center, right text

        self.focused = False
        self.cursor_position = 0

    def is_focused(self):
        """Returns True if the status line is currently focused."""
        return self.focused

    def set_focused(self, value: bool = True):
        """Sets the focus of the status line."""
        self.focused = value

        if self.is_focused():
            curses.curs_set(1)
            self.window.move(0, self.cursor_position)
        else:
            curses.curs_set(0)
            self.cursor_position = 0

    def set_text(self, position: int, text: str):
        """Change text at the specified position (left/center/right)."""
        self.text[position] = text
        self.set_changed(True)

    def clear(self):
        """Clear all text from the StatusLine."""
        self.text = ["", "", ""]
        self.set_changed(True)

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        if not self.is_focused():
            if key == ":":
                self.set_focused(True)
            else:
                return

        self.set_changed(True)

        c_pos = self.cursor_position

        if key in (curses.KEY_BACKSPACE, "\x7f"):  # backspace
            if c_pos > 1:
                self.text[0] = self.text[0][: c_pos - 1] + self.text[0][c_pos:]
                self.cursor_position -= 1
            else:
                if len(self.text[0]) == 1:
                    self.text[0] = ""
                    self.set_focused(False)

        elif key == curses.KEY_DC:  # del
            self.text[0] = self.text[0][:c_pos] + self.text[0][c_pos + 1 :]

        elif key == 27:  # esc
            self.text[0] = ""
            self.set_focused(False)

        elif key == curses.KEY_LEFT:  # move cursor left
            self.cursor_position = max(1, c_pos - 1)

        elif key == curses.KEY_RIGHT:  # move cursor right
            self.cursor_position = min(len(self.text[0]), c_pos + 1)

        elif key == 553:  # ctrl + left
            space_pos = self.text[0].rfind(" ", 0, self.cursor_position - 1)
            self.cursor_position = space_pos + 1 if space_pos != -1 else 1

        elif key == 568:  # ctrl + right
            space_pos = self.text[0].find(" ", self.cursor_position + 1)
            self.cursor_position = space_pos if space_pos != -1 else len(self.text[0])

        elif key == curses.KEY_HOME:  # home
            self.cursor_position = 1

        elif key == curses.KEY_END:  # end
            self.cursor_position = len(self.text[0])

        elif key in (curses.KEY_ENTER, "\n", "\r"):  # enter
            command = self.text[0][1:].split()

            # parsing of specific commands
            if command == ["q"]:
                return ["quit"]

            self.set_focused(False)
            self.text[0] = ""

            return command

        else:  # add the char to the command string
            self.text[0] = self.text[0][:c_pos] + str(key) + self.text[0][c_pos:]
            self.cursor_position += 1

    def draw(self):
        _, width = self.window.getmaxyx()

        left_offset = 0
        center_offset = util.center_coordinate(width, len(self.text[1]))
        right_offset = width - len(self.text[2]) - 1

        # if the status line is focused, only draw the left line
        self.window.addstr(0, left_offset, self.text[0])
        if not self.is_focused():
            self.window.addstr(0, center_offset, self.text[1])
            self.window.addstr(0, right_offset, self.text[2])

        self.window.move(0, self.cursor_position)


class Interface:
    """A high-level class for rendering the Vimvaldi user interface."""

    def __init__(self, window):
        # window setup
        self.window = window

        height, width = self.window.getmaxyx()
        self.main_window = self.window.derwin(height - 1, width, 0, 0)
        self.status_window = self.window.derwin(1, width, height - 1, 0)

        curses.curs_set(0)

        self.initialize_colors()

        # COMPONENT INITIALIZATION
        self.status_line = StatusLine(self.status_window)

        self.components = {
            "logo": LogoDisplay(
                self.main_window,
                self.status_line,
                (
                    "     ________  **    ________               \n"
                    "    /        \****  /        \              \n"
                    "    \        /******\        /              \n"
                    "     |      |********/      /'              \n"
                    "     |      |******/      /'                \n"
                    "    *|      |****/      /'                  \n"
                    "  ***|      |**/      /'****                \n"
                    "*****|      |/      /'********              \n"
                    "  ***|            /'*********               \n"
                    "    *|      _   /'*********       _     _ _ \n"
                    "     |     (_)/'__ _____   ____ _| | __| (_)\n"
                    "     |     | | '_ V _ \ \ / / _` | |/ _` | |\n"
                    "     |    /| | | | | | \ V / (_| | | (_| | |\n"
                    "     |__/' |_|_| |_| |_|\_/ \__._|_|\__,_|_|"
                ).split("\n"),
            ),
            "info": TextDisplay(
                self.main_window,
                self.status_line,
                [
                    r"# Info",
                    r"The following page contains relevant information about the app.",
                    r"",
                    r"## History",
                    r"This project was created as a semester project for the AP Programming Course at the Charles University (/http:\/\/mj.ucw.cz\/vyuka\/1920\/p1x\//).",
                    r"",
                    r"## Source Code",
                    r"The code is licensed under MIT and freely available from /https:\/\/github.com\/xiaoxiae\/Vimvaldi\//, so feel free do whatever you want with it :-). Also feel free to submit a pull request if there's something you'd like to see changed or implemented!",
                ],
            ),
            "help": TextDisplay(
                self.main_window,
                self.status_line,
                [
                    r"# Help",
                    r"The following page contains instructions on using the app.",
                    r"",
                    r"## General commands (can be run from anywhere within the app)",
                    r"_:help_       -- displays this page",
                    r"_:info_       -- displays the info page",
                    r"_:q_ or _:quit_ -- terminates the app",
                ],
            ),
            "menu": Menu(
                self.main_window,
                self.status_line,
                [
                    MenuItem("CREATE", [], "Creates a new score."),
                    MenuItem("IMPORT", [], "Imports a score from a file."),
                    None,
                    MenuItem(
                        "HELP",
                        ["append_state", "help"],
                        "Displays program documentation.",
                    ),
                    MenuItem(
                        "INFO",
                        ["append_state", "info"],
                        "Shows information about the program.",
                    ),
                    None,
                    MenuItem("QUIT", ["quit"], "Terminates the program."),
                ],
            ),
        }

        # a stack with main window components, with the top one being the one currently
        # being displayed; we start with the logo
        self.state_stack: List[Component] = [self.components["logo"]]

        # run the program
        self.run()

    def run(self):
        """The main loop of the program."""
        k = None
        while True:
            # handle window resize event
            if k == curses.KEY_RESIZE:
                self.resize_windows()

            command = self.state_stack[-1].handle_keypress(k)

            # handle commands sent by the components
            if command != None:
                if len(command) == 1:
                    # quit command
                    if command[0] == "quit":
                        self.state_stack.pop()

                        # when there's nothing to control, exit...
                        if len(self.state_stack) == 0:
                            sys.exit()

                    # switch to help and info (if they aren't already in the stack)
                    elif command[0] in ("help", "info"):
                        # there can be only one text display in the stack at any time
                        i = 0
                        while i < len(self.state_stack):
                            if type(self.state_stack[i]) is TextDisplay:
                                self.state_stack.pop(i)
                            i += 1

                        self.state_stack.append(self.components[command[0]])

                elif len(command) == 2:
                    # changing the state of the app
                    if command[0] == "change_state":
                        self.state_stack[-1] = self.components[command[1]]

                    # adding another state of the app
                    elif command[0] == "append_state":
                        self.state_stack.append(self.components[command[1]])

                self.state_stack[-1].set_changed(True)

            # redraw the component and the status line
            # check for errors when drawing, possibly displaying the error message
            try:
                self.state_stack[-1].refresh()
                self.status_line.refresh()
            except curses.error:
                height, width = self.window.getmaxyx()

                error_text = "Terminal size too small!"[: width - 1]

                self.window.clear()
                self.window.addstr(
                    height // 2,
                    util.center_coordinate(width, len(error_text)),
                    error_text,
                )

            k = self.window.get_wch()

    def initialize_colors(self):
        """Initializes the colors used throughout the program 
        (see https://jonasjacek.github.io/colors/)."""

        curses.start_color()
        curses.use_default_colors()

        for i in range(curses.COLORS):
            curses.init_pair(i + 1, i, -1)

    def resize_windows(self):
        """Resize the windows of the interface."""
        height, width = self.window.getmaxyx()

        # Please, don't ask me why this is necessary. There seems to be an issue with
        # simply moving the status window using mvin, but this seems to fix it (remove
        # one of the lines and try for yourself by resizing the terminal).
        self.status_window.mvderwin(height - 1, 0)
        self.status_window.mvwin(height - 1, 0)

        self.main_window.resize(height - 1, width)


if __name__ == "__main__":
    curses.wrapper(Interface)
