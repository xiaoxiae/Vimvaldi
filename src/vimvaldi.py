# terminal interaction
import curses

# cleaner code!
from typing import Callable, Sequence, Tuple, Generator


class MenuItem:
    """A class for representing an item of a menu."""

    def __init__(self, label, action, tooltip):
        self.label = label
        self.action = action
        self.tooltip = tooltip


class MenuSpacer(MenuItem):
    """A class for representing a spacer (ie. blank unselectable menu item)."""

    def __init__(self):
        """Takes no arguments."""
        pass


class Menu:
    """A class for representing a menu."""

    def __init__(self, items: Sequence[MenuItem]):
        self.index = 0  # currently selected item in the menu
        self.items = items

    def _move_index(self, delta):
        """Moves the index of the menu by delta until it points to something that isn't spacer."""
        self.index = (self.index + delta) % len(self.items)

        # skip menu the spacers
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


class Interface:
    """A high-level class for rendering the Vimvaldi user interface."""

    def __init__(self, window):
        """Initializes the interface."""
        # window setup
        self.window = window
        self.resize_windows()

        curses.curs_set(0)

        self.initialize_colors()

        # app menu setup
        self.menu = Menu(
            [
                MenuItem("CREATE", lambda _: _, "Opens a new score."),
                MenuItem("IMPORT", lambda _: _, "Imports a score from a file."),
                MenuSpacer(),
                MenuItem("HELP", lambda _: _, "Opens program documentation"),
                MenuItem("MISC", lambda _: _, "Opens information about the program."),
            ]
        )

        # the state of the GUI
        # 0) logo screen
        # 1) menu
        # 2) help/info screen (same thing, just different text)
        # 3) score
        self.state = 0

        # run the program
        self.run()

    def run(self):
        """The main loop of the program."""
        while True:
            k = None

            if self.state == 0:
                while k not in {curses.KEY_ENTER, 10, 13}:
                    self.draw_logo()
                    k = self.window.getch()

                # go to the menu after enter has been pressed
                self.state = 1

            if self.state == 1:
                self.display_menu()

                k = self.window.getch()
                if chr(k) == "j":
                    self.menu.next()
                elif chr(k) == "k":
                    self.menu.previous()

    def center_coordinate(self, a: int, b: int) -> int:
        """Return the starting coordinate of an object of size a centered in an  object 
        of size b. Note that the function can return negative values (if a > b)."""
        return (a // 2) - (b // 2) - b % 2

    def display_menu(self):
        """Draw the menu to the main window."""
        self.resize_windows()

        menu_title = (
            " __  __                  \n"
            "|  \/  | ___ _ __  _   _ \n"
            "| |\/| |/ _ \ '_ \| | | |\n"
            "| |  | |  __/ | | | |_| |\n"
            "|_|  |_|\___|_| |_|\__,_|"
        ).split("\n")

        height, width = self.main_window.getmaxyx()

        y_off = self.center_coordinate(
            len(menu_title) + 1 + len(self.menu.items), height
        )

        # draw the title
        for i, line in enumerate(menu_title):
            x_off = self.center_coordinate(width, len(line))
            self.main_window.addstr(i - y_off, x_off, line)

        # draw the menu itself
        for i, item in enumerate(self.menu.items):
            if type(item) is MenuSpacer:
                continue

            # if the current label is selected, draw its tooltip to the command window
            if self.menu.is_selected(item):
                label = f"> {item.label} <"
                self.set_status_message(item.tooltip)
            else:
                label = item.label

            x_off = self.center_coordinate(width, len(label))
            self.main_window.addstr(i + len(menu_title) + 1 - y_off, x_off, label)

    def set_status_message(self, message):
        """Sets the status message of the command window."""
        self.cmd_window.addstr(0, 0, message)

    def initialize_colors(self):
        """Initializes the colors used throughout the program 
        (see https://jonasjacek.github.io/colors/)."""

        curses.start_color()
        curses.use_default_colors()

        for i in range(curses.COLORS):
            curses.init_pair(i + 1, i, -1)

    def resize_windows(self):
        """Clears and resizes main and command windows to the appropriate sizes."""
        height, width = self.window.getmaxyx()

        self.main_window = self.window.subwin(height - 1, 0, 0, 0)
        self.cmd_window = self.window.subwin(height - 1, 0)

        self.main_window.clear()
        self.cmd_window.clear()

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
