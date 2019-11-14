# terminal interaction
import curses

# cleaner code!
from typing import Callable, Sequence, Tuple, Generator

# utility functions
import util


class MenuItem:
    """A class for representing an item of a menu."""

    def __init__(self, label: str, action: Callable, tooltip: str):
        self.label = label
        self.action = action
        self.tooltip = tooltip


class MenuSpacer(MenuItem):
    """A class for representing a spacer (ie. blank unselectable menu item)."""

    def __init__(self):
        pass


class Menu:
    """A class for representing and working with a menu."""

    def __init__(self, window, items: Sequence[MenuItem]):
        self.index = 0
        self.items = items

        # drawing-related variables
        self.window = window
        self.title = (
            " __  __                  \n"
            "|  \/  | ___ _ __  _   _ \n"
            "| |\/| |/ _ \ '_ \| | | |\n"
            "| |  | |  __/ | | | |_| |\n"
            "|_|  |_|\___|_| |_|\__,_|"
        ).split("\n")

    def _move_index(self, delta):
        """Moves the index of the menu by delta positions (ignoring spacers)."""
        self.index = (self.index + delta) % len(self.items)

        # skip the spacers
        while type(self.items[self.index]) is MenuSpacer:
            self.index = (self.index + (1 if delta > 0 else -1)) % len(self.items)

    def next(self):
        """Point to the next item in the menu."""
        self._move_index(1)

    def previous(self):
        """Point to the previous item in the menu."""
        self._move_index(-1)

    def select(self):
        """Call the callable specified in the option tuple."""
        self.options[self.index]()

    def is_selected(self, item: MenuItem) -> bool:
        """Returns True if the specified item matches the currently selected one."""
        return self.items[self.index] is item

    def draw(self):
        """Draw the menu to the window."""
        self.window.clear()

        height, width = self.window.getmaxyx()

        y_off = util.center_coordinate(len(self.title) + 2 + len(self.items), height)

        # draw the title of the menu
        for i, line in enumerate(self.title):
            x_off = util.center_coordinate(width, len(line))
            self.window.addstr(i - y_off, x_off, line)

        # draw the menu itself
        for i, item in enumerate(self.items):
            # ignore spacers
            if type(item) is MenuSpacer:
                continue

            if self.is_selected(item):
                label = f"> {item.label} <"
            else:
                label = item.label

            x_off = util.center_coordinate(width, len(label))
            self.window.addstr(i + len(self.title) + 2 - y_off, x_off, label)

        self.window.refresh()


class StatusLine:
    """A class for displaying information about the state of the program/parsing
    the commands specified by the user."""

    def __init__(self, window):
        self.clear()
        self.window = window
        self.focused = False

    def clear(self):
        """Clears the status line."""
        self.left_text, self.center_text, self.right_text = "", "", ""

    def is_focused(self):
        """Returns True if the status line is currently focused."""
        return self.focused

    def set_focus(self, value: bool = True):
        """Sets the focus of the status line."""
        self.focused = value

    def draw(self):
        """Draw the status line to the window."""
        self.window.clear()

        _, width = self.window.getmaxyx()

        # draw left, center and right text
        self.window.addstr(0, 0, self.left_text)
        self.window.addstr(
            0, util.center_coordinate(width, len(self.center_text)), self.center_text
        )
        self.window.addstr(0, width - len(self.right_text) - 1, self.right_text)

        self.window.refresh()


class Interface:
    """A high-level class for rendering the Vimvaldi user interface."""

    def __init__(self, window):
        """Initializes the interface."""
        # window setup
        self.window = window
        height, width = self.window.getmaxyx()
        self.main_window = self.window.subwin(height - 1, 0, 0, 0)
        self.status_window = self.window.subwin(height - 1, 0)

        curses.curs_set(0)

        self.initialize_colors()

        # initialize the interface components
        self.menu = Menu(
            self.main_window,
            [
                MenuItem("CREATE", lambda: None, "Creates a new score."),
                MenuItem("IMPORT", lambda: None, "Imports a score from a file."),
                MenuSpacer(),
                MenuItem("HELP", lambda: None, "Displays program documentation."),
                MenuItem("INFO", lambda: None, "Shows information about the program."),
            ],
        )

        # status line setup
        self.status_line = StatusLine(self.status_window)

        # the state of the GUI; NOTE: possibly make this an enum?
        # 0) logo screen
        # 1) menu
        # 2) help/info screen (same thing, just different text)
        # 3) score
        self.state = 0

        # run the program
        self.run()

    def run(self):
        """The main loop of the program."""
        k = None
        while True:
            self.resize_windows()

            if self.state == 0:
                self.draw_logo()

                if k in {curses.KEY_ENTER, 10, 13}:
                    self.state = 1

            if self.state == 1:
                if k is not None:
                    if chr(k) == "j":
                        self.menu.next()
                    elif chr(k) == "k":
                        self.menu.previous()

                self.menu.draw()

            k = self.window.getch()

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

        self.main_window = self.window.subwin(height - 1, 0, 0, 0)
        self.status_window = self.window.subwin(height - 1, 0)

    def draw_logo(self) -> bool:
        """Draws the centered program logo on the main window. Return True if is was
        successful."""
        self.window.clear()

        logo_lines = (
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
        ).split("\n")

        height, width = self.window.getmaxyx()

        # return False if the logo doesn't fit the screen
        if height < len(logo_lines) or width < len(logo_lines[0]):
            return False

        for y, line in enumerate(logo_lines):
            for x, char in enumerate(line):
                self.window.addstr(
                    y + (height - len(logo_lines)) // 2,
                    x + (width - len(line)) // 2,
                    char,
                    curses.color_pair(16 if char not in ("*") else 3),
                )

        return True


if __name__ == "__main__":
    curses.wrapper(Interface)
