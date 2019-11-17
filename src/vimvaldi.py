# terminal interaction
import curses

# cleaner code!
from typing import Callable, Sequence, Tuple, Generator
from enum import Enum

# utility functions
import util


class Position(Enum):
    """An enum for storing information about the position of something."""

    LEFT = 0
    CENTER = 1
    RIGHT = 2


class InterfaceState(Enum):
    LOGO = 0  # the logo screen
    MENU = 1  # the menu
    HELP = 2  # the documentation page
    INFO = 3  # the  info page
    SCORE = 4  # the score editing


class Drawable:
    """A class to be extended by classes that write on the courses windows."""

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
        """Refreshes the Drawable."""
        self.set_changed(False)
        self.window.refresh()


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


class Menu(Drawable):
    """A class for representing and working with a menu."""

    def __init__(self, window, items: Sequence[MenuItem]):
        super(Menu, self).__init__(window)

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
        while type(self.items[self.index]) is MenuSpacer:
            self.index = (self.index + (1 if delta > 0 else -1)) % len(self.items)

        self.set_changed(True)

    def next(self):
        """Point to the next item in the menu."""
        self.__move_index(1)

    def previous(self):
        """Point to the previous item in the menu."""
        self.__move_index(-1)

    def open(self):
        """Run the action associated with the current menu item."""
        return self.items[self.index].action()

    def get_tooltip(self) -> str:
        """Return the tooltip associated with the currently selected menu item."""
        return self.items[self.index].tooltip

    def is_selected(self, item: MenuItem) -> bool:
        """Returns True if the specified item matches the currently selected one."""
        return self.items[self.index] is item

    def handle_keypress(self, key: int):
        """Handles a single keypress."""
        if key == "j":
            self.next()

        if key == "k":
            self.previous()

        if key in (curses.KEY_ENTER, "\n", "\r", "l"):
            self.open()

    def draw(self):
        if not self.get_changed():
            return

        self.window.erase()

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

        self.refresh()


class StatusLine(Drawable):
    """A class for displaying information about the state of the program/parsing the 
    commands specified by the user."""

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

    def set_text(self, position: Position, text: str):
        """Change text at the specified position (left/center/right)."""
        self.text[position.value] = text
        self.set_changed(True)

    def get_text(self, position: Position) -> str:
        """Return text at the specified position (left/center/right)."""
        return self.text[position.value]

    def issue_command(self, command: str):
        """Issue the specified command."""

    def handle_keypress(self, key: int):
        """Handles a single keypress."""
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
            self.issue_command(self.text[0])
            self.set_focused(False)
            self.text[0] = ""

        else:  # add the char to the command string
            self.text[0] = self.text[0][:c_pos] + str(key) + self.text[0][c_pos:]
            self.cursor_position += 1

        self.set_changed(True)

    def draw(self):
        if not self.get_changed():
            return

        self.window.erase()

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

        self.set_changed(False)
        self.window.refresh()


class Interface:
    """A high-level class for rendering the Vimvaldi user interface."""

    def __init__(self, window):
        """Initializes the interface."""
        # window setup
        self.window = window

        height, width = self.window.getmaxyx()
        self.main_window = self.window.derwin(height - 1, width, 0, 0)
        self.status_window = self.window.derwin(1, width, height - 1, 0)

        curses.curs_set(0)

        self.initialize_colors()

        # COMPONENT INITIALIZATION
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

        self.status_line = StatusLine(self.status_window)

        # the state of the GUI
        self.state = InterfaceState.LOGO

        # run the program
        self.run()

    def run(self):
        """The main loop of the program."""
        k = None
        while True:
            # handle window resize event
            if k == curses.KEY_RESIZE:
                self.resize_windows()

            if self.state == InterfaceState.LOGO:
                self.draw_logo()

                if k in (curses.KEY_ENTER, "\n", "\r"):
                    self.state = InterfaceState.MENU

            if self.state == InterfaceState.MENU:
                self.status_line.handle_keypress(k)

                if not self.status_line.is_focused():
                    self.menu.handle_keypress(k)

                # display tooltip when the status line isn't focused
                self.status_line.set_text(Position.CENTER, self.menu.get_tooltip())

                self.menu.draw()
                self.status_line.draw()

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
                    # 16 is color white; 3 is green
                    curses.color_pair(16 if char not in ("*") else 3),
                )

        return True


if __name__ == "__main__":
    curses.wrapper(Interface)
