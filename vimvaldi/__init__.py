"""The initial module that gets called when the program is launched."""


from typing import *
from dataclasses import dataclass

from abc import ABC, abstractmethod

import sys
import re

import curses
from vimvaldi.utilities import *
from vimvaldi.components import *

# DEBUG; TO BE REMOVED
import logging

logging.basicConfig(filename="vimvaldi.log", level=logging.DEBUG)
print = logging.info


@dataclass
class View:
    x: int
    y: int
    width: int
    height: int


class WindowView:
    """A Curses window wrapper to only paint on a part of it because either I'm stupid
    or Curses is a broken mess and Windows don't work as they should."""

    def __init__(self, parent, view: View = View(-1, -1, -1, -1)):
        # the parent window
        self.parent = parent

        # the restricted view of the parent window
        # it's x, y, width, height
        self.view = view

    def resize(self, view: View):
        """Resize view to the given size."""
        self.view = view

    def width(self) -> int:
        """Return the width of the window."""
        return self.view.width

    def height(self) -> int:
        """Return the height of the window."""
        return self.view.height

    def clear(self, *args, **kwargs):
        # TODO delete only the rectangle -- this deletes whole lines
        for y in range(self.view.height):
            self.parent.move(y + self.view.y, 0)
            self.parent.clrtoeol()

    def addstr(self, x: int, y: int, string: str, *args, **kwargs):
        # TODO check bounds
        self.parent.addstr(y + self.view.y, x + self.view.x, string, *args, **kwargs)


class Drawable(ABC, Changeable):
    """A class to be extended by things that write on the curses windows."""

    focused = False  # whether this drawable is currently focused
    cursor_position = None

    def __init__(self, window: WindowView):
        self.window = window

    def set_focused(self, value: bool):
        """Set the focus on this Drawable."""
        self.focused = value

    def is_focused(self) -> bool:
        """Return True if this Drawable is currently focused."""
        return self.focused

    @abstractmethod
    def _draw(self):
        """The internal implementation that draws on the actual window and has to be
        implemented by classes that inherit this class."""
        pass

    def draw(self):
        """The function that draws the Drawable (if anything changed). Checks, whether
        the drawable has changed; if it does, clears the window, calls _draw() and
        attempts to set the cursor position (if also focused)."""
        if self.has_changed():
            self.window.clear()
            self._draw()

        if self.is_focused():
            if self.cursor_position is not None:
                curses.curs_set(1)
                self.window.move(*self.cursor_position)
            else:
                curses.curs_set(0)


class DrawableMenu(Drawable, Menu):
    def __init__(self, window, title: str, items: Sequence[Optional[MenuItem]]):
        Drawable.__init__(self, window)
        Menu.__init__(self, items)

        self.title = title

    def _draw(self):
        lines = self.title.splitlines()

        # the y offset from the top of the window to where to start drawing
        y_off = center_coordinate(
            self.window.height(), len(lines) + 1 + len(self.items)
        )

        # draw the title of the menu, line by line
        for i, line in enumerate(lines):
            x_off = center_coordinate(self.window.width(), len(line))
            self.window.addstr(x_off, y_off + i, line)

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

            x_off = center_coordinate(self.window.width(), len(text))
            self.window.addstr(x_off, y_off + len(lines) + 2 + i, text)


class DrawableLogoDisplay(Drawable, LogoDisplay):
    def __init__(self, window, text: str):
        Drawable.__init__(self, window)
        LogoDisplay.__init__(self, text)

    def _draw(self):
        """Draws the centered program logo on the window."""
        lines = self.text.splitlines()

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                self.window.addstr(
                    x + (self.window.width() - len(line)) // 2,
                    y + (self.window.height() - len(lines)) // 2,
                    char,
                    curses.color_pair(16 if char != "*" else 35),
                )


class DrawableTextDisplay(Drawable, TextDisplay):
    def __init__(self, window, text: str):
        Drawable.__init__(self, window)
        TextDisplay.__init__(self, text)

        self.side_offsets = [3, 1]  # left/right offset, top/bottom offset when drawing

    def __get_content_space(self) -> Tuple[int, int]:
        """Get the width and the height of the area that we can put text on."""
        return (
            self.window.width() - 2 * self.side_offsets[0],
            self.window.height() - 2 * self.side_offsets[1],
        )

    def _draw(self):
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
                        self.side_offsets[0] + x,
                        self.side_offsets[1] + y,
                        char,
                        evaluated_flags
                        | (curses.color_pair(h_level + 34) if h_level != 0 else 0),
                    )

                    x += 1

            h_level = 0
            y += 1

    def handle_keypress(self, key: int) -> Command:
        """Expanded because TextDisplay couldn't easily implement ^D and ^U, since it
        doesn't know the current zoom level."""
        # call super for the command
        command = TextDisplay.handle_keypress(self, key)

        # if a command was generated, propagate
        if command is not None:
            return command

        # else check for ^D and ^U
        else:
            height = self.__get_content_space()[1]

            if key == chr(4):  # ^D
                self.line_offset += height // 3
                self.set_changed(True)

            if key == chr(21):  # ^U
                self.line_offset -= height // 3
                self.set_changed(True)


class DrawableStatusLine(Drawable, StatusLine):
    def __init__(self, window):
        Drawable.__init__(self, window)
        StatusLine.__init__(self)

    def _draw(self):
        # the offsets of each of the text positions
        l_off = 0
        c_off = center_coordinate(self.window.width(), len(self.text[1]))
        r_off = self.window.width() - len(self.text[2]) - 1

        # if the status line is focused, only draw the left line (i.e. the command)
        self.window.addstr(l_off, 0, self.text[0])
        self.cursor_position = (0, self.cursor_offset)

        # if it isn't also draw the rest
        if not self.is_focused():
            self.window.addstr(c_off, 0, self.text[1])
            self.window.addstr(r_off, 0, self.text[2])


class Interface:
    """A high-level class for rendering the user interface."""

    def __init__(self, window):
        # window setup
        self.window = window

        # derive two windows from the current one -- the main one and the status one
        self.main_window = WindowView(window)
        self.status_window = WindowView(window)
        self.resize_windows()

        # initialize the terminal colors
        self.initialize_colors()

        # component initialization
        self.status_line = DrawableStatusLine(self.status_window)

        self.components = {
            "logo": DrawableLogoDisplay(
                self.main_window,
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
                "     |__/' |_|_| |_| |_|\_/ \__._|_|\__,_|_|",
            ),
            "menu": DrawableMenu(
                self.main_window,
                " __  __                  \n"
                "|  \/  | ___ _ __  _   _ \n"
                "| |\/| |/ _ \ '_ \| | | |\n"
                "| |  | |  __/ | | | |_| |\n"
                "|_|  |_|\___|_| |_|\__,_|",
                [
                    MenuItem("CREATE", None, "Creates a new score."),
                    MenuItem("IMPORT", None, "Imports a score from a file."),
                    None,
                    MenuItem("HELP", PushComponentCommand("help"), "Displays program documentation."),
                    MenuItem("INFO", PushComponentCommand("info"), "Shows information about the program."),
                    None,
                    MenuItem("QUIT", PopComponentCommand(), "Terminates the program."),
                ],
            ),
            "info": DrawableTextDisplay(
                self.main_window,
                r"# Info" + "\n"
                r"The following page contains relevant information about the app." + "\n\n"
                r"## History" + "\n"
                r"This project was created as a semester project for the AP Programming Course at the Charles University (/http:\/\/mj.ucw.cz\/vyuka\/1920\/p1x\//)." + "\n\n"
                r"## Source Code" + "\n"
                r"The code is licensed under MIT and freely available from /https:\/\/github.com\/xiaoxiae\/Vimvaldi\//, so feel free do whatever you want with it :-). Also feel free to submit a pull request if there's something you'd like to see changed or implemented!"
            ),
            "help": DrawableTextDisplay(
                self.main_window,
                r"# Help" + "\n"
                r"The following page contains instructions on using the app." + "\n\n"
                r"## General commands (can be run from anywhere within the app)" + "\n"
                r"_:help_       -- displays this page" + "\n"
                r"_:info_       -- displays the info page" + "\n"
                r"_:q_ or _:quit_ -- terminates the app"
            ),
        }

        # the stack of the currently active components
        # start with logo on top of menu
        self.component_stack = [self.components["menu"], self.components["logo"]]
        self.component_stack[-1].set_focused(True)


        # run the program (permanent loop)
        self.loop()

    def get_focused(self):
        """Get the focused component."""
        return self.status_line if self.status_line.is_focused() else self.component_stack[-1]
        

    def loop(self):
        """The main loop of the program."""
        k = None
        while True:
            # special window resize event handling
            if k == curses.KEY_RESIZE:
                self.resize_windows()
            else:
                # send the key to the currently focused component
                commands = self.get_focused().handle_keypress(k)
                print(commands)

                for command in commands:
                    # component commands
                    if isinstance(command, PopComponentCommand):
                        self.component_stack.pop()

                        # if there are no remaining components, return
                        if len(self.component_stack) == 0:
                            return

                    elif isinstance(command, PushComponentCommand):
                        self.component_stack.append(self.components[command.component])

            # redraw the component and the status line
            # check for errors when drawing, possibly displaying an error message
            try:
                # update the components
                self.component_stack[-1].draw()
                self.status_line.draw()

            except curses.error:
                # TODO better error handling
                height, width = self.window.getmaxyx()

                error_text = "Terminal size too small!"[: width - 1]

                self.window.clear()
                self.window.addstr(
                    center_coordinate(width, len(error_text)), height // 2, error_text,
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

        self.main_window.resize(View(0, 0, width, height - 1))
        self.status_window.resize(View(0, height - 1, width, 1))


def run():
    """An entry point to the program."""
    curses.wrapper(Interface)


if __name__ == "__main__":
    run()
