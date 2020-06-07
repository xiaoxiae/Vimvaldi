"""A module for working with command."""

from dataclasses import dataclass

from vimvaldi.utilities import *



@dataclass
class Command:
    """The default command class that is inherited by all other command classes."""



class GeneralCommand(Command):
    """Other commands that didn't really fit anywhere else."""

class ToggleFocusCommand(GeneralCommand):
    """A command to toggle focus from the status line to the main window."""



class IOCommand(Command):
    """Things related to file IO."""

@dataclass
class QuitCommand(IOCommand):
    forced: bool = False  # q!

@dataclass
class SaveCommand(IOCommand):
    path: str = None
    forced: bool = False  # w!

@dataclass
class OpenCommand(IOCommand):
    path: str = None
    forced: bool = False  # o! (overwrite currently open file)



class ComponentCommand(Command):
    """A class for component commands."""

class PopComponentCommand(ComponentCommand):
    """Pop a component from the component stack."""

@dataclass
class PushComponentCommand(ComponentCommand):
    """Push a component onto the component stack."""
    component: str



class StatusLineCommand(Command):
    """A class for status line commands."""

@dataclass
class SetStatusLineTextCommand(StatusLineCommand):
    """Set the status line to the given text."""
    text: str
    position: Position

@dataclass
class SetStatusLineStateCommand(StatusLineCommand):
    """Set the status line state."""
    state: State

class ClearStatusLineCommand(StatusLineCommand):
    """Clears the contents of the status line."""



class EditorCommand(Command):
    """Commands that concern the note editor."""

@dataclass
class InsertCommand(EditorCommand):
    """The command that gets passed to the editor to deal with."""
    text: str

@dataclass
class SetCommand(EditorCommand):
    """Set something to something (clef, key, time...).
    Either `:set something something` or `:set something=something`."""
    option: str
    value: str
