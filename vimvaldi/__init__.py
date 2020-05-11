"""The initial module that gets called when the program is launched."""

import argparse

from vimvaldi.components import *
from vimvaldi.utilities import *
from vimvaldi.graphics import *


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

    def move(self, x: int, y: int):
        self.parent.move(y + self.view.y, x + self.view.x)


class Drawable(ABC, Changeable):
    """A class to be extended by things that write on the curses windows."""

    focused = False  # whether this drawable is currently focused
    cursor_position = None

    def __init__(self, window: WindowView):
        self.window = window

    def toggle_focused(self) -> List[Command]:
        """Toggle the focus on this Drawable."""
        return self.set_focused(not self.focused)

    def set_focused(self, value: bool) -> List[Command]:
        """Set the focus on this Drawable. Possibly return a command if the component
        wants to do some action (they will override it)."""
        self.focused = value
        self.set_changed(True)

        return []

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
            self.set_changed(False)

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

    def set_focused(self, value: bool) -> List[Command]:
        """If the focus switched to the menu, set the status line according to the
        currently selected item."""
        Drawable.set_focused(self, value)
        return [] if not value else self.update_status_line()


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
        wrapped: List[Tuple[str, int]] = []
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

    def set_focused(self, value: bool) -> List[Command]:
        Drawable.set_focused(self, value)
        return [ClearStatusLineCommand()]

    def handle_keypress(self, key: str) -> Command:
        """Expanded because TextDisplay couldn't easily implement ^D and ^U, since it
        doesn't know the current zoom level."""
        # call super for the command
        command = TextDisplay.handle_keypress(self, key)

        # if a command was generated, propagate
        if len(command) != 0:
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

        return []


class DrawableStatusLine(Drawable, StatusLine):
    def __init__(self, window):
        Drawable.__init__(self, window)
        StatusLine.__init__(self)

    def _draw(self):
        # the offsets of each of the text positions (left, center, right)
        offsets = [
            0,
            center_coordinate(self.window.width(), len(self.text[1])),
            self.window.width() - len(self.text[2]) - 1,
        ]

        if self.is_focused():
            command_text = self.text[0]
            cursor_offset = self.cursor_offset

            if self.current_state is State.NORMAL:
                command_text = ":" + command_text
            elif self.current_state is State.INSERT:
                command_text = ">" + command_text

            self.window.addstr(0, 0, command_text)
            self.cursor_position = (self.cursor_offset + 1, 0)
        else:
            for i, offset in enumerate(offsets):
                self.window.addstr(offset, 0, self.text[i])


class DrawableEditor(Drawable, Editor):
    def __init__(self, window, title: str):
        Drawable.__init__(self, window)
        Editor.__init__(self)

        self.title = title

        self.side_offsets = [5, 1]  # left/right offset, top/bottom offset

    def _draw(self):
        sheet_lines = 5  # number of lines in a note sheet

        width = self.window.width()
        height = self.window.height()

        title_sheet_spacing = 3  # distance from the notesheet to the window title

        # center the logo and the sheet horizontally
        center = center_coordinate(
            height, sheet_lines + len(self.title.splitlines()) + title_sheet_spacing
        )

        # draw the title of the menu
        for i, line in enumerate(self.title.splitlines()):
            x_off = center_coordinate(width, len(line))
            self.window.addstr(x_off, center + i + title_sheet_spacing, line)

        # draw the sheet lines
        for x in range(self.side_offsets[0], width - self.side_offsets[0]):
            for y in range(sheet_lines):
                y += center + len(self.title.splitlines()) + title_sheet_spacing
                self.window.addstr(x, y, " ", curses.A_UNDERLINE)

    def set_focused(self, value: bool) -> List[Command]:
        """For setting status line information."""
        Drawable.set_focused(self, value)
        return [ClearStatusLineCommand(), self.get_file_name_command()]


class Interface:
    """A high-level class for rendering the user interface."""

    def __init__(self, window, arguments):
        # window setup
        self.window = window

        # derive two windows from the current one -- the main one and the status one
        self.main_window = WindowView(window)
        self.status_window = WindowView(window)

        # initialize the terminal colors
        self.initialize_colors()

        # component initialization
        self.status_line = DrawableStatusLine(self.status_window)

        self.components = {
            "logo": DrawableLogoDisplay(self.main_window, vimvaldi_logo),
            "menu": DrawableMenu(
                self.main_window,
                menu_logo,
                [
                    MenuItem(
                        "EDIT", [PushComponentCommand("editor")], "Creates a new score."
                    ),
                    MenuItem(
                        "OPEN",
                        [
                            ToggleFocusCommand(),
                            SetStatusLineTextCommand("open ", Position.LEFT),
                        ],
                        "Opens an existing score.",
                    ),
                    None,
                    MenuItem(
                        "HELP",
                        [PushComponentCommand("help")],
                        "Displays program documentation.",
                    ),
                    MenuItem(
                        "INFO",
                        [PushComponentCommand("info")],
                        "Shows information about the program.",
                    ),
                    None,
                    MenuItem(
                        "QUIT", [PopComponentCommand()], "Terminates the program."
                    ),
                ],
            ),
            "info": DrawableTextDisplay(self.main_window, info_text),
            "help": DrawableTextDisplay(self.main_window, help_text),
            "editor": DrawableEditor(self.main_window, editor_logo),
        }

        # the stack of the currently active components
        # start with logo on top of menu
        self.component_stack = [self.components["menu"], self.components["logo"]]
        self.component_stack[-1].set_focused(True)

        self.resize_windows()

        # run the program (permanent loop)
        self.loop()

    def get_focused(self):
        """Get the focused component."""
        return (
            self.status_line
            if self.status_line.is_focused()
            else self.component_stack[-1]
        )

    def loop(self):
        """The main loop of the program."""
        k = None
        while True:
            # special window resize event handling
            if k == curses.KEY_RESIZE:
                self.resize_windows()
            else:
                # send the key to the currently focused component
                self.resolve_commands(self.get_focused().handle_keypress(k))

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
                    height // 2, center_coordinate(width, len(error_text)), error_text,
                )

            # wait for the next character
            # done to handle ^C gracefully, since curses sends an error
            try:
                k = self.window.get_wch()
            except curses.error as e:
                self.resolve_commands([QuitCommand()])
                k = None

    def resolve_commands(self, commands: List[Command]):
        """Resolve the specified commands."""
        # this is important, since it creates a new list so we can modify it freely
        commands = list(commands)

        while len(commands) != 0:
            command = commands.pop(0)

            # pop the component, possibly terminating the app
            if isinstance(command, PopComponentCommand):
                self.component_stack.pop()

                # if there are no remaining components, return
                if len(self.component_stack) == 0:
                    quit()

                commands += self.component_stack[-1].set_focused(True)

            # add a new component, setting the focus on it
            elif isinstance(command, PushComponentCommand):
                self.component_stack.append(self.components[command.component])
                commands += self.status_line.set_focused(False)
                commands += self.component_stack[-1].set_focused(True)

            # toggle focus
            elif isinstance(command, ToggleFocusCommand):
                commands += self.status_line.toggle_focused()
                commands += self.component_stack[-1].toggle_focused()

            # status line things
            elif isinstance(command, StatusLineCommand):
                commands += self.status_line.handle_command(command)

            # else just let the active component handle it
            else:
                commands += self.component_stack[-1].handle_command(command)

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

        self.status_line.set_changed(True)
        self.component_stack[-1].set_changed(True)


def run():
    """An entry point to the program."""
    parser = argparse.ArgumentParser(
        description="A terminal note sheet editor with Vim-like keybindings.",
    )

    curses.wrapper(Interface, parser.parse_args())


if __name__ == "__main__":
    run()
