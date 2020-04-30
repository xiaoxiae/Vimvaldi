"""The initial class that gets called when the program is launched."""

from typing import *
from dataclasses import dataclass

from abc import ABC, abstractmethod

import curses
import sys
import re

from vimvaldi.utilities import *
from vimvaldi.music import *


class Drawable(ABC, Changeable):
    """A class to be extended by things that write on the courses windows."""

    focused = False  # whether this drawable is currently focused

    def __init__(self, window):
        self.window = window

    def focus(self):
        """Set the focus on this Drawable."""
        self.focused = True

    def is_focused(self):
        """Return True if this Drawable is currently focused."""
        return self.focused

    def move_cursor(self, position: Tuple[int, int]):
        """A function for setting the cursor position. Called after the components are
        drawn, since drawing them moves the cursor. Only does something if the drawable
        is focused."""
        if self.focused:
            if self.cursor_position is not None:
                curses.curs_set(1)
                self.window.move(*self.cursor_position)
            else:
                curses.curs_set(0)

    def width(self):
        """Return the width of the window."""
        return self.window.getmaxyx()[1]

    def height(self):
        """Return the height of the window."""
        return self.window.getmaxyx()[0]

    @abstractmethod
    def __draw(self):
        """The internal implementation that draws on the actual window and has to be
        implemented by classes that inherit this class."""
        pass

    def draw(self):
        """The function that draws the Drawable (if anything changed). Checks, whether
        the drawable has changed; if it does, clears the window and calls __draw()."""
        if self.has_changed():
            self.window.clear()
            self.__draw()


class DrawableMenu(Drawable, Menu):
    def __init__(self, window, title: str, items: Sequence[Optional[MenuItem]]):
        Drawable.__init__(self, window)
        Menu.__init__(self, items)

        self.title = title

    def __draw(self):
        # the y offset from the top of the window to where to start drawing
        y_off = center_coordinate(self.height(), len(self.title) + 1 + len(self.items))

        # draw the title of the menu, line by line
        for i, line in enumerate(self.title):
            x_off = center_coordinate(self.width(), len(line))
            self.window.addstr(y_off + i, x_off, line)

        # draw the menu itself
        for i, item in enumerate(self.items):
            # ignore spacers
            if item is None:
                continue

            # mark the selected label
            if self.get_selected() is item:
                text = f"> {item.label} <"
            else:
                text = item.label

            x_off = center_coordinate(self.width(), len(text))
            self.window.addstr(y_off + len(self.title) + 2 + i, x_off, text)


class DrawableLogoDisplay(Drawable, LogoDisplay):
    def __init__(self, window, text: str):
        Drawable.__init__(self, window)
        LogoDisplay.__init__(self, text)

    def __draw(self):
        """Draws the centered program logo on the window."""
        for y, line in enumerate(self.text.splitlines()):
            for x, char in enumerate(line):
                self.window.addstr(
                    y + (self.height() - len(self.text)) // 2,
                    x + (self.width() - len(line)) // 2,
                    char,
                    curses.color_pair(16 if char != "*" else 35),
                )


class DrawableTextDisplay(Controllable):
    def __init__(self, window, text: str):
        Drawable.__init__(self, window)
        TextDisplay.__init__(self, text)

        self.text = text

        self.side_offsets = [3, 1]  # left/right offset, top/bottom offset when drawing

    def __get_content_space(self) -> Tuple[int, int]:
        """Get the width and the height of the area that we can put text on."""
        return (
            self.width() - 2 * self.side_offsets[0],
            self.height() - 2 * self.side_offsets[1],
        )

    def __draw(self):
        # get the free space that we can draw on
        width, height = self.__get_content_space()

        # wrap the lines first (adding them to a list)
        wrapped: List[Tuple[str, indent_level]] = []
        for line in self.text.splitlines():
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

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        command = self.status_line.handle_keypress(key)

        if self.status_line.is_focused() or command != None:
            return command

        if key in ("j", curses.KEY_ENTER, "\n", "\r"):
            self.line_offset += 1
            self.window.noutrefresh()

        if key == "k":
            self.line_offset -= 1
            self.window.noutrefresh()

        if key == "q":
            return ["quit"]

        # TODO drawable text display
        height = self.__get_content_space()[1]

        if key == chr(4):  # ^D
            self.line_offset += height // 3
            self.window.noutrefresh()

        if key == chr(21):  # ^U
            self.line_offset -= height // 3
            self.window.noutrefresh()


class Editor(Controllable):
    """A class for working with the notes. This is the main class of the program."""

    def __init__(self, window, status_line):
        super(Editor, self).__init__(window, status_line)
        self.score = Score()

        self.side_offsets = [5, 1]  # left/right offset, top/bottom offset

        self.key_stack = []

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        # special handling for insert commands
        if key == "i" and not self.status_line.is_focused():
            key = "INSERT"

        command = self.status_line.handle_keypress(key)

        if command is None:
            if not self.status_line.is_focused():
                if len(self.key_stack) == 0:
                    if key == "l":
                        self.score.next()

                    elif key == "h":
                        self.score.previous()

                    elif key == "g":
                        self.key_stack.append("g")

                    elif key == "G":
                        self.score.last()

                    elif key == "x":
                        if not self.score.remove():
                            self.status_line.set_text(
                                self.status_line.CENTER, "Not allowed!"
                            )
                    else:
                        self.key_stack = []
                else:
                    if key == "g" and self.key_stack[-1] == "g":
                        self.score.first()

                    self.key_stack.pop()
        else:
            if len(command) > 0 and command[0] == "insert":
                if not self.score.insert(command[1]):
                    self.status_line.set_text(
                        self.status_line.CENTER, "Incorrect identifier!"
                    )

        return command

    def draw(self):
        height, width = self.window.getmaxyx()

        lines = 5  # number of lines in a note sheet

        heading = (
            " _____    _   _            \n"
            "| ____|__| |_| |_ ___  _ _ \n"
            "|  _| / _` (_) __/ _ \| '_|\n"
            "| |__| (_| | | || (_) | |  \n"
            "|_____\__,_|_|\__\___/|_|  \n"
            "                           \n\n\n"
        ).split("\n")

        center = center_coordinate(height, lines + len(heading))

        # draw the title of the menu
        for i, line in enumerate(heading):
            x_off = center_coordinate(width, len(line))
            self.window.addstr(center + i, x_off, line)

        # draw the 5 lines of a note sheet
        for x in range(self.side_offsets[0], width - self.side_offsets[0]):
            for y in range(center, center + lines):
                self.window.addstr(y + len(heading), x, " ", curses.A_UNDERLINE)

        # draw the key
        self.window.addstr(
            center + len(heading) + lines // 2,
            self.side_offsets[0] + 2,
            self.score.clef,
            curses.A_UNDERLINE,
        )

        # draw the time
        for i, component in enumerate(self.score.time.split("/")):
            self.window.addstr(
                center + len(heading) + lines // 2 + i,
                self.side_offsets[0] + 4,
                component,
                curses.A_UNDERLINE,
            )

        # draw the vertical bar after time
        draw_vertical_bar(
            self.window,
            self.side_offsets[0] + 6,
            center + 1 + len(heading),
            center + lines + len(heading),
        )

        # draw the notes/rests/whatever
        x = 8  # position from left offset
        i = 0  # position in the score
        duration = 0.0  # the accumulate duration of notes
        cursor_position = None

        while i < len(self.score):
            item = self.score[i]

            # don't draw outside screen
            if x + 2 * self.side_offsets[0] > width:
                break

            # if the duration accumulated to 1, draw a vertical bar
            # and reset the duration
            if duration == 1:
                duration = 0

                draw_vertical_bar(
                    self.window,
                    self.side_offsets[0] + x,
                    center + 1 + len(heading),
                    center + lines + len(heading),
                )

                x += 2
                continue

            # draw rests
            if type(item) is Rest:
                self.window.addstr(
                    center + len(heading) + lines // 2,
                    self.side_offsets[0] + x,
                    str(item),
                    curses.A_UNDERLINE,
                )

            # draw notes
            elif type(item) is Note:
                # the position of C4
                offset = ord(item.pitch[0]) - 99 + (item.pitch[1] - 4) * 8

                l = offset // 2
                m = offset % 2

                note = str(item)
                if m == 1:
                    note += "*"

                self.window.addstr(
                    center + len(heading) + lines // 2 - l,
                    self.side_offsets[0] + x,
                    note,
                    curses.A_UNDERLINE,
                )

            # possibly move the cursor accordingly
            if i == self.score.position:
                x_offset = 0 if type(item) is not None else m
                y_offset = 0 if type(item) is not None else l

                cursor_position = (
                    center + len(heading) + lines // 2 - y_offset,
                    self.side_offsets[0] + x + x_offset,
                )

            ## check for a dot
            # if item.dotted:
            #    x += 1

            #    self.window.addstr(
            #        center + len(heading) + lines // 2,
            #        self.side_offsets[0] + x,
            #        ".",  # TODO: replace with a better dot
            #        curses.A_UNDERLINE,
            #    )

            # the duration of notes is 1 = whole, 2 = half...
            duration += 1 / item.duration
            x += 2
            i += 1

        self.status_line.set_text(self.status_line.RIGHT, "".join(self.key_stack))

        # update cursor position
        if cursor_position is not None:
            self.cursor_position = cursor_position
        else:
            self.cursor_position = (
                center + len(heading) + lines // 2,
                self.side_offsets[0] + x,
            )


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
        self.cursor_offset = 0

    def is_focused(self):
        """Returns True if the status line is currently focused."""
        return self.focused

    def set_focused(self, value: bool = True):
        """Sets the focus of the status line."""
        self.focused = value

        # get rid of cursor control when the status line is no longer in focus
        if not self.focused:
            self.cursor_position = None

    def set_text(self, position: int, text: str):
        """Change text at the specified position (left/center/right)."""
        self.text[position] = text

    def clear(self):
        """Clear all text from the StatusLine."""
        self.text = ["", "", ""]

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        if not self.is_focused():
            if key == ":":
                self.set_focused(True)
                self.cursor_offset = 0
            elif key == "INSERT":  # special command
                self.set_focused(True)
                self.cursor_offset = 0

                key = ">"
            else:
                return

        c_pos = self.cursor_offset

        if key in (curses.KEY_BACKSPACE, "\x7f"):
            if c_pos > 1:
                self.text[0] = self.text[0][: c_pos - 1] + self.text[0][c_pos:]
                self.cursor_offset -= 1
            else:
                if len(self.text[0]) == 1:
                    self.text[0] = ""
                    self.set_focused(False)

        elif key == curses.KEY_DC:  # del
            self.text[0] = self.text[0][:c_pos] + self.text[0][c_pos + 1 :]

        elif type(key) is str and ord(key) == 27:  # esc
            self.text[0] = ""
            self.set_focused(False)

        elif key == curses.KEY_LEFT:  # move cursor left
            self.cursor_offset = max(1, c_pos - 1)

        elif key == curses.KEY_RIGHT:  # move cursor right
            self.cursor_offset = min(len(self.text[0]), c_pos + 1)

        elif key == 553:  # ctrl + left
            space_pos = self.text[0].rfind(" ", 0, self.cursor_offset - 1)
            self.cursor_offset = space_pos + 1 if space_pos != -1 else 1

        elif key == 568:  # ctrl + right
            space_pos = self.text[0].find(" ", self.cursor_offset + 1)
            self.cursor_offset = space_pos if space_pos != -1 else len(self.text[0])

        elif key == curses.KEY_HOME:  # home
            self.cursor_offset = 1

        elif key == curses.KEY_END:  # end
            self.cursor_offset = len(self.text[0])

        elif key in (curses.KEY_ENTER, "\n", "\r"):  # enter

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

        elif len(str(key)) == 1:  # add the char to the command string
            self.text[0] = self.text[0][:c_pos] + str(key) + self.text[0][c_pos:]
            self.cursor_offset += 1

    def draw(self):
        _, width = self.window.getmaxyx()

        left_offset = 0
        center_offset = center_coordinate(width, len(self.text[1]))
        right_offset = width - len(self.text[2]) - 1

        # if the status line is focused, only draw the left line (i.e. the command)
        self.window.addstr(0, left_offset, self.text[0])
        if not self.is_focused():
            self.window.addstr(0, center_offset, self.text[1])
            self.window.addstr(0, right_offset, self.text[2])

        self.cursor_position = (0, self.cursor_offset) if self.is_focused() else None


class Interface:
    """A high-level class for rendering the Vimvaldi user interface."""

    def __init__(self, window):
        # window setup
        self.window = window

        # derive two windows from the current one -- the main one and the status one
        height, width = self.window.getmaxyx()
        self.main_window = self.window.derwin(height - 1, width, 0, 0)
        self.status_window = self.window.derwin(1, width, height - 1, 0)

        # initialize the terminal colors
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
                ),
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
                    MenuItem("CREATE", ["new"], "Creates a new score."),
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
            "editor": Editor(self.main_window, self.status_line),
        }

        # a stack with main window components, with the top one being the one currently
        # being displayed; we start with the logo
        self.state_stack: List[Component] = [self.components["logo"]]

        # run the program (permanent loop)
        self.loop()

    def loop(self):
        """The main loop of the program."""
        k = None
        while True:
            # special window resize event handling
            if k == curses.KEY_RESIZE:
                self.resize_windows()

            # redraw the component and the status line
            # check for errors when drawing, possibly displaying an error message
            try:
                # refresh the virtual component screen
                self.state_stack[-1].refresh()
                self.status_line.refresh()

                # positions of the cursor
                main_cp = self.state_stack[-1].cursor_position
                status_cp = self.status_line.cursor_position

                self.state_stack[-1].window.refresh()
                self.status_line.window.refresh()

            except curses.error:
                # TODO better error handling
                height, width = self.window.getmaxyx()

                error_text = "Terminal size too small!"[: width - 1]

                self.window.clear()
                self.window.addstr(
                    height // 2, center_coordinate(width, len(error_text)), error_text,
                )

            # wait for the next character
            k = self.window.get_wch()

    def initialize_colors(self):
        """Initializes the colors used throughout the program."""
        curses.start_color()
        curses.use_default_colors()

        for i in range(curses.COLORS):
            curses.init_pair(i + 1, i, -1)

    def resize_windows(self):
        """Resize the windows of the interface."""
        height, width = self.window.getmaxyx()

        # TODO is this necessary?
        self.status_window.mvderwin(height - 1, 0)
        self.status_window.mvwin(height - 1, 0)

        self.main_window.resize(height - 1, width)


def run():
    """An entry point to the progam."""
    curses.wrapper(Interface)


if __name__ == "__main__":
    run()
