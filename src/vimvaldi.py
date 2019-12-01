# cleaner code!
from typing import Callable, Sequence, Tuple, Generator, Union, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum

# terminal interaction
import curses

# utility functions
import util
import sys


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
        """Does the actual drawing; is called after draw() handles checking for changes
        and erases the window."""
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

        # display the tooltip of the current item
        if not self.status_line.is_focused():
            self.status_line.set_text(self.status_line.CENTER, self.get_tooltip())
            self.status_line.set_changed(True)

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

        if self.status_line.is_focused():
            return

        if key == "j":
            self.next()

        elif key == "k":
            self.previous()

        elif key in (curses.KEY_ENTER, "\n", "\r", "l"):
            return self.items[self.index].action

    def draw(self):
        height, width = self.window.getmaxyx()

        y_off = util.center_coordinate(len(self.title) + 2 + len(self.items), height)

        # draw the title of the menu
        for i, line in enumerate(self.title):
            x_off = util.center_coordinate(width, len(line))
            self.window.addstr(i - y_off, x_off, line)

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
            self.window.addstr(i + len(self.title) + 2 - y_off, x_off, label)


class LogoDisplay(Controllable):
    """A very simple class for displaying the logo."""

    def __init__(self, window, status_line, text: Sequence[str]):
        super(LogoDisplay, self).__init__(window, status_line)

        self.text = text

    def draw(self) -> bool:
        """Draws the centered program logo on the main window."""
        self.window.clear()

        height, width = self.window.getmaxyx()

        for y, line in enumerate(self.text):
            for x, char in enumerate(line):
                self.window.addstr(
                    y + (height - len(self.text)) // 2,
                    x + (width - len(line)) // 2,
                    char,
                    # 16 is color white; 3 is green
                    curses.color_pair(16 if char not in ("*") else 3),
                )

        self.status_line.clear()

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        if key in (curses.KEY_ENTER, "\n", "\r"):
            return ["change_state", "menu"]


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

    def handle_keypress(self, key: int) -> Union[None, List[str]]:
        if not self.is_focused():
            if key == ":":
                self.set_focused(True)
            else:
                return

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

        elif key == curses.KEY_HOME:  # home
            self.cursor_position = 1

        elif key == curses.KEY_END:  # end
            self.cursor_position = len(self.text[0])

        elif key in (curses.KEY_ENTER, "\n", "\r"):  # enter
            command = self.text[0][1:]

            self.set_focused(False)
            self.text[0] = ""

            # return the split command
            return command.split()

        else:  # add the char to the command string
            self.text[0] = self.text[0][:c_pos] + str(key) + self.text[0][c_pos:]
            self.cursor_position += 1

        self.set_changed(True)

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
        self.control_state_stack = [self.components["logo"]]

        # run the program
        self.run()

    def run(self):
        """The main loop of the program."""
        k = None
        while True:
            # handle window resize event
            if k == curses.KEY_RESIZE:
                self.resize_windows()

            command = self.control_state_stack[-1].handle_keypress(k)

            # handle commands sent by the components
            if command != None:
                # relinquish the control from the current element to the next
                if len(command) == 1 and command[0] == "quit":
                    self.control_state_stack.pop()

                    # when there's nothing to control, exit...
                    if len(self.control_state_stack) == 0:
                        sys.exit()
                    else:
                        self.control_state_stack[-1].set_changed(True)

                # change state -- remove the current one and add the specified one
                elif len(command) == 2 and command[0] == "change_state":
                    self.control_state_stack[-1] = self.components[command[1]]
                    self.control_state_stack[-1].set_changed(True)

                # change state append the specified one to the current one
                elif len(command) == 2 and command[0] == "append_state":
                    self.control_state_stack.append(self.components[command[1]])
                    self.control_state_stack[-1].set_changed(True)

            # redraw the component and the status line
            self.control_state_stack[-1].refresh()
            self.status_line.refresh()

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

        self.main_window.resize(height - 1, width)
        self.status_window.mvwin(height - 1, 0)


if __name__ == "__main__":
    curses.wrapper(Interface)
